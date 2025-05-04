import logging
import uuid
import time
from collections import deque
# Use TypedDict for better session structure definition
from typing import Any, Dict, List, Optional, Set, Union, TypedDict

from .. import config
from ..data_access import db_layer # Added for potential future DB interaction
from ..ingestion import pipeline as ingestion_pipeline # To trigger ingestion
from ..utils import mcp_utils # For simulated MCP calls

logger = logging.getLogger(__name__)

# --- Rate Limiting Configuration (Tier 0 - In-Memory) ---
# Kept from previous version
SEARCH_RATE_LIMIT_WINDOW_SECONDS = 60
SEARCH_RATE_LIMIT_MAX_REQUESTS = 10
DOWNLOAD_RATE_LIMIT_WINDOW_SECONDS = 60
DOWNLOAD_RATE_LIMIT_MAX_REQUESTS = 5
SESSION_TIMEOUT_SECONDS = 3600 # 1 hour example from pseudocode

# Global state for rate limiting (using deque for efficient window management)
_search_request_timestamps: deque = deque(maxlen=SEARCH_RATE_LIMIT_MAX_REQUESTS)
_download_request_timestamps: deque = deque(maxlen=DOWNLOAD_RATE_LIMIT_MAX_REQUESTS)

# --- State Management (Simple In-Memory Example for Tier 0) ---
# WARNING: This state is lost on service restart. A persistent store (DB) is needed for robustness.
discovery_sessions: Dict[str, Dict[str, Any]] = {}
# Define the structure of a discovery session using TypedDict
class ProcessedItemStatus(TypedDict):
    id: str
    title: str
    status: str # e.g., "pending_download", "downloading", "downloaded", "ingesting", "ingested", "skipped", "download_failed", "ingestion_failed", "processing_error"
    error: Optional[str]
    document_id: Optional[str]

class DiscoverySession(TypedDict):
    status: str # e.g., "pending_confirmation", "processing", "complete", "complete_with_errors", "error"
    created_at: float
    candidates: List[Dict[str, Any]] # List of book details from zlib search
    selected_items: List[Dict[str, Any]] # List of validated book details selected by user
    processed_items: List[ProcessedItemStatus] # Status tracking for each selected item
    error_message: Optional[str]

discovery_sessions: Dict[str, DiscoverySession] = {}


# --- Helper Functions: Session Management ---

def create_discovery_session() -> str:
    """Creates a new discovery session and returns its ID."""
    # TDD: Test session creation returns a valid UUID
    discovery_id = str(uuid.uuid4())
    discovery_sessions[discovery_id] = {
        "status": "pending_confirmation", # Initial state after discovery
        "created_at": time.time(),
        "candidates": [],
        "selected_items": [],
        "processed_items": [], # Track status of each selected item
        "error_message": None
    }
    logger.info(f"Created discovery session: {discovery_id}")
    return discovery_id

def get_discovery_session(discovery_id: str) -> Optional[DiscoverySession]:
    """Retrieves an active discovery session, returns None if not found or expired."""
    session = discovery_sessions.get(discovery_id)
    if session:
        if time.time() - session['created_at'] > SESSION_TIMEOUT_SECONDS:
            logger.warning(f"Discovery session {discovery_id} has expired.")
            # Optionally remove expired session: del discovery_sessions[discovery_id]
            return None # Treat expired as not found
        return session
    return None

def update_discovery_session(discovery_id: str, updates: Dict[str, Any]) -> bool:
    """Updates an existing discovery session.

    Note: This performs a partial update. For type safety with TypedDict,
    care must be taken, but for this simple in-memory store, it's acceptable.
    A more robust implementation might use a dedicated update mechanism.
    """
    session = get_discovery_session(discovery_id) # Use getter to check expiry
    if session:
        session.update(updates)
        logger.debug(f"Updated discovery session {discovery_id}: {updates}")
        return True
    else:
        logger.error(f"Attempted to update non-existent or expired session: {discovery_id}")
        return False


# --- Helper Functions: Rate Limiting ---

