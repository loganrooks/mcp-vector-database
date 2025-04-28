# PhiloGraph Tier 0 - Pseudocode: Text Processing Pipeline

## Overview

This module defines the workflow for processing source documents (PDF, EPUB, MD, TXT) into structured data (metadata, text chunks, embeddings, references) stored in the database. It orchestrates calls to various text processing tools, the LiteLLM Proxy for embeddings, and the Database Interaction Layer.

**Dependencies:**

*   Database Interaction Layer (`db_layer.py`)
*   External Tools/Services:
    *   GROBID (assumed accessible via HTTP API or local library call)
    *   PyMuPDF/ebooklib (Python libraries)
    *   `semchunk` (Python library)
    *   AnyStyle (optional, assumed accessible via HTTP API or local library call)
    *   LiteLLM Proxy (running locally, accessible via `{{LITELLM_PROXY_URL}}`)
*   Configuration:
    *   `{{SOURCE_FILE_DIR}}`: Base directory for source files.
    *   `{{LITELLM_PROXY_URL}}`: URL for the LiteLLM Proxy.
    *   `{{EMBEDDING_MODEL_NAME}}`: Internal model name configured in LiteLLM (e.g., "philo-embed").
    *   `{{TARGET_CHUNK_SIZE}}`: Target size for text chunks.
    *   `{{EMBEDDING_BATCH_SIZE}}`: Number of chunks to send per embedding request.
    *   `{{GROBID_API_URL}}` (if applicable)
    *   `{{ANYSTYLE_API_URL}}` (if applicable)

