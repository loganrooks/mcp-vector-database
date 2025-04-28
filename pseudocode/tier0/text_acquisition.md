# PhiloGraph Tier 0 - Pseudocode: Text Acquisition Service

## Overview

This module handles the workflow for acquiring missing texts identified by the system (e.g., through citation analysis). It interacts with the external `zlibrary-mcp` server via MCP calls to search for, download, and process texts, then triggers the PhiloGraph ingestion pipeline.

**Dependencies:**

*   `ingestion_pipeline.py` (to trigger ingestion)
*   `db_layer.py` (potentially to check for existing docs or store acquisition status)
*   MCP Interaction Library (simulated as `mcp_call_tool`)
*   Configuration:
    *   `ZLIBRARY_MCP_SERVER_NAME`: Name of the zlibrary-mcp server (e.g., "zlibrary-mcp").
*   State Management (e.g., in-memory dict for Tier 0, or DB table for persistence)

```pseudocode
IMPORT ingestion_pipeline
IMPORT db_layer // Optional, for status tracking or pre-checks
IMPORT mcp_interaction // Provides mcp_call_tool(server_name, tool_name, arguments)
IMPORT logging
IMPORT uuid // For generating acquisition IDs

// --- Configuration ---
CONSTANT ZLIB_SERVER = get_config("ZLIBRARY_MCP_SERVER_NAME", default="zlibrary-mcp")

// --- State Management (Simple In-Memory Example for Tier 0) ---
// WARNING: This state is lost on service restart. A persistent store (DB) is needed for robustness.
acquisition_requests = {} // { acquisition_id: { status: "searching/confirming/processing/error/complete", details: {...} } }

// --- Main Acquisition Functions ---

FUNCTION start_acquisition_search(text_details):
    // text_details: dict containing info like {"title": "...", "author": "..."}
    // TDD: Test successful search returns results and 'needs_confirmation' status
    // TDD: Test search with no results returns appropriate status/message
    // TDD: Test handling of errors during MCP call to 'search_books'

    logging.info(f"Starting acquisition search for: {text_details}")
    acquisition_id = str(uuid.uuid4())
    acquisition_requests[acquisition_id] = {"status": "searching", "details": text_details}

    TRY:
        search_args = {"query": f"{text_details.get('title', '')} {text_details.get('author', '')}".strip()}
        // TDD: Test construction of search query from text_details
        // TDD: Test MCP call simulation with correct server, tool, args
        mcp_response = mcp_interaction.mcp_call_tool(ZLIB_SERVER, "search_books", search_args)

        // Assuming mcp_response contains a list of bookDetails objects if successful
        IF mcp_response AND isinstance(mcp_response, list) AND len(mcp_response) > 0:
            logging.info(f"Found {len(mcp_response)} potential matches for acquisition {acquisition_id}.")
            acquisition_requests[acquisition_id]['status'] = 'confirming'
            acquisition_requests[acquisition_id]['search_results'] = mcp_response
            RETURN {
                "status": "needs_confirmation",
                "search_results": mcp_response,
                "acquisition_id": acquisition_id
            }
        ELSE:
            logging.warning(f"No matches found for acquisition {acquisition_id}.")
            acquisition_requests[acquisition_id]['status'] = 'error'
            acquisition_requests[acquisition_id]['error_message'] = 'No matches found'
            RETURN {"status": "error", "message": "No matches found"}

    CATCH Exception as e:
        logging.error(f"MCP search_books call failed for acquisition {acquisition_id}: {e}")
        acquisition_requests[acquisition_id]['status'] = 'error'
        acquisition_requests[acquisition_id]['error_message'] = f"MCP search failed: {e}"
        RETURN {"status": "error", "message": f"MCP search failed: {e}"}

END FUNCTION

FUNCTION confirm_and_trigger_download(acquisition_id, selected_book_details):
    // TDD: Test successful confirmation triggers download and returns 'processing' status
    // TDD: Test confirmation for non-existent acquisition_id returns 'not_found'
    // TDD: Test confirmation for acquisition not in 'confirming' state returns error
    // TDD: Test handling of errors during MCP call to 'download_book_to_file'

    IF acquisition_id not in acquisition_requests:
        logging.warning(f"Attempted to confirm non-existent acquisition: {acquisition_id}")
        RETURN {"status": "not_found"}

    request_state = acquisition_requests[acquisition_id]
    IF request_state['status'] != 'confirming':
        logging.warning(f"Attempted to confirm acquisition {acquisition_id} in invalid state: {request_state['status']}")
        RETURN {"status": "error", "message": f"Invalid state for confirmation: {request_state['status']}"}

    logging.info(f"Confirming download for acquisition {acquisition_id}, book: {selected_book_details.get('title')}")
    request_state['status'] = 'processing'
    request_state['selected_book'] = selected_book_details

    TRY:
        download_args = {
            "bookDetails": selected_book_details,
            "process_for_rag": True
            // Optionally add "outputDir" if configurable paths are implemented in zlibrary-mcp
        }
        // TDD: Test MCP call simulation for download with correct args
        mcp_response = mcp_interaction.mcp_call_tool(ZLIB_SERVER, "download_book_to_file", download_args)

        // Assuming mcp_response = { success: bool, processed_path: str | None, error: str | None }
        IF mcp_response AND mcp_response.get('success') == True AND mcp_response.get('processed_path'):
            processed_file_path = mcp_response['processed_path']
            logging.info(f"Acquisition {acquisition_id}: Download and RAG processing successful. Processed file at: {processed_file_path}")
            request_state['processed_path'] = processed_file_path

            // Trigger PhiloGraph ingestion pipeline
            // TDD: Test that ingestion_pipeline.process_document is called with the correct path
            // Note: This assumes process_document can handle absolute paths or paths relative to a known base
            // Consider making process_document handle this path appropriately.
            // This could be synchronous or asynchronous depending on API design
            ingestion_result = ingestion_pipeline.process_document(processed_file_path) // Might need adjustment based on path handling

            IF ingestion_result['status'] == 'Success':
                logging.info(f"Acquisition {acquisition_id}: Ingestion successful.")
                request_state['status'] = 'complete'
                request_state['philo_doc_id'] = ingestion_result['document_id']
            ELSE:
                logging.error(f"Acquisition {acquisition_id}: Ingestion failed after download. Reason: {ingestion_result.get('message')}")
                request_state['status'] = 'error'
                request_state['error_message'] = f"Ingestion failed: {ingestion_result.get('message')}"
                // Return error status to API handler
                RETURN {"status": "error", "message": f"Ingestion failed after download: {ingestion_result.get('message')}"}

            RETURN {"status": "processing", "message": "Download successful, ingestion triggered."} // API might return ACCEPTED earlier

        ELSE:
            error_msg = mcp_response.get('error', 'Unknown download/processing error') if mcp_response else 'No response from MCP server'
            logging.error(f"Acquisition {acquisition_id}: MCP download_book_to_file failed. Reason: {error_msg}")
            request_state['status'] = 'error'
            request_state['error_message'] = f"MCP download/process failed: {error_msg}"
            RETURN {"status": "error", "message": f"MCP download/process failed: {error_msg}"}

    CATCH Exception as e:
        logging.error(f"MCP download_book_to_file call failed for acquisition {acquisition_id}: {e}")
        request_state['status'] = 'error'
        request_state['error_message'] = f"MCP download call failed: {e}"
        RETURN {"status": "error", "message": f"MCP download call failed: {e}"}

END FUNCTION

FUNCTION get_status(acquisition_id):
    // TDD: Test retrieving status for various states (searching, confirming, processing, complete, error)
    // TDD: Test retrieving status for non-existent ID returns None
    logging.debug(f"Getting status for acquisition {acquisition_id}")
    RETURN acquisition_requests.get(acquisition_id, None)
END FUNCTION

// --- Optional: Function to identify missing texts ---
FUNCTION find_missing_texts_from_citations(threshold=5):
    // TDD: Test identifying frequently cited but missing documents
    // TDD: Test threshold parameter limits results
    // This requires DB queries to aggregate citation data and check against existing documents
    logging.info(f"Finding missing texts cited more than {threshold} times...")
    db_conn = db_layer.get_db_connection()
    missing_texts_details = []
    TRY:
        // 1. Query `references` table, aggregate counts based on `cited_doc_details_jsonb`
        //    (Requires consistent structure in cited_doc_details_jsonb)
        // cited_counts = db_layer.get_citation_counts(db_conn) // Hypothetical function

        // 2. For highly cited items, check if a corresponding document exists in `documents` table
        //    (Matching logic based on title/author from cited_doc_details_jsonb)
        // FOR cited_detail, count in cited_counts.items():
        //     IF count >= threshold:
        //         IF NOT db_layer.check_document_exists_by_details(db_conn, cited_detail): // Hypothetical
        //             missing_texts_details.append(cited_detail)

        // Placeholder implementation
        logging.warning("find_missing_texts_from_citations DB logic not fully implemented in pseudocode.")

    CATCH Exception as e:
        logging.error(f"Error finding missing texts: {e}")
    FINALLY:
        db_layer.close_db_connection(db_conn)

    logging.info(f"Found {len(missing_texts_details)} potential missing texts.")
    RETURN missing_texts_details // List of dicts like {"title": "...", "author": "..."}
END FUNCTION