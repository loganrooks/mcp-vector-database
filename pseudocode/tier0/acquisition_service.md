# PhiloGraph Tier 0 - Pseudocode: Acquisition Service (Internal Logic)

## Overview

This module contains the internal business logic for the text acquisition workflow, corresponding to the `/acquire/discover` and `/acquire/confirm/{discovery_id}` API endpoints. It orchestrates interactions between the database layer (`db_layer`), the `zlibrary-mcp` server, and potentially the ingestion pipeline.

**Dependencies:**

*   `db_layer.py` (for querying citations, checking existing documents)
*   `ingestion_pipeline.py` (to trigger ingestion after successful download)
*   MCP Interaction Library (simulated as `mcp_call_tool`)
*   Configuration:
    *   `ZLIBRARY_MCP_SERVER_NAME`: Name of the zlibrary-mcp server.
*   State Management (e.g., in-memory dict for Tier 0, or DB table for persistence)

```pseudocode
IMPORT db_layer
IMPORT ingestion_pipeline
IMPORT mcp_interaction // Provides mcp_call_tool(server_name, tool_name, arguments)
IMPORT logging
IMPORT uuid
IMPORT time // For session expiry

// --- Configuration ---
CONSTANT ZLIB_SERVER = get_config("ZLIBRARY_MCP_SERVER_NAME", default="zlibrary-mcp")
CONSTANT SESSION_TIMEOUT_SECONDS = 3600 // 1 hour example

// --- State Management (Simple In-Memory Example for Tier 0) ---
// WARNING: This state is lost on service restart. A persistent store (DB) is needed for robustness.
discovery_sessions = {} // { discovery_id: { status: "pending_confirmation" | "processing" | "complete" | "error", created_at: timestamp, candidates: [...], selected_items: [...], processed_items: [...] } }

// --- Helper Functions: Session Management ---

FUNCTION create_discovery_session():
    // TDD: Test session creation returns a valid UUID
    discovery_id = str(uuid.uuid4())
    discovery_sessions[discovery_id] = {
        "status": "pending_confirmation", // Initial state after discovery
        "created_at": time.time(),
        "candidates": [],
        "selected_items": [],
        "processed_items": [] // Track status of each selected item
    }
    logging.info(f"Created discovery session: {discovery_id}")
    RETURN discovery_id
END FUNCTION

FUNCTION get_discovery_session(discovery_id):
    // TDD: Test retrieving an existing session
    // TDD: Test retrieving a non-existent session returns None
    // TDD: Test retrieving an expired session returns None or specific status
    session = discovery_sessions.get(discovery_id)
    IF session:
        IF time.time() - session['created_at'] > SESSION_TIMEOUT_SECONDS:
            logging.warning(f"Discovery session {discovery_id} has expired.")
            // Optionally remove expired session: del discovery_sessions[discovery_id]
            RETURN None // Treat expired as not found
        RETURN session
    RETURN None
END FUNCTION

FUNCTION update_discovery_session(discovery_id, updates):
    // TDD: Test updating session status
    // TDD: Test adding candidates to session
    // TDD: Test adding selected items to session
    // TDD: Test updating non-existent session raises error or returns False
    session = get_discovery_session(discovery_id) // Use getter to check expiry
    IF session:
        session.update(updates)
        logging.debug(f"Updated discovery session {discovery_id}: {updates}")
        RETURN True
    ELSE:
        logging.error(f"Attempted to update non-existent or expired session: {discovery_id}")
        RETURN False
END FUNCTION

// --- Core Service Functions ---

FUNCTION handle_discovery_request(filters):
    // filters: dict containing criteria like {"threshold": 5, "author": "Kant", "tags": ["ethics"]}
    // TDD: Test discovery based on citation threshold (requires mock db_layer)
    // TDD: Test discovery based on author/title filter (requires mock db_layer)
    // TDD: Test discovery combining multiple filters
    // TDD: Test discovery when db_layer finds potential candidates
    // TDD: Test discovery when db_layer finds no potential candidates
    // TDD: Test successful zlibrary search returns candidates and discovery_id
    // TDD: Test zlibrary search returning no results
    // TDD: Test handling of errors from db_layer during candidate finding
    // TDD: Test handling of errors from mcp_call_tool during zlibrary search

    logging.info(f"Handling discovery request with filters: {filters}")
    discovery_id = create_discovery_session()
    potential_candidates_details = [] // List of dicts like {"title": "...", "author": "..."}

    // 1. Find potential missing texts based on filters (using db_layer)
    db_conn = None // Manage connection appropriately
    TRY:
        db_conn = db_layer.get_db_connection()
        // --- Logic to query DB based on filters ---
        // Example: If threshold filter exists
        IF "threshold" in filters:
            threshold = filters["threshold"]
            // potential_candidates_details = db_layer.find_highly_cited_missing_docs(db_conn, threshold) // Hypothetical
            logging.warning("DB query for citation threshold not fully implemented in pseudocode.")
        // Example: If author/title filters exist
        ELIF "author" in filters or "title" in filters:
            # potential_candidates_details = db_layer.find_docs_matching_details(db_conn, filters) # Hypothetical
            logging.warning("DB query for author/title filter not fully implemented in pseudocode.")
            # For Tier 0, maybe just pass filters directly to zlib search? Simpler start.
            potential_candidates_details.append(filters) # Simplification for now
        ELSE:
             // Handle case with other filters (tags, etc.) or invalid filter combinations
             logging.warning("Filter logic beyond threshold/author/title not implemented in pseudocode.")
             potential_candidates_details.append(filters) # Simplification for now

    CATCH Exception as e:
        logging.error(f"Error querying database for discovery candidates: {e}", exc_info=True)
        update_discovery_session(discovery_id, {"status": "error", "error_message": f"Database query failed: {e}"})
        RETURN {"status": "error", "message": f"Database query failed: {e}"}
    FINALLY:
        IF db_conn: db_layer.close_db_connection(db_conn)

    IF not potential_candidates_details:
        logging.info(f"No potential candidates found in DB for discovery {discovery_id}")
        # Return success but empty, or a specific status? API returns OK with empty list.
        update_discovery_session(discovery_id, {"status": "complete", "candidates": []}) # Or a different terminal status?
        RETURN {"status": "no_candidates", "discovery_id": discovery_id, "candidates": []}

    // 2. Search for each potential candidate using zlibrary-mcp
    all_zlib_results = []
    search_errors = []
    FOR candidate_detail in potential_candidates_details:
        TRY:
            query = f"{candidate_detail.get('title', '')} {candidate_detail.get('author', '')}".strip()
            IF not query: continue

            search_args = {"query": query, "count": 5} # Limit results per candidate
            mcp_response = mcp_interaction.mcp_call_tool(ZLIB_SERVER, "search_books", search_args)

            IF mcp_response AND isinstance(mcp_response, list):
                all_zlib_results.extend(mcp_response) # Simple aggregation, might need deduplication/ranking later
        CATCH Exception as e:
            logging.error(f"MCP search_books call failed for candidate {candidate_detail}: {e}")
            search_errors.append(str(e))
            // Continue searching for other candidates

    IF not all_zlib_results and search_errors:
         # If all searches failed
        error_summary = "; ".join(search_errors)
        update_discovery_session(discovery_id, {"status": "error", "error_message": f"All Z-Library searches failed: {error_summary}"})
        RETURN {"status": "error", "message": f"Z-Library search failed: {error_summary}"}

    IF not all_zlib_results:
        logging.info(f"No results found on Z-Library for discovery {discovery_id}")
        update_discovery_session(discovery_id, {"status": "complete", "candidates": []}) # Or 'no_candidates'?
        RETURN {"status": "no_candidates", "discovery_id": discovery_id, "candidates": []}

    // TODO: Add deduplication and ranking logic for all_zlib_results if needed

    // 3. Store candidates and return
    update_discovery_session(discovery_id, {"candidates": all_zlib_results})
    RETURN {
        "status": "success",
        "discovery_id": discovery_id,
        "candidates": all_zlib_results
    }
END FUNCTION

FUNCTION handle_confirmation_request(discovery_id, selected_items):
    // selected_items: List of candidate IDs or full book details objects
    // TDD: Test successful confirmation triggers download for each selected item
    // TDD: Test confirmation with a mix of valid and invalid selected items
    // TDD: Test confirmation where zlib download fails for some items
    // TDD: Test confirmation where ingestion fails for some items
    // TDD: Test overall status update based on item processing results
    // TDD: Test confirmation for non-existent/expired discovery_id
    // TDD: Test confirmation for session not in 'pending_confirmation' state

    logging.info(f"Handling confirmation request for discovery {discovery_id} with {len(selected_items)} items.")
    session = get_discovery_session(discovery_id)

    IF not session:
        RETURN {"status": "not_found"}
    IF session['status'] != 'pending_confirmation':
        RETURN {"status": "invalid_state"}

    // Validate selected_items against session['candidates'] - requires IDs or robust matching
    // TDD: Add tests for selection validation logic
    valid_selections = []
    invalid_selection_details = []
    candidate_map = {c.get('md5') or str(i): c for i, c in enumerate(session['candidates'])} # Example using md5 or index as ID

    FOR item in selected_items:
        item_id = None
        book_details = None
        IF isinstance(item, str): # Assume it's an ID
            item_id = item
            IF item_id in candidate_map:
                book_details = candidate_map[item_id]
            ELSE:
                 invalid_selection_details.append(f"ID '{item_id}' not found in candidates.")
        ELIF isinstance(item, dict) and item.get('md5'): # Assume it's full details with md5
            item_id = item['md5']
            IF item_id in candidate_map: # Check if it was a candidate
                 book_details = item # Use the provided details
            ELSE:
                 invalid_selection_details.append(f"Item with md5 '{item_id}' not found in candidates.")
        ELSE:
            invalid_selection_details.append("Invalid item format in selection.")

        IF book_details:
            valid_selections.append(book_details)

    IF invalid_selection_details:
        logging.warning(f"Invalid items in confirmation for {discovery_id}: {invalid_selection_details}")
        # Option 1: Reject entire request
        # RETURN {"status": "invalid_selection", "details": "; ".join(invalid_selection_details)}
        # Option 2: Proceed with valid items only (chosen here)
        IF not valid_selections:
             RETURN {"status": "invalid_selection", "message": "No valid items selected.", "details": "; ".join(invalid_selection_details)}

    update_discovery_session(discovery_id, {"status": "processing", "selected_items": valid_selections, "processed_items": []})

    // Trigger download and ingestion for each valid selection (can be parallelized later)
    all_success = True
    for book_details in valid_selections:
        item_status = {"id": book_details.get('md5', 'unknown'), "title": book_details.get('title'), "status": "pending_download"}
        session['processed_items'].append(item_status)
        TRY:
            logging.info(f"Triggering download for '{book_details.get('title')}' (Discovery: {discovery_id})")
            item_status['status'] = "downloading"
            download_args = {
                "bookDetails": book_details,
                "process_for_rag": True,
                "processed_output_format": "text" // Or markdown? Configurable?
            }
            mcp_response = mcp_interaction.mcp_call_tool(ZLIB_SERVER, "download_book_to_file", download_args)

            IF mcp_response AND mcp_response.get('success') == True AND mcp_response.get('processed_path'):
                processed_file_path = mcp_response['processed_path']
                item_status['status'] = "downloaded"
                logging.info(f"Download successful for '{book_details.get('title')}'. Path: {processed_file_path}")

                // Trigger ingestion
                item_status['status'] = "ingesting"
                ingestion_result = ingestion_pipeline.process_document(processed_file_path)

                IF ingestion_result['status'] == 'Success':
                    item_status['status'] = "ingested"
                    item_status['document_id'] = ingestion_result['document_id']
                    logging.info(f"Ingestion successful for '{book_details.get('title')}'. Doc ID: {ingestion_result['document_id']}")
                ELSE:
                    item_status['status'] = "ingestion_failed"
                    item_status['error'] = ingestion_result.get('message')
                    logging.error(f"Ingestion failed for '{book_details.get('title')}': {item_status['error']}")
                    all_success = False
            ELSE:
                error_msg = mcp_response.get('error', 'Unknown download/processing error') if mcp_response else 'No response from MCP server'
                item_status['status'] = "download_failed"
                item_status['error'] = error_msg
                logging.error(f"Download failed for '{book_details.get('title')}': {error_msg}")
                all_success = False

        CATCH Exception as e:
            item_status['status'] = "processing_error"
            item_status['error'] = str(e)
            logging.exception(f"Unexpected error processing item '{book_details.get('title')}' for discovery {discovery_id}", exc_info=e)
            all_success = False

    // Update final session status
    final_status = "complete" if all_success else "complete_with_errors"
    update_discovery_session(discovery_id, {"status": final_status})

    RETURN {"status": "processing_started"} // API returns ACCEPTED immediately

END FUNCTION

FUNCTION get_status(discovery_id):
    // TDD: Test retrieving status for various states (pending, processing, complete, error)
    // TDD: Test retrieving status includes details of processed items
    // TDD: Test retrieving status for non-existent/expired ID returns None
    logging.debug(f"Getting status for discovery session {discovery_id}")
    session = get_discovery_session(discovery_id) // Checks expiry
    RETURN session

END FUNCTION