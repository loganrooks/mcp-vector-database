# PhiloGraph Tier 0 - Pseudocode: Backend API (Flask/FastAPI)

## Overview

This module defines the RESTful API endpoints for the PhiloGraph backend service. It acts as the primary interface for the CLI and MCP Server, orchestrating calls to underlying services like the Ingestion Pipeline, Search Module, Text Acquisition Service, and Database Layer.

**Framework:** Python (Flask or FastAPI - specific choice deferred to implementation). Pseudocode aims for framework neutrality where possible.

**Dependencies:**

*   Database Interaction Layer (`db_layer.py`)
*   Ingestion Pipeline (`ingestion_pipeline.py`)
*   Search Module (`search_module.py`)
*   Text Acquisition Service (`text_acquisition.py`)
*   Configuration (DB connection details, etc.)

```pseudocode
IMPORT db_layer
IMPORT ingestion_pipeline
IMPORT search_module
IMPORT text_acquisition
IMPORT http_status_codes
IMPORT request_handler // Framework-specific request parsing/response building
IMPORT logging

// --- API Application Setup ---
// Initialize Flask/FastAPI app instance
app = initialize_web_framework()

// --- Error Handling ---
// Define global error handlers (e.g., for 404 Not Found, 500 Internal Server Error)
// TDD: Test generic 500 error handler returns appropriate JSON response
// TDD: Test 404 error handler returns appropriate JSON response
FUNCTION handle_generic_error(error):
    logging.exception("Unhandled exception occurred", exc_info=error)
    RETURN create_json_response({"error": "Internal Server Error"}, http_status_codes.INTERNAL_SERVER_ERROR)
END FUNCTION

FUNCTION handle_not_found_error(error):
    RETURN create_json_response({"error": "Resource not found"}, http_status_codes.NOT_FOUND)
END FUNCTION

// Register error handlers with the app

// --- Endpoints ---

// === Ingestion ===
@app.route("/ingest", methods=["POST"])
FUNCTION handle_ingest_request():
    // TDD: Test successful ingestion request for a single file path
    // TDD: Test successful ingestion request for a directory path
    // TDD: Test request with missing 'path' parameter returns 400
    // TDD: Test request with invalid path returns appropriate error (e.g., 404 if path checked here, or relies on pipeline error)
    // TDD: Test response when ingestion pipeline returns success
    // TDD: Test response when ingestion pipeline returns error
    // TDD: Test response when ingestion pipeline returns skipped

    request_data = get_request_json()
    IF 'path' not in request_data:
        RETURN create_json_response({"error": "Missing 'path' parameter"}, http_status_codes.BAD_REQUEST)

    relative_path = request_data['path']

    // Option 1: Synchronous call (simple for Tier 0, but long requests block)
    // result = ingestion_pipeline.process_document(relative_path)

    // Option 2: Asynchronous call (better for long tasks, requires background worker setup - Celery, RQ, etc.)
    // task = trigger_background_ingestion_task(relative_path)
    // RETURN create_json_response({"message": "Ingestion started", "task_id": task.id}, http_status_codes.ACCEPTED)

    // Assuming synchronous for Tier 0 pseudocode simplicity:
    TRY:
        result = ingestion_pipeline.process_document(relative_path)
        IF result['status'] == "Success":
            RETURN create_json_response({"message": "Ingestion successful", "document_id": result['document_id']}, http_status_codes.CREATED)
        ELSE IF result['status'] == "Skipped":
            RETURN create_json_response({"message": result['message']}, http_status_codes.OK)
        ELSE: // Error
            RETURN create_json_response({"error": f"Ingestion failed: {result['message']}"}, http_status_codes.INTERNAL_SERVER_ERROR)
    CATCH Exception as e:
        logging.exception(f"Unexpected error during ingestion call for {relative_path}", exc_info=e)
        RETURN handle_generic_error(e)

END FUNCTION

// === Search ===
@app.route("/search", methods=["POST"])
FUNCTION handle_search_request():
    // TDD: Test successful search with query only
    // TDD: Test successful search with query and filters (author, year)
    // TDD: Test request with missing 'query' parameter returns 400
    // TDD: Test request with invalid filter format returns 400
    // TDD: Test handling of errors from search_module (e.g., embedding failure)
    // TDD: Test pagination parameters (limit, offset) if implemented

    request_data = get_request_json()
    IF 'query' not in request_data:
        RETURN create_json_response({"error": "Missing 'query' parameter"}, http_status_codes.BAD_REQUEST)

    query_text = request_data['query']
    filters = request_data.get('filters', NULL) // e.g., {"author": "Kant", "year": 1781}
    top_k = request_data.get('limit', 10) // Default limit

    // Validate filters if necessary
    // TDD: Add validation tests for filter structure/values

    TRY:
        search_results = search_module.perform_search(query_text, top_k, filters)
        // TDD: Test that search_results are formatted correctly in the response
        RETURN create_json_response({"results": search_results}, http_status_codes.OK)
    CATCH ValueError as ve: // e.g., embedding dimension mismatch
        logging.error(f"Search value error: {ve}")
        RETURN create_json_response({"error": f"Search parameter error: {ve}"}, http_status_codes.BAD_REQUEST)
    CATCH Exception as e:
        logging.exception(f"Unexpected error during search for query: {query_text}", exc_info=e)
        RETURN handle_generic_error(e)

END FUNCTION

// === Document Retrieval ===
@app.route("/documents/<doc_id>", methods=["GET"])
FUNCTION get_document(doc_id):
    // TDD: Test retrieving an existing document by ID
    // TDD: Test retrieving a non-existent document returns 404
    // TDD: Test handling of invalid ID format returns 400/404
    db_conn = db_layer.get_db_connection()
    TRY:
        document = db_layer.get_document_by_id(db_conn, doc_id)
        IF document:
            RETURN create_json_response(document, http_status_codes.OK)
        ELSE:
            RETURN handle_not_found_error(None) // Or specific 404 response
    CATCH Exception as e:
        logging.exception(f"Error retrieving document {doc_id}", exc_info=e)
        RETURN handle_generic_error(e)
    FINALLY:
        db_layer.close_db_connection(db_conn)
END FUNCTION

// === Chunk Retrieval ===
@app.route("/chunks/<chunk_id>", methods=["GET"])
FUNCTION get_chunk(chunk_id):
    // TDD: Test retrieving an existing chunk by ID
    // TDD: Test retrieving a non-existent chunk returns 404
    // Potentially less useful endpoint, maybe retrieve chunks by document/section?
    // Placeholder - implement if needed, requires db_layer function
    RETURN create_json_response({"message": "Not implemented"}, http_status_codes.NOT_IMPLEMENTED)
END FUNCTION

// === Collection Management ===
@app.route("/collections", methods=["POST"])
FUNCTION create_collection():
    // TDD: Test creating a new collection with a valid name
    // TDD: Test request with missing 'name' returns 400
    request_data = get_request_json()
    IF 'name' not in request_data:
        RETURN create_json_response({"error": "Missing 'name' parameter"}, http_status_codes.BAD_REQUEST)
    collection_name = request_data['name']

    db_conn = db_layer.get_db_connection()
    TRY:
        collection_id = db_layer.add_collection(db_conn, collection_name)
        RETURN create_json_response({"message": "Collection created", "collection_id": collection_id}, http_status_codes.CREATED)
    CATCH Exception as e:
        logging.exception(f"Error creating collection '{collection_name}'", exc_info=e)
        RETURN handle_generic_error(e)
    FINALLY:
        db_layer.close_db_connection(db_conn)
END FUNCTION

@app.route("/collections/<collection_id>/items", methods=["POST"])
FUNCTION add_collection_item(collection_id):
    // TDD: Test adding a valid document item to a collection
    // TDD: Test adding a valid chunk item to a collection
    // TDD: Test request with missing 'item_type' or 'item_id' returns 400
    // TDD: Test request with invalid 'item_type' returns 400
    // TDD: Test adding item to non-existent collection returns 404
    request_data = get_request_json()
    item_type = request_data.get('item_type')
    item_id = request_data.get('item_id')

    IF not item_type or not item_id:
        RETURN create_json_response({"error": "Missing 'item_type' or 'item_id'"}, http_status_codes.BAD_REQUEST)
    IF item_type not in ['document', 'chunk']: // Define allowed types
        RETURN create_json_response({"error": "Invalid 'item_type'"}, http_status_codes.BAD_REQUEST)

    db_conn = db_layer.get_db_connection()
    TRY:
        // Optional: Check if collection_id exists first
        db_layer.add_item_to_collection(db_conn, collection_id, item_type, item_id)
        RETURN create_json_response({"message": f"{item_type} added to collection"}, http_status_codes.OK)
    CATCH ForeignKeyViolationError: // Or specific error for non-existent collection
        RETURN create_json_response({"error": "Collection not found"}, http_status_codes.NOT_FOUND)
    CATCH Exception as e:
        logging.exception(f"Error adding item to collection {collection_id}", exc_info=e)
        RETURN handle_generic_error(e)
    FINALLY:
        db_layer.close_db_connection(db_conn)
END FUNCTION

@app.route("/collections/<collection_id>", methods=["GET"])
FUNCTION get_collection(collection_id):
    // TDD: Test retrieving items for an existing collection
    // TDD: Test retrieving items for a non-existent collection returns 404
    db_conn = db_layer.get_db_connection()
    TRY:
        // Optional: Check if collection exists first
        items = db_layer.get_collection_items(db_conn, collection_id)
        RETURN create_json_response({"collection_id": collection_id, "items": items}, http_status_codes.OK)
    CATCH Exception as e:
        logging.exception(f"Error retrieving collection {collection_id}", exc_info=e)
        RETURN handle_generic_error(e)
    FINALLY:
        db_layer.close_db_connection(db_conn)
END FUNCTION

// === Text Acquisition (New Workflow - ADR 009) ===

@app.route("/acquire/discover", methods=["POST"])
FUNCTION handle_discover_request():
    // TDD: Test successful discovery with threshold filter
    // TDD: Test successful discovery with author filter
    // TDD: Test successful discovery with tag filter
    // TDD: Test discovery with multiple filters
    // TDD: Test discovery with no filters (returns error or default behavior?)
    // TDD: Test discovery resulting in no candidates found
    // TDD: Test handling of errors from acquisition_service.handle_discovery_request
    // TDD: Test response structure includes 'candidates' list and 'discovery_id'

    request_data = get_request_json()
    filters = request_data.get('filters', {}) // e.g., {"threshold": 5, "author": "Kant", "tags": ["ethics"]}

    IF not filters:
        RETURN create_json_response({"error": "Missing discovery filters"}, http_status_codes.BAD_REQUEST)

    TRY:
        // Call the new acquisition service function
        result = acquisition_service.handle_discovery_request(filters)

        IF result['status'] == 'success':
            RETURN create_json_response({
                "discovery_id": result['discovery_id'],
                "candidates": result['candidates'] // List of bookDetails-like objects
            }, http_status_codes.OK)
        ELSE IF result['status'] == 'no_candidates':
             RETURN create_json_response({
                "discovery_id": result['discovery_id'],
                "candidates": []
            }, http_status_codes.OK) // Still OK, just no results
        ELSE: // Error case
            RETURN create_json_response({"error": result['message']}, http_status_codes.INTERNAL_SERVER_ERROR)

    CATCH Exception as e:
        logging.exception("Error during acquisition discovery", exc_info=e)
        RETURN handle_generic_error(e)
END FUNCTION

@app.route("/acquire/confirm/<discovery_id>", methods=["POST"])
FUNCTION handle_confirm_request(discovery_id):
    // TDD: Test successful confirmation with valid discovery_id and selected items
    // TDD: Test confirmation with non-existent discovery_id returns 404
    // TDD: Test confirmation with discovery_id in invalid state returns 400/409
    // TDD: Test confirmation with empty selected items list
    // TDD: Test confirmation with invalid selected item IDs/details returns 400
    // TDD: Test response indicating processing started (ACCEPTED)
    // TDD: Test handling of errors from acquisition_service.handle_confirmation_request

    request_data = get_request_json()
    selected_items = request_data.get('selected_items', []) // List of candidate IDs or full details

    IF not selected_items:
        RETURN create_json_response({"error": "Missing 'selected_items'"}, http_status_codes.BAD_REQUEST)
    IF not discovery_id:
         RETURN create_json_response({"error": "Missing 'discovery_id' in path"}, http_status_codes.BAD_REQUEST) // Should be caught by routing

    TRY:
        // Call the new acquisition service function
        result = acquisition_service.handle_confirmation_request(discovery_id, selected_items)

        IF result['status'] == 'processing_started':
            RETURN create_json_response({
                "message": "Acquisition confirmed. Download and processing initiated.",
                "status_url": f"/acquire/status/{discovery_id}" // Optional status endpoint using discovery_id
            }, http_status_codes.ACCEPTED)
        ELSE IF result['status'] == 'not_found':
            RETURN create_json_response({"error": "Discovery session not found or expired"}, http_status_codes.NOT_FOUND)
        ELSE IF result['status'] == 'invalid_state':
            RETURN create_json_response({"error": "Discovery session is not awaiting confirmation"}, http_status_codes.CONFLICT) # 409 Conflict
        ELSE IF result['status'] == 'invalid_selection':
             RETURN create_json_response({"error": f"Invalid items selected: {result.get('details', '')}"}, http_status_codes.BAD_REQUEST)
        ELSE: // Error case
            RETURN create_json_response({"error": result['message']}, http_status_codes.INTERNAL_SERVER_ERROR)

    CATCH Exception as e:
        logging.exception(f"Error confirming acquisition for discovery {discovery_id}", exc_info=e)
        RETURN handle_generic_error(e)
END FUNCTION

// Optional: Status endpoint for async acquisition/ingestion using discovery_id
@app.route("/acquire/status/<discovery_id>", methods=["GET"])
FUNCTION get_acquisition_status(discovery_id):
    // TDD: Test retrieving status for ongoing acquisition (processing)
    // TDD: Test retrieving status for completed acquisition (all items processed/failed)
    // TDD: Test retrieving status for failed acquisition (major error)
    // TDD: Test retrieving status for invalid discovery_id returns 404
    // Requires acquisition_service to track status by discovery_id
    status_info = acquisition_service.get_status(discovery_id)
    IF status_info:
        RETURN create_json_response(status_info, http_status_codes.OK)
    ELSE:
        RETURN handle_not_found_error(None)
END FUNCTION


// === DEPRECATED Text Acquisition (Old Workflow) ===
// @app.route("/acquire", methods=["POST"])
// FUNCTION handle_acquire_request_DEPRECATED():
//     // ... (previous implementation) ...
// END FUNCTION
//
// @app.route("/acquire/confirm", methods=["POST"])
// FUNCTION handle_acquire_confirm_DEPRECATED():
//     // ... (previous implementation) ...
// END FUNCTION


// --- Utility ---
FUNCTION create_json_response(data, status_code):
    // Framework-specific implementation to create a JSON response
    RETURN framework_json_response(data, status_code)
END FUNCTION

FUNCTION get_request_json():
    // Framework-specific implementation to parse JSON from request body
    RETURN framework_parse_json()
END FUNCTION

// --- Main Execution ---
IF __name__ == "__main__":
    // Load configuration, setup logging
    // Run the Flask/FastAPI development server
    run_app(app, host="0.0.0.0", port=5000) // Example port
END IF