def _check_rate_limit(timestamps: deque, max_requests: int, window_seconds: int, resource_name: str) -> bool:
    """Checks if the rate limit for a given resource has been exceeded.

    Args:
        timestamps: Deque storing request timestamps.
        max_requests: Maximum requests allowed in the window.
        window_seconds: The time window in seconds.
        resource_name: Name of the resource being limited (for logging).

    Returns:
        True if the rate limit is exceeded, False otherwise.
    """
    current_time = time.time()
    # Remove timestamps older than the window
    while timestamps and timestamps[0] <= current_time - window_seconds:
        timestamps.popleft()
    # Check if limit is exceeded
    if len(timestamps) >= max_requests:
        logger.warning(f"{resource_name} rate limit exceeded.")
        return True
    # Record current request timestamp
    timestamps.append(current_time)
    return False


# --- Helper Functions: Validation (Kept from previous version) ---

# Expected keys for book details validation (SR-ACQ-001)
EXPECTED_BOOK_KEYS: Set[str] = {
    'title', 'author', 'publisher', 'year', 'language',
    'extension', 'size', 'md5', 'cover_url', 'download_url',
    'id', 'zlibrary_id', 'source', 'isbn', 'series', 'volume',
    'edition', 'pages', 'description', 'tags', 'rating', 'uploader',
    'upload_date', 'last_modified_date', 'ipfs_cid', 'file_format',
}
REQUIRED_BOOK_KEYS: Set[str] = {'md5', 'download_url'} # Keys absolutely needed for download

def _validate_book_details(details: Dict[str, Any]) -> bool:
    """Validates the structure and content of book details for download."""
    if not isinstance(details, dict):
        logger.error("Validation failed: Book details is not a dictionary.")
        return False

    unexpected_keys = set(details.keys()) - EXPECTED_BOOK_KEYS
    if unexpected_keys:
        logger.warning(f"Validation warning: Unexpected keys found in book details: {unexpected_keys}")
        # Logging only for Tier 0

    missing_keys = REQUIRED_BOOK_KEYS - set(details.keys())
    if missing_keys:
        logger.error(f"Validation failed: Missing required keys in book details: {missing_keys}")
        return False

    if not isinstance(details.get('md5'), str) or not details['md5']:
        logger.error("Validation failed: Invalid or missing 'md5'.")
        return False
    if not isinstance(details.get('download_url'), str) or not details['download_url']:
        logger.error("Validation failed: Invalid or missing 'download_url'.")
        return False
    if 'title' in details and not isinstance(details['title'], str):
         logger.warning("Validation warning: 'title' is not a string.")
    if 'author' in details and not isinstance(details['author'], str):
         logger.warning("Validation warning: 'author' is not a string.")

    return True


# --- Helper Functions: Confirmation Validation ---

def _validate_selected_items(
    selected_items: List[Union[str, Dict[str, Any]]],
    session_candidates: List[Dict[str, Any]]
) -> tuple[List[Dict[str, Any]], List[str]]:
    """
    Validates selected items against session candidates and book details schema.

    Args:
        selected_items: List of items selected by the user (IDs or full details).
        session_candidates: List of candidate dictionaries from the discovery session.

    Returns:
        A tuple containing:
            - valid_selections: List of validated book detail dictionaries.
            - invalid_selection_details: List of error messages for invalid items.
    """
    valid_selections: List[Dict[str, Any]] = []
    invalid_selection_details: List[str] = []

    # Create a map for easy lookup, using md5 if available, otherwise index as fallback ID
    candidate_map = {}
    for i, c in enumerate(session_candidates):
        if isinstance(c, dict):
            candidate_id = c.get('md5') or f"index_{i}" # Use md5 or index
            candidate_map[candidate_id] = c

    for item in selected_items:
        item_id = None
        book_details = None
        if isinstance(item, str): # Assume it's an ID (md5 or index_*)
            item_id = item
            if item_id in candidate_map:
                book_details = candidate_map[item_id]
            else:
                invalid_selection_details.append(f"ID '{item_id}' not found in candidates.")
        elif isinstance(item, dict) and item.get('md5'): # Assume it's full details with md5
            item_id = item['md5']
            # Check if this md5 was among the candidates presented
            if item_id in candidate_map:
                book_details = item # Use the provided details
            else:
                # Allow confirmation even if not strictly in candidate list? Maybe if md5 is valid?
                # For now, require it to be in the candidate list for safety.
                logger.warning(f"Item with md5 '{item_id}' provided for confirmation but not found in original candidates.")
                invalid_selection_details.append(f"Item with md5 '{item_id}' not found in candidates.")
        else:
            invalid_selection_details.append(f"Invalid item format in selection: {type(item)}")

        if book_details:
            # --- Input Validation (SR-ACQ-001) ---
            if _validate_book_details(book_details):
                valid_selections.append(book_details)
            else:
                logger.error(f"Validation failed for selected book details (ID: {item_id})")
                invalid_selection_details.append(f"Validation failed for item ID '{item_id}'.")
            # --- End Input Validation ---

    return valid_selections, invalid_selection_details


