import logging
import uuid
from typing import Any, Dict, List, Optional

from .. import config
from ..ingestion import pipeline as ingestion_pipeline # To trigger ingestion
from ..utils import mcp_utils # For simulated MCP calls

logger = logging.getLogger(__name__)

async def initiate_acquisition(query: str, search_type: str, download: bool) -> str:
    """Placeholder for initiating acquisition."""
    logger.info(f"Placeholder: Initiating acquisition for query='{query}', type='{search_type}', download={download}")
    # In a real implementation, this would likely call start_acquisition_search
    # or similar logic and return a generated ID.
    return f"placeholder_acq_{uuid.uuid4()}"
# --- State Management (Simple In-Memory Example for Tier 0) ---
# WARNING: This state is lost on service restart. A persistent store (DB) is needed for robustness.
# Structure: { acquisition_id: { status: str, details: dict, search_results: list | None, selected_book: dict | None, error_message: str | None, processed_path: str | None, philo_doc_id: int | None } }
acquisition_requests: Dict[str, Dict[str, Any]] = {}

# --- Main Acquisition Functions ---

async def start_acquisition_search(text_details: Dict[str, str]) -> Dict[str, Any]:
    """
    Starts the process of acquiring a text by searching via zlibrary-mcp.

    Args:
        text_details: Dictionary containing text metadata (e.g., title, author).

    Returns:
        A dictionary indicating the status ('needs_confirmation' or 'error')
        and relevant data (search_results, acquisition_id, message).
    """
    # TDD: Test successful search returns results and 'needs_confirmation' status
    # TDD: Test search with no results returns appropriate status/message
    # TDD: Test handling of errors during MCP call to 'search_books'
    if not text_details or not isinstance(text_details, dict):
        logger.error("start_acquisition_search called with invalid text_details")
        return {"status": "error", "message": "Invalid text details provided."}

    query_str = f"{text_details.get('title', '')} {text_details.get('author', '')}".strip()
    if not query_str:
        logger.error("start_acquisition_search called with empty title and author.")
        return {"status": "error", "message": "Title or author must be provided for search."}

    logging.info(f"Starting acquisition search for: {text_details}")
    acquisition_id = str(uuid.uuid4())
    acquisition_requests[acquisition_id] = {"status": "searching", "details": text_details}

    try:
        search_args = {"query": query_str, "count": 5} # Limit initial results
        # TDD: Test construction of search query from text_details
        # TDD: Test MCP call simulation with correct server, tool, args
        mcp_response = await mcp_utils.call_mcp_tool(
            config.ZLIBRARY_MCP_SERVER_NAME,
            "search_books",
            search_args
        )

        # Assuming mcp_response contains a list of bookDetails objects if successful
        if mcp_response and isinstance(mcp_response, list) and len(mcp_response) > 0:
            logger.info(f"Found {len(mcp_response)} potential matches for acquisition {acquisition_id}.")
            acquisition_requests[acquisition_id]['status'] = 'confirming'
            # Store only essential details if response objects are large
            acquisition_requests[acquisition_id]['search_results'] = mcp_response
            return {
                "status": "needs_confirmation",
                "search_results": mcp_response,
                "acquisition_id": acquisition_id
            }
        else:
            logger.warning(f"No matches found via zlibrary-mcp for acquisition {acquisition_id} (Query: '{query_str}').")
            acquisition_requests[acquisition_id]['status'] = 'error'
            acquisition_requests[acquisition_id]['error_message'] = 'No matches found via zlibrary-mcp'
            # Clean up state for failed searches?
            # del acquisition_requests[acquisition_id]
            return {"status": "error", "message": "No matches found via zlibrary-mcp"}

    except mcp_utils.MCPValidationError as e:
        logger.error(f"MCP validation error during search_books for acquisition {acquisition_id}: {e}")
        acquisition_requests[acquisition_id]['status'] = 'error'
        acquisition_requests[acquisition_id]['error_message'] = f"MCP validation error: {e}"
        return {"status": "error", "message": f"MCP validation error: {e}"}
    except mcp_utils.MCPToolError as e:
        logger.error(f"MCP tool error during search_books for acquisition {acquisition_id}: {e}")
        acquisition_requests[acquisition_id]['status'] = 'error'
        acquisition_requests[acquisition_id]['error_message'] = f"MCP tool error: {e}"
        return {"status": "error", "message": f"MCP tool error: {e}"}
    except Exception as e:
        logger.exception(f"Unexpected error during zlibrary-mcp search for acquisition {acquisition_id}", exc_info=e)
        acquisition_requests[acquisition_id]['status'] = 'error'
        acquisition_requests[acquisition_id]['error_message'] = f"Unexpected error during search: {e}"
        return {"status": "error", "message": f"Unexpected error during search: {e}"}


