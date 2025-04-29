import asyncio
import logging
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx # For potential errors from http_client

from .. import config
from ..data_access import db_layer
from ..utils import file_utils, http_client, text_processing

logger = logging.getLogger(__name__)

# --- Helper: Embedding Generation ---

async def get_embeddings_in_batches(
    chunks_data: List[Tuple[int, str, int]], # (section_id, chunk_text, chunk_sequence)
    batch_size: int = config.EMBEDDING_BATCH_SIZE
) -> List[List[float]]:
    """
    Generates embeddings for text chunks in batches via LiteLLM Proxy.
    """
    # TDD: Test successful embedding request via LiteLLM proxy
    # TDD: Test handling of HTTP errors from LiteLLM proxy
    # TDD: Test handling of errors reported in LiteLLM response body
    # TDD: Test retry logic (potentially handled by LiteLLM itself or http_client)
    # TDD: Test handling of empty chunks_data list
    if not chunks_data:
        return []

    all_embeddings: List[List[float]] = []
    total_chunks = len(chunks_data)
    headers = {}
    if config.LITELLM_API_KEY:
        headers["Authorization"] = f"Bearer {config.LITELLM_API_KEY}"

    logger.info(f"Requesting embeddings for {total_chunks} chunks in batches of {batch_size}...")

    for i in range(0, total_chunks, batch_size):
        batch = chunks_data[i : i + batch_size]
        chunk_texts = [item[1] for item in batch] # Extract text

        if not chunk_texts:
            continue

        payload = {"model": config.EMBEDDING_MODEL_NAME, "input": chunk_texts}
        batch_num = i // batch_size + 1
        logger.debug(f"Requesting embeddings for batch {batch_num} ({len(chunk_texts)} chunks)")

        try:
            response = await http_client.make_async_request(
                "POST",
                f"{config.LITELLM_PROXY_URL}/embeddings",
                json_data=payload,
                headers=headers,
                timeout=120.0 # Increased timeout for potentially large batches
            )
            response.raise_for_status() # Check for HTTP errors
            response_data = await response.json() # Await the coroutine

            if 'data' not in response_data or len(response_data['data']) != len(chunk_texts):
                logger.error(f"Mismatch between requested ({len(chunk_texts)}) and received embeddings ({len(response_data.get('data', []))}) in batch {batch_num}. Response: {response_data}")
                raise ValueError("Mismatch between requested and received embeddings in batch")

            batch_embeddings = [item['embedding'] for item in response_data['data']]

            # Validate dimensions of received embeddings
            for idx, emb in enumerate(batch_embeddings):
                if len(emb) != config.TARGET_EMBEDDING_DIMENSION:
                     chunk_info = batch[idx] # (section_id, text, sequence)
                     logger.error(f"Embedding dimension mismatch for chunk (section={chunk_info[0]}, seq={chunk_info[2]}) in batch {batch_num}. Expected {config.TARGET_EMBEDDING_DIMENSION}, got {len(emb)}.")
                     raise ValueError(f"Received embedding with incorrect dimension ({len(emb)})")

            all_embeddings.extend(batch_embeddings)
            logger.debug(f"Received embeddings for batch {batch_num}")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching embeddings for batch {batch_num}: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"Embedding generation failed (HTTP {e.response.status_code})") from e
        except httpx.RequestError as e:
            logger.error(f"Request error fetching embeddings for batch {batch_num}: {e}")
            raise RuntimeError("Embedding generation failed (Request Error)") from e
        except (ValueError, KeyError, json.JSONDecodeError) as e:
             logger.error(f"Error processing embedding response for batch {batch_num}: {e}. Response: {response.text if 'response' in locals() else 'N/A'}")
             raise RuntimeError("Embedding generation failed (Processing Error)") from e
        except Exception as e:
            logger.exception(f"Unexpected error fetching embeddings for batch {batch_num}", exc_info=e)
            raise RuntimeError("Embedding generation failed (Unexpected Error)") from e

    logger.info(f"Successfully received {len(all_embeddings)} embeddings.")
    if len(all_embeddings) != total_chunks:
         logger.error(f"Final embedding count mismatch: Expected {total_chunks}, got {len(all_embeddings)}")
         raise RuntimeError("Embedding generation failed: Final count mismatch.")

    return all_embeddings


# --- Helper: Content Extraction Dispatcher ---