# --- Helper Functions: Item Processing ---

async def _process_single_item(book_details: Dict[str, Any], discovery_id: str) -> Dict[str, Any]:
    """
    Handles the download, processing (via MCP), and ingestion of a single selected book.

    Args:
        book_details: The validated details of the book to process.
        discovery_id: The ID of the parent discovery session (for logging).

    Returns:
        A dictionary representing the processing status of the item.
    """
    item_id = book_details.get('md5', 'unknown')
    item_title = book_details.get('title', 'Unknown Title')
    item_status = {"id": item_id, "title": item_title, "status": "pending_download", "error": None, "document_id": None}

    try:
        logger.info(f"Triggering download for '{item_title}' (Discovery: {discovery_id})")
        item_status['status'] = "downloading"
        download_args = {
            "bookDetails": book_details,
            "process_for_rag": True,
            "processed_output_format": "text" # Or markdown? Configurable?
        }
        mcp_response = await mcp_utils.call_mcp_tool(
            config.ZLIBRARY_MCP_SERVER_NAME,
            "download_book_to_file",
            download_args
        )

        if mcp_response and mcp_response.get('success') is True and mcp_response.get('processed_path'):
            processed_file_path = mcp_response['processed_path']
            item_status['status'] = "downloaded"
            logger.info(f"Download successful for '{item_title}'. Path: {processed_file_path}")

            # Trigger ingestion
            item_status['status'] = "ingesting"
            logger.info(f"Triggering PhiloGraph ingestion for {processed_file_path}...")
            # Assuming process_document can handle the path returned by MCP
            ingestion_result = await ingestion_pipeline.process_document(processed_file_path)

            if ingestion_result.get('status') == 'Success':
                item_status['status'] = "ingested"
                item_status['document_id'] = ingestion_result.get('document_id')
                logger.info(f"Ingestion successful for '{item_title}'. Doc ID: {item_status['document_id']}")
            elif ingestion_result.get('status') == 'Skipped':
                item_status['status'] = "skipped" # More specific than ingested
                logger.warning(f"Ingestion skipped for '{item_title}'. Message: {ingestion_result.get('message')}")
                # Still counts as overall success for this item's processing
            else:
                item_status['status'] = "ingestion_failed"
                item_status['error'] = ingestion_result.get('message', 'Unknown ingestion error')
                logger.error(f"Ingestion failed for '{item_title}': {item_status['error']}")
        else:
            error_msg = mcp_response.get('error', 'Unknown download/processing error') if mcp_response else 'No response from MCP server'
            item_status['status'] = "download_failed"
            item_status['error'] = error_msg
            logger.error(f"Download failed for '{item_title}': {error_msg}")

    except mcp_utils.MCPValidationError as e:
            logger.error(f"MCP validation error during download for '{item_title}': {e}")
            item_status['status'] = "processing_error"
            item_status['error'] = f"MCP Validation Error: {e}"
    except mcp_utils.MCPToolError as e:
        logger.error(f"MCP tool error during download for '{item_title}': {e}")
        item_status['status'] = "processing_error"
        item_status['error'] = f"MCP Tool Error: {e}"
    except Exception as e:
        item_status['status'] = "processing_error"
        item_status['error'] = str(e)
        logger.exception(f"Unexpected error processing item '{item_title}' for discovery {discovery_id}", exc_info=e)

    return item_status