async def confirm_and_trigger_download(acquisition_id: str, selected_book_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Confirms book selection, triggers download and processing via zlibrary-mcp,
    and then triggers the PhiloGraph ingestion pipeline.

    Args:
        acquisition_id: The ID of the ongoing acquisition process.
        selected_book_details: The full book details object selected by the user.

    Returns:
        A dictionary indicating the status ('processing', 'error', 'not_found')
        and relevant data (message, status_url).
    """
    # TDD: Test successful confirmation triggers download and returns 'processing' status
    # TDD: Test confirmation for non-existent acquisition_id returns 'not_found'
    # TDD: Test confirmation for acquisition not in 'confirming' state returns error
    # TDD: Test handling of errors during MCP call to 'download_book_to_file'
    # TDD: Test that ingestion_pipeline.process_document is called with the correct path on success

    if acquisition_id not in acquisition_requests:
        logger.warning(f"Attempted to confirm non-existent acquisition: {acquisition_id}")
        return {"status": "not_found", "message": "Acquisition ID not found."}

    request_state = acquisition_requests[acquisition_id]
    if request_state.get('status') != 'confirming':
        logger.warning(f"Attempted to confirm acquisition {acquisition_id} in invalid state: {request_state.get('status')}")
        return {"status": "error", "message": f"Invalid state for confirmation: {request_state.get('status')}"}

    if not selected_book_details or not isinstance(selected_book_details, dict):
         logger.error(f"Invalid selected_book_details provided for acquisition {acquisition_id}")
         return {"status": "error", "message": "Invalid selected book details."}

    logger.info(f"Confirming download for acquisition {acquisition_id}, book: {selected_book_details.get('title')}")
    request_state['status'] = 'processing_download' # More specific status
    request_state['selected_book'] = selected_book_details
    request_state.pop('search_results', None) # Clear search results

    try:
        download_args = {
            "bookDetails": selected_book_details,
            "process_for_rag": True
            # Optionally add "outputDir" if configurable paths are implemented in zlibrary-mcp
        }
        # TDD: Test MCP call simulation for download with correct args
        mcp_response = await mcp_utils.call_mcp_tool(
            config.ZLIBRARY_MCP_SERVER_NAME,
            "download_book_to_file",
            download_args
        )

        # Assuming mcp_response = { success: bool, processed_path: str | None, download_path: str | None, error: str | None }
        if mcp_response and mcp_response.get('success') is True and mcp_response.get('processed_path'):
            processed_file_path = mcp_response['processed_path']
            logger.info(f"Acquisition {acquisition_id}: zlibrary-mcp download and RAG processing successful. Processed file at: {processed_file_path}")
            request_state['processed_path'] = processed_file_path
            request_state['status'] = 'processing_ingestion'

            # Trigger PhiloGraph ingestion pipeline
            # Note: process_document expects path relative to SOURCE_FILE_DIR.
            # This assumes zlibrary-mcp writes to a location *outside* SOURCE_FILE_DIR,
            # and process_document needs to handle absolute paths or paths relative to project root.
            # For Tier 0, let's assume process_document can handle the absolute path returned by the mock.
            # A more robust solution might involve copying the file or configuring output paths.
            logger.info(f"Acquisition {acquisition_id}: Triggering PhiloGraph ingestion for {processed_file_path}...")
            # Run ingestion in background? For Tier 0 API, synchronous might be okay.
            ingestion_result = await ingestion_pipeline.process_document(processed_file_path)

            if ingestion_result.get('status') == 'Success':
                logger.info(f"Acquisition {acquisition_id}: PhiloGraph ingestion successful. Doc ID: {ingestion_result.get('document_id')}")
                request_state['status'] = 'complete'
                request_state['philo_doc_id'] = ingestion_result.get('document_id')
                return {
                    "status": "complete", # Indicate final success
                    "message": f"Acquisition and ingestion successful. PhiloGraph Doc ID: {request_state['philo_doc_id']}",
                    "document_id": request_state['philo_doc_id']
                 }
            elif ingestion_result.get('status') == 'Skipped':
                 logger.warning(f"Acquisition {acquisition_id}: PhiloGraph ingestion skipped (likely already exists). Message: {ingestion_result.get('message')}")
                 request_state['status'] = 'complete' # Treat skip as completion of acquisition process
                 request_state['philo_doc_id'] = None # Or query DB for existing ID?
                 return {
                    "status": "complete",
                    "message": f"Acquisition successful, ingestion skipped: {ingestion_result.get('message')}"
                 }
            else:
                ingestion_error = ingestion_result.get('message', 'Unknown ingestion error')
                logger.error(f"Acquisition {acquisition_id}: PhiloGraph ingestion failed after download. Reason: {ingestion_error}")
                request_state['status'] = 'error'
                request_state['error_message'] = f"Ingestion failed: {ingestion_error}"
                return {"status": "error", "message": f"Ingestion failed after download: {ingestion_error}"}

        else:
            # Handle failure from zlibrary-mcp download/process step
            error_msg = mcp_response.get('error', 'Unknown download/processing error') if mcp_response else 'No response from zlibrary-mcp'
            logger.error(f"Acquisition {acquisition_id}: zlibrary-mcp download_book_to_file failed. Reason: {error_msg}")
            request_state['status'] = 'error'
            request_state['error_message'] = f"zlibrary-mcp download/process failed: {error_msg}"
            return {"status": "error", "message": f"zlibrary-mcp download/process failed: {error_msg}"}

    except mcp_utils.MCPValidationError as e:
        logger.error(f"MCP validation error during download_book_to_file for acquisition {acquisition_id}: {e}")
        request_state['status'] = 'error'
        request_state['error_message'] = f"MCP validation error: {e}"
        return {"status": "error", "message": f"MCP validation error: {e}"}
    except mcp_utils.MCPToolError as e:
        logger.error(f"MCP tool error during download_book_to_file for acquisition {acquisition_id}: {e}")
        request_state['status'] = 'error'
        request_state['error_message'] = f"MCP tool error: {e}"
        return {"status": "error", "message": f"MCP tool error: {e}"}
    except Exception as e:
        logger.exception(f"Unexpected error during zlibrary-mcp download/ingestion trigger for acquisition {acquisition_id}", exc_info=e)
        request_state['status'] = 'error'
        request_state['error_message'] = f"Unexpected error during download/ingestion: {e}"
        return {"status": "error", "message": f"Unexpected error during download/ingestion: {e}"}


async def get_acquisition_status(acquisition_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the current status of an acquisition process.

    Args:
        acquisition_id: The ID of the acquisition process.

    Returns:
        The status dictionary or None if the ID is not found.
    """
    # TDD: Test retrieving status for various states (searching, confirming, processing, complete, error)
    # TDD: Test retrieving status for non-existent ID returns None
    logger.debug(f"Getting status for acquisition {acquisition_id}")
    return acquisition_requests.get(acquisition_id, None)

# --- Optional: Function to identify missing texts ---
# This requires more complex DB interaction and is deferred for Tier 0 implementation focus.
# async def find_missing_texts_from_citations(threshold: int = 5) -> List[Dict[str, str]]:
#     # ... implementation using db_layer ...
#     pass