```pseudocode
IMPORT db_layer
IMPORT http_client // For calling GROBID, AnyStyle, LiteLLM
IMPORT file_system_utils
IMPORT text_processing_utils // Wrappers for PyMuPDF, semchunk, etc.
IMPORT logging

// --- Configuration ---
CONSTANT SOURCE_DIR = get_config("{{SOURCE_FILE_DIR}}")
CONSTANT LITELLM_URL = get_config("{{LITELLM_PROXY_URL}}")
CONSTANT EMBED_MODEL = get_config("{{EMBEDDING_MODEL_NAME}}")
CONSTANT CHUNK_SIZE = get_config("{{TARGET_CHUNK_SIZE}}")
CONSTANT BATCH_SIZE = get_config("{{EMBEDDING_BATCH_SIZE}}")
CONSTANT GROBID_URL = get_config("{{GROBID_API_URL}}", optional=True) // URL for GROBID service if external
CONSTANT ANYSTYLE_URL = get_config("{{ANYSTYLE_API_URL}}", optional=True) // URL for AnyStyle service if external

// --- Main Ingestion Function ---
FUNCTION process_document(file_path_relative):
    // TDD: Test processing a valid PDF file successfully
    // TDD: Test processing a valid EPUB file successfully
    // TDD: Test processing a valid MD file successfully
    // TDD: Test processing a valid TXT file successfully
    // TDD: Test processing a file that already exists in DB (skip or update?)
    // TDD: Test handling of file not found error
    // TDD: Test handling of unsupported file type error
    // TDD: Test handling of errors during extraction, chunking, embedding, or indexing

    full_path = file_system_utils.join_paths(SOURCE_DIR, file_path_relative)
    logging.info(f"Starting ingestion for: {full_path}")

    IF NOT file_system_utils.file_exists(full_path):
        logging.error(f"File not found: {full_path}")
        RETURN {status: "Error", message: "File not found"}

    // Check if document already processed (based on source_path)
    db_conn = db_layer.get_db_connection()
    IF db_layer.check_document_exists(db_conn, file_path_relative):
        logging.warning(f"Document already processed: {file_path_relative}. Skipping.")
        db_layer.close_db_connection(db_conn)
        RETURN {status: "Skipped", message: "Document already exists"}
    db_layer.close_db_connection(db_conn) // Close initial check connection

    // 1. Extraction
    TRY:
        extracted_data = extract_content_and_metadata(full_path)
        IF extracted_data IS NULL:
            RETURN {status: "Error", message: "Extraction failed or unsupported format"}
        // extracted_data = { text_by_section: { "Section Title": "Text..." }, metadata: {...}, references_raw: [...] }
    CATCH Exception as e:
        logging.error(f"Extraction failed for {full_path}: {e}")
        RETURN {status: "Error", message: f"Extraction failed: {e}"}

    // 2. Database Entry (Initial Document)
    db_conn = db_layer.get_db_connection()
    TRY:
        doc_id = db_layer.add_document(db_conn,
                                       extracted_data.metadata.get('title'),
                                       extracted_data.metadata.get('author'),
                                       extracted_data.metadata.get('year'),
                                       file_path_relative,
                                       extracted_data.metadata)
        logging.info(f"Added document record with ID: {doc_id}")
    CATCH Exception as e:
        logging.error(f"Failed to add document record for {file_path_relative}: {e}")
        db_layer.close_db_connection(db_conn)
        RETURN {status: "Error", message: f"DB document insert failed: {e}"}

    // 3. Chunking & Embedding Preparation
    all_chunks_for_embedding = [] // List of (section_id, chunk_text, chunk_sequence)
    section_mapping = {} // Map section title/sequence to section_id

    TRY:
        section_sequence = 0
        FOR section_title, section_text in extracted_data.text_by_section.items():
            // Add section to DB
            section_id = db_layer.add_section(db_conn, doc_id, section_title, extracted_data.metadata.get('structure_level', 0), section_sequence)
            section_mapping[section_sequence] = section_id
            section_sequence += 1

            // Chunk the section text
            // TDD: Test chunking produces expected chunk sizes and overlap
            chunks = text_processing_utils.chunk_text_semantically(section_text, CHUNK_SIZE)

            chunk_sequence = 0
            FOR chunk_text in chunks:
                all_chunks_for_embedding.append((section_id, chunk_text, chunk_sequence))
                chunk_sequence += 1
    CATCH Exception as e:
        logging.error(f"Chunking or DB section insert failed for doc {doc_id}: {e}")
        // Consider cleanup: delete document record?
        db_layer.close_db_connection(db_conn)
        RETURN {status: "Error", message: f"Chunking/Section DB insert failed: {e}"}

    // 4. Embedding Generation (via LiteLLM Proxy)
    all_embeddings = []
    TRY:
        logging.info(f"Requesting embeddings for {len(all_chunks_for_embedding)} chunks...")
        all_embeddings = get_embeddings_in_batches(all_chunks_for_embedding, LITELLM_URL, EMBED_MODEL, BATCH_SIZE)
        logging.info(f"Received {len(all_embeddings)} embeddings.")
        ASSERT len(all_embeddings) == len(all_chunks_for_embedding)
    CATCH Exception as e:
        logging.error(f"Embedding generation failed for doc {doc_id}: {e}")
        // Consider cleanup
        db_layer.close_db_connection(db_conn)
        RETURN {status: "Error", message: f"Embedding generation failed: {e}"}

    // 5. Database Indexing (Chunks with Embeddings)
    chunks_to_index = []
    FOR i, (section_id, chunk_text, chunk_sequence) in enumerate(all_chunks_for_embedding):
        chunks_to_index.append((section_id, chunk_text, chunk_sequence, all_embeddings[i]))

    TRY:
        logging.info(f"Indexing {len(chunks_to_index)} chunks...")
        db_layer.add_chunks_batch(db_conn, chunks_to_index)
        logging.info(f"Successfully indexed chunks for doc {doc_id}.")
    CATCH Exception as e:
        logging.error(f"Indexing chunks failed for doc {doc_id}: {e}")
        // Consider cleanup
        db_layer.close_db_connection(db_conn)
        RETURN {status: "Error", message: f"DB chunk indexing failed: {e}"}

    // 6. Citation Parsing & Linking (Optional/Basic)
    TRY:
        IF extracted_data.references_raw:
            logging.info(f"Parsing {len(extracted_data.references_raw)} raw references...")
            parsed_references = parse_references(extracted_data.references_raw)
            // TDD: Test reference parsing extracts key fields (author, title, year)
            // TDD: Test linking references to source chunks (requires chunk IDs or mapping)
            // For Tier 0, might just store parsed details without complex linking
            // Example: Store in `references` table linked to document or section ID
            // placeholder_chunk_id = get_first_chunk_id_for_doc(db_conn, doc_id) // Simplistic linking
            // FOR ref_details in parsed_references:
            //     db_layer.add_reference(db_conn, placeholder_chunk_id, ref_details)
            logging.info("Stored parsed reference details.") // Adjust log based on actual storage
    CATCH Exception as e:
        logging.warning(f"Reference parsing/storing failed for doc {doc_id}: {e}")
        // Non-critical failure, continue processing

    // --- Completion ---
    db_layer.close_db_connection(db_conn)
    logging.info(f"Successfully completed ingestion for: {file_path_relative} (Doc ID: {doc_id})")
    RETURN {status: "Success", document_id: doc_id}

END FUNCTION

// --- Helper: Content Extraction ---
FUNCTION extract_content_and_metadata(full_path):
    file_type = file_system_utils.get_file_extension(full_path).lower()

    IF file_type == ".pdf":
        // TDD: Test GROBID PDF extraction returns text, metadata, refs
        // TDD: Test handling of GROBID API errors (if using API)
        // TDD: Test handling of complex PDF layouts
        RETURN call_grobid_extractor(full_path) // Assumes returns dict {text_by_section, metadata, references_raw}
    ELSE IF file_type == ".epub":
        // TDD: Test EPUB extraction returns text and metadata
        // TDD: Test handling of encrypted/DRM EPUBs (expect failure)
        RETURN text_processing_utils.extract_epub_content(full_path) // Assumes returns dict {text_by_section, metadata, references_raw=None}
    ELSE IF file_type == ".md" OR file_type == ".txt":
        // TDD: Test TXT/MD extraction reads content correctly
        // TDD: Test MD extraction handles frontmatter metadata
        RETURN text_processing_utils.extract_text_content(full_path) // Assumes returns dict {text_by_section={"main": content}, metadata, references_raw=None}
    ELSE:
        logging.warning(f"Unsupported file type: {file_type}")
        RETURN NULL
END FUNCTION

FUNCTION call_grobid_extractor(pdf_path):
    // Implementation depends on whether GROBID is a service or library
    // If service:
    //   response = http_client.post(f"{GROBID_URL}/processFulltextDocument", files={'input': open(pdf_path, 'rb')})
    //   response.raise_for_status()
    //   tei_xml = response.text
    // If library:
    //   tei_xml = grobid_client.process("processFulltextDocument", pdf_path)

    // TDD: Test parsing of GROBID TEI XML for structure, text, metadata, biblio
    parsed_data = text_processing_utils.parse_grobid_tei(tei_xml)
    RETURN parsed_data // {text_by_section, metadata, references_raw}
END FUNCTION

// --- Helper: Embedding Generation ---
FUNCTION get_embeddings_in_batches(chunks_data, litellm_url, model_name, batch_size):
    all_embeddings = []
    total_chunks = len(chunks_data)
    FOR i in range(0, total_chunks, batch_size):
        batch = chunks_data[i : i + batch_size]
        chunk_texts = [item[1] for item in batch] // Extract text from (section_id, text, sequence)

        logging.debug(f"Requesting embeddings for batch {i//batch_size + 1} ({len(chunk_texts)} chunks)")
        // TDD: Test successful embedding request via LiteLLM proxy
        // TDD: Test handling of HTTP errors from LiteLLM proxy
        // TDD: Test handling of errors reported in LiteLLM response body
        // TDD: Test retry logic (potentially handled by LiteLLM itself)
        response = http_client.post(
            f"{litellm_url}/embeddings",
            json={"model": model_name, "input": chunk_texts},
            headers={"Authorization": "Bearer {{LITELLM_API_KEY}}"} // Or however auth is handled
        )
        response.raise_for_status() // Check for HTTP errors
        response_data = response.json()

        IF 'data' not in response_data OR len(response_data['data']) != len(chunk_texts):
            RAISE ValueError("Mismatch between requested and received embeddings in batch")

        batch_embeddings = [item['embedding'] for item in response_data['data']]
        all_embeddings.extend(batch_embeddings)
        logging.debug(f"Received embeddings for batch {i//batch_size + 1}")

    RETURN all_embeddings
END FUNCTION

// --- Helper: Citation Parsing ---
FUNCTION parse_references(raw_references):
    // raw_references: List of strings or structured data from GROBID
    // TDD: Test parsing various citation string formats
    // TDD: Test using AnyStyle if available and configured
    // TDD: Test extraction of key fields (author, title, year)
    parsed_details_list = []
    FOR ref in raw_references:
        IF ANYSTYLE_URL:
            // response = http_client.post(ANYSTYLE_URL, json={'references': [ref]})
            // parsed = response.json()[0] // Assuming AnyStyle API format
            parsed = call_anystyle_parser(ref)
        ELSE:
            // Fallback: Basic parsing using regex or simple heuristics on GROBID output
            parsed = text_processing_utils.basic_reference_parser(ref)

        IF parsed: // Only add if parsing was somewhat successful
            parsed_details_list.append(parsed)
    RETURN parsed_details_list
END FUNCTION

FUNCTION call_anystyle_parser(reference_string):
    // Placeholder for actual AnyStyle API call logic
    // ...
    RETURN {"title": "Parsed Title", "author": "Parsed Author", "year": "Parsed Year"} // Example
END FUNCTION