async def extract_content_and_metadata(full_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extracts content and metadata based on file type.
    """
    file_type = file_utils.get_file_extension(full_path)

    if file_type == ".pdf":
        # TDD: Test GROBID PDF extraction returns text, metadata, refs
        # GROBID call is potentially long-running, hence async
        return await text_processing.call_grobid_extractor(full_path)
    elif file_type == ".epub":
        # TDD: Test EPUB extraction returns text and metadata
        # TDD: Test handling of encrypted/DRM EPUBs (expect failure)
        # This is CPU bound, but run in executor if it becomes blocking
        return text_processing.extract_epub_content(full_path)
    elif file_type in [".md", ".txt"]:
        # TDD: Test TXT/MD extraction reads content correctly
        # TDD: Test MD extraction handles frontmatter metadata
        return text_processing.extract_text_content(full_path)
    else:
        logger.warning(f"Unsupported file type for extraction: {file_type} ({full_path})")
        return None

# --- Main Ingestion Function ---

async def process_document(file_path_relative: str) -> Dict[str, Any]:
    """
    Processes a single document or all documents in a directory.
    """
    # TDD: Test processing a valid PDF file successfully
    # TDD: Test processing a valid EPUB file successfully
    # TDD: Test processing a valid MD file successfully
    # TDD: Test processing a valid TXT file successfully
    # TDD: Test processing a file that already exists in DB (skip or update?) -> Skips
    # TDD: Test handling of file not found error
    # TDD: Test handling of unsupported file type error
    # TDD: Test handling of errors during extraction, chunking, embedding, or indexing

    # Resolve absolute path relative to configured source directory
    try:
        # Ensure the relative path doesn't try to escape the source dir
        # Note: config.SOURCE_FILE_DIR_ABSOLUTE is already resolved
        # .resolve(strict=True) will raise FileNotFoundError if path doesn't exist
        full_path = (config.SOURCE_FILE_DIR_ABSOLUTE / file_path_relative).resolve(strict=True)
        # Path traversal check (redundant if resolve(strict=True) works as expected, but keep for safety)
        if config.SOURCE_FILE_DIR_ABSOLUTE not in full_path.parents and full_path != config.SOURCE_FILE_DIR_ABSOLUTE:
             logger.error(f"Attempted path traversal: {file_path_relative}")
             # This case should ideally not be reached if resolve(strict=True) is used
             return {"status": "Error", "message": "Invalid path (traversal attempt)"}
    except FileNotFoundError:
         # This is the expected exception if the path doesn't exist
         logger.warning(f"Path not found during resolution: {file_path_relative}")
         # Return the standard "not found" message for the API handler
         return {"status": "Error", "message": "File or directory not found"}
    except Exception as path_e:
         # Catch other potential path errors (e.g., permission denied, invalid characters)
         logger.error(f"Error resolving path '{file_path_relative}': {path_e}")
         return {"status": "Error", "message": f"Invalid path or access error: {path_e}"}


    if file_utils.check_directory_exists(full_path):
        logger.info(f"Processing directory: {full_path}")
        results = []
        # Use file_utils to list files, respecting allowed extensions if needed
        allowed_ext = ['.pdf', '.epub', '.md', '.txt']
        # NOTE: file_utils.list_files_in_directory is a generator, needs async iteration
        # This part needs adjustment if file_utils itself isn't async
        # Assuming a synchronous version for now, or needs async file listing utility
        for file_to_process in file_utils.list_files_in_directory(full_path, allowed_extensions=allowed_ext, recursive=True):
            # Get path relative to the original source dir for consistency
            try:
                relative_sub_path = file_to_process.relative_to(config.SOURCE_FILE_DIR_ABSOLUTE)
                logger.info(f"Queueing file from directory: {relative_sub_path}")
                # Process each file individually (could be parallelized later)
                result = await _process_single_file(relative_sub_path)
                results.append({str(relative_sub_path): result})
            except Exception as e:
                 logger.error(f"Failed processing file {file_to_process} in directory {full_path}: {e}", exc_info=True)
                 results.append({str(file_to_process): {"status": "Error", "message": str(e)}})
        # Aggregate results (simple summary for now)
        success_count = sum(1 for r in results if list(r.values())[0]['status'] == 'Success')
        skipped_count = sum(1 for r in results if list(r.values())[0]['status'] == 'Skipped')
        error_count = len(results) - success_count - skipped_count
        return {
            "status": "Directory Processed",
            "message": f"Processed directory '{file_path_relative}'. Success: {success_count}, Skipped: {skipped_count}, Errors: {error_count}",
            "details": results
        }
    elif file_utils.check_file_exists(full_path):
        logger.info(f"Processing single file: {full_path}")
        # Ensure we use the relative path for DB storage and checks
        relative_path_obj = full_path.relative_to(config.SOURCE_FILE_DIR_ABSOLUTE)
        return await _process_single_file(relative_path_obj)
    else:
        logger.error(f"Path not found or is not a file/directory: {full_path}")
        return {"status": "Error", "message": "File or directory not found"}


async def _process_single_file(file_path_relative: Path) -> Dict[str, Any]:
    """Internal function to process a single file."""
    full_path = (config.SOURCE_FILE_DIR_ABSOLUTE / file_path_relative).resolve()
    relative_path_str = str(file_path_relative) # Use consistent string representation for DB/logs

    logger.info(f"Starting ingestion for single file: {relative_path_str}")

    # Check if document already processed
    try:
        async with db_layer.get_db_connection() as conn:
            exists = await db_layer.check_document_exists(conn, relative_path_str)
            if exists:
                logger.warning(f"Document already processed: {relative_path_str}. Skipping.")
                return {"status": "Skipped", "message": "Document already exists"}
    except Exception as db_e:
         logger.error(f"Database check failed for {relative_path_str}: {db_e}", exc_info=True)
         return {"status": "Error", "message": f"DB check failed: {db_e}"}

    # 1. Extraction
    try:
        extracted_data = await extract_content_and_metadata(full_path)
        if extracted_data is None:
            return {"status": "Error", "message": "Extraction failed or unsupported format"}
        # extracted_data = { text_by_section: { "Section Title": "Text..." }, metadata: {...}, references_raw: [...] }
    except Exception as e:
        logger.error(f"Extraction failed for {relative_path_str}: {e}", exc_info=True)
        return {"status": "Error", "message": f"Extraction failed: {e}"}

    doc_id = -1 # Initialize doc_id
    # Use a single connection for the transaction
    try:
        async with db_layer.get_db_connection() as conn:
            # 2. Database Entry (Initial Document)
            try:
                doc_metadata = extracted_data.get('metadata', {})
                doc_id = await db_layer.add_document(conn,
                                                   doc_metadata.get('title'),
                                                   doc_metadata.get('author'),
                                                   doc_metadata.get('year'),
                                                   relative_path_str,
                                                   doc_metadata)
                logger.info(f"Added document record for {relative_path_str} with ID: {doc_id}")
            except Exception as e:
                logger.error(f"Failed to add document record for {relative_path_str}: {e}", exc_info=True)
                # No need to rollback here, context manager handles it on exception
                raise RuntimeError(f"DB document insert failed: {e}") from e # Raise to trigger outer catch

            # 3. Chunking & Embedding Preparation
            all_chunks_for_embedding: List[Tuple[int, str, int]] = [] # (section_id, chunk_text, chunk_sequence)
            section_mapping: Dict[int, int] = {} # Map section_sequence to section_id

            try:
                section_sequence = 0
                for section_title, section_text in extracted_data.get('text_by_section', {}).items():
                    if not section_text: # Skip empty sections
                        continue
                    # Add section to DB
                    section_id = await db_layer.add_section(conn, doc_id, section_title, doc_metadata.get('structure_level', 0), section_sequence)
                    section_mapping[section_sequence] = section_id

                    # Chunk the section text
                    # TDD: Test chunking produces expected chunk sizes and overlap
                    chunks = text_processing.chunk_text_semantically(section_text, config.TARGET_CHUNK_SIZE)

                    chunk_sequence = 0
                    for chunk_text in chunks:
                        if chunk_text: # Ensure chunk is not empty
                            all_chunks_for_embedding.append((section_id, chunk_text, chunk_sequence))
                            chunk_sequence += 1
                    section_sequence += 1
            except Exception as e:
                logger.error(f"Chunking or DB section insert failed for doc {doc_id}: {e}", exc_info=True)
                raise RuntimeError(f"Chunking/Section DB insert failed: {e}") from e

            if not all_chunks_for_embedding:
                 logger.warning(f"No text chunks generated for document {doc_id} ({relative_path_str}).")
                 # Decide if this is an error or just a warning. For now, treat as success with no chunks.
                 return {"status": "Success", "document_id": doc_id, "message": "Document added but no text chunks generated."}

            # 4. Embedding Generation (via LiteLLM Proxy)
            try:
                all_embeddings = await get_embeddings_in_batches(all_chunks_for_embedding)
            except Exception as e:
                logger.error(f"Embedding generation failed for doc {doc_id}: {e}", exc_info=True)
                raise RuntimeError(f"Embedding generation failed: {e}") from e

            # 5. Database Indexing (Chunks with Embeddings)
            chunks_to_index = []
            if len(all_embeddings) != len(all_chunks_for_embedding):
                 logger.error(f"Embedding count mismatch before indexing for doc {doc_id}: Expected {len(all_chunks_for_embedding)}, got {len(all_embeddings)}")
                 raise RuntimeError("Embedding count mismatch before indexing.")

            for i, (section_id, chunk_text, chunk_sequence) in enumerate(all_chunks_for_embedding):
                chunks_to_index.append((section_id, chunk_text, chunk_sequence, all_embeddings[i]))

            try:
                logger.info(f"Indexing {len(chunks_to_index)} chunks for doc {doc_id}...")
                await db_layer.add_chunks_batch(conn, chunks_to_index)
                logger.info(f"Successfully indexed chunks for doc {doc_id}.")
            except Exception as e:
                logger.error(f"Indexing chunks failed for doc {doc_id}: {e}", exc_info=True)
                raise RuntimeError(f"DB chunk indexing failed: {e}") from e

            # 6. Citation Parsing & Linking (Optional/Basic)
            try:
                raw_references = extracted_data.get('references_raw')
                if raw_references:
                    logger.info(f"Parsing {len(raw_references)} raw references for doc {doc_id}...")
                    parsed_references = await text_processing.parse_references(raw_references)
                    # TDD: Test reference parsing extracts key fields (author, title, year)
                    # TDD: Test linking references to source chunks (requires chunk IDs or mapping)

                    # Basic Tier 0: Store parsed details linked to the document ID
                    # More advanced: Link to specific chunks where citation occurred (requires more complex extraction)
                    if parsed_references:
                        # Example: Add references linked to the first chunk of the document (very basic)
                        # A better approach would require mapping refs back to text locations
                        first_chunk_id_query = "SELECT id FROM chunks WHERE section_id IN (SELECT id FROM sections WHERE doc_id = %s) ORDER BY sequence ASC LIMIT 1;"
                        async with conn.cursor() as cur:
                            await cur.execute(first_chunk_id_query, (doc_id,))
                            first_chunk_res = await cur.fetchone()
                            link_chunk_id = first_chunk_res['id'] if first_chunk_res else None

                        if link_chunk_id:
                            for ref_details in parsed_references:
                                try:
                                    await db_layer.add_reference(conn, link_chunk_id, ref_details)
                                except Exception as ref_e:
                                     # logger.warning(f"Failed to add parsed reference to DB for doc {doc_id}: {ref_e}", exc_info=True)
                                     # Re-raise to fail the transaction
                                     raise RuntimeError(f"DB reference insert failed: {ref_e}") from ref_e
                            # logger.info(f"Stored {len(parsed_references)} parsed reference details for doc {doc_id}.") # This won't be reached if an error occurs
                        else:
                             logger.warning(f"Could not find a chunk to link references to for doc {doc_id}.")
            except Exception as e:
                # logger.warning(f"Reference parsing/storing failed for doc {doc_id}: {e}", exc_info=True)
                # Re-raise to fail the transaction
                raise RuntimeError(f"Reference parsing/storing failed: {e}") from e

            # --- Transaction Commit ---
            # If we reach here without exceptions, the context manager commits implicitly

    except Exception as e:
        # Catch errors from the transactional block
        logger.error(f"Ingestion transaction failed for {relative_path_str} (Doc ID might be {doc_id} if created): {e}", exc_info=True)
        # Consider cleanup if needed (e.g., delete document if partially created), though rollback is handled
        return {"status": "Error", "message": f"Ingestion transaction failed: {e}"}

    # --- Completion ---
    logger.info(f"Successfully completed ingestion for: {relative_path_str} (Doc ID: {doc_id})")
    return {"status": "Success", "document_id": doc_id}

# Example of how to run this (e.g., from API handler)
# async def main_ingest(relative_path):
#     result = await process_document(relative_path)
#     print(result)

# if __name__ == "__main__":
#     # Example: Run ingestion for a specific file or directory
#     # Make sure DB and LiteLLM proxy are running
#     # Set environment variables first
#     target = "path/to/your/document.pdf" # Relative to SOURCE_FILE_DIR
#     asyncio.run(main_ingest(target))