# --- Core Service Functions (New Workflow) ---

async def handle_discovery_request(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles the discovery phase: finds potential candidates based on filters
    and searches for them using zlibrary-mcp.
    """
    logger.info(f"Handling discovery request with filters: {filters}")

    # --- Rate Limiting Check (SR-ACQ-002) ---
    if _check_rate_limit(_search_request_timestamps, SEARCH_RATE_LIMIT_MAX_REQUESTS, SEARCH_RATE_LIMIT_WINDOW_SECONDS, "Search"):
        return {"status": "error", "message": "Search rate limit exceeded. Please try again later."}
    # --- End Rate Limiting Check ---

    discovery_id = create_discovery_session()
    potential_candidates_details: List[Dict[str, str]] = []

    # 1. Find potential missing texts based on filters (using db_layer - Placeholder for Tier 0)
    #    For Tier 0, we'll simplify and pass filters directly to zlib search.
    #    A real implementation would query the DB first.
    try:
        # --- Placeholder DB Query Logic ---
        if "threshold" in filters:
            logger.warning("DB query for citation threshold not implemented in Tier 0 service.")
            potential_candidates_details.append(filters) # Simplification
        elif "author" in filters or "title" in filters:
            logger.warning("DB query for author/title filter not implemented in Tier 0 service.")
            potential_candidates_details.append(filters) # Simplification
        else:
             logger.warning("Filter logic beyond threshold/author/title not implemented in Tier 0 service.")
             potential_candidates_details.append(filters) # Simplification
        # --- End Placeholder DB Query Logic ---

    except Exception as e:
        logger.error(f"Error during placeholder DB candidate finding: {e}", exc_info=True)
        update_discovery_session(discovery_id, {"status": "error", "error_message": f"Candidate finding failed: {e}"})
        return {"status": "error", "message": f"Candidate finding failed: {e}"}

    if not potential_candidates_details:
        logger.info(f"No potential candidates identified in DB for discovery {discovery_id}")
        # If DB query was the *only* source and it's empty, we might stop here.
        # Since we are simplifying, we proceed to zlib search anyway.
        pass # Proceed to zlib search even if DB step is skipped/empty for now

    # 2. Search for each potential candidate using zlibrary-mcp
    all_zlib_results = []
    search_errors = []
    for candidate_detail in potential_candidates_details:
        try:
            query = f"{candidate_detail.get('title', '')} {candidate_detail.get('author', '')}".strip()
            if not query:
                logger.debug("Skipping candidate with empty title/author.")
                continue

            search_args = {"query": query, "count": 5} # Limit results per candidate
            logger.info(f"Calling zlibrary-mcp search_books for query: '{query}' (Discovery: {discovery_id})")
            mcp_response = await mcp_utils.call_mcp_tool(
                config.ZLIBRARY_MCP_SERVER_NAME,
                "search_books",
                search_args
            )

            if mcp_response and isinstance(mcp_response, list):
                logger.debug(f"Received {len(mcp_response)} results for query '{query}'")
                all_zlib_results.extend(mcp_response) # Simple aggregation
            else:
                 logger.debug(f"Received no results or invalid response for query '{query}'")


        except mcp_utils.MCPValidationError as e:
             logger.error(f"MCP validation error during search_books for candidate {candidate_detail}: {e}")
             search_errors.append(f"Validation Error: {e}")
        except mcp_utils.MCPToolError as e:
            logger.error(f"MCP tool error during search_books for candidate {candidate_detail}: {e}")
            search_errors.append(f"Tool Error: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error during zlibrary-mcp search for candidate {candidate_detail}", exc_info=e)
            search_errors.append(f"Unexpected Error: {e}")
            # Continue searching for other candidates

    # Note: Deduplication and ranking logic for all_zlib_results could be added here.

    if not all_zlib_results and search_errors:
         # If all searches failed
        error_summary = "; ".join(search_errors)
        update_discovery_session(discovery_id, {"status": "error", "error_message": f"All Z-Library searches failed: {error_summary}"})
        return {"status": "error", "message": f"Z-Library search failed: {error_summary}"}

    if not all_zlib_results:
        logger.info(f"No results found on Z-Library for discovery {discovery_id}")
        update_discovery_session(discovery_id, {"status": "complete", "candidates": []}) # Mark as complete, no candidates
        return {"status": "no_candidates", "discovery_id": discovery_id, "candidates": []}

    # 3. Store candidates and return
    update_discovery_session(discovery_id, {"candidates": all_zlib_results})
    logger.info(f"Discovery {discovery_id} successful, found {len(all_zlib_results)} candidates.")
    return {
        "status": "success",
        "discovery_id": discovery_id,
        "candidates": all_zlib_results
    }


async def handle_confirmation_request(discovery_id: str, selected_items: List[Union[str, Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Handles the confirmation phase: validates selections, triggers download/processing
    via zlibrary-mcp, and initiates ingestion.
    """
    logger.info(f"Handling confirmation request for discovery {discovery_id} with {len(selected_items)} items.")
    session = get_discovery_session(discovery_id)

    if not session:
        return {"status": "not_found", "message": "Discovery session not found or expired."}
    if session['status'] != 'pending_confirmation':
        logger.warning(f"Attempted confirmation on session {discovery_id} with status {session['status']}")
        return {"status": "invalid_state", "message": f"Discovery session is not awaiting confirmation (status: {session['status']})."}

    # Validate selected_items against session['candidates']
    valid_selections, invalid_selection_details = _validate_selected_items(
        selected_items, session.get('candidates', [])
    )

    if invalid_selection_details:
        logger.warning(f"Invalid items in confirmation for {discovery_id}: {invalid_selection_details}")
        # Proceed with valid items only
        if not valid_selections:
            update_discovery_session(discovery_id, {"status": "error", "error_message": "No valid items selected for confirmation."})
            return {"status": "invalid_selection", "message": "No valid items selected.", "details": "; ".join(invalid_selection_details)}

    if not valid_selections:
        logger.warning(f"No items selected for confirmation in session {discovery_id}")
        # Should this be an error or just do nothing? Treat as bad request for now.
        return {"status": "invalid_selection", "message": "No items selected."}

    # --- Rate Limiting Check (SR-ACQ-002) ---
    if _check_rate_limit(_download_request_timestamps, DOWNLOAD_RATE_LIMIT_MAX_REQUESTS, DOWNLOAD_RATE_LIMIT_WINDOW_SECONDS, "Download"):
        # Don't update session status yet, just return error
        return {"status": "error", "message": "Download rate limit exceeded. Please try again later."}
    # --- End Rate Limiting Check ---

    # Update session state *before* starting background tasks
    update_discovery_session(discovery_id, {
        "status": "processing",
        "selected_items": valid_selections,
        "processed_items": [] # Reset processed items list for this confirmation
    })

    # Trigger download and ingestion for each valid selection
    # For Tier 0, run sequentially. Consider background tasks (asyncio.create_task or Celery) later.
    all_success = True
    for book_details in valid_selections:
        item_processing_status = await _process_single_item(book_details, discovery_id)
        session['processed_items'].append(item_processing_status)
        if "fail" in item_processing_status.get("status", "") or "error" in item_processing_status.get("status", ""):
            all_success = False

    # Update final session status based on item outcomes
    final_status = "complete" if all_success else "complete_with_errors"
    update_discovery_session(discovery_id, {"status": final_status})
    logger.info(f"Confirmation processing finished for session {discovery_id} with status: {final_status}")

    # API should return ACCEPTED immediately, status checked via GET /acquire/status/{id}
    return {"status": "processing_started"}


async def get_status(discovery_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the status of a discovery session."""
    # TDD: Test retrieving status for various states (pending, processing, complete, error)
    # TDD: Test retrieving status includes details of processed items
    # TDD: Test retrieving status for non-existent/expired ID returns None
    logger.debug(f"Getting status for discovery session {discovery_id}")
    session = get_discovery_session(discovery_id) # Checks expiry
    return session