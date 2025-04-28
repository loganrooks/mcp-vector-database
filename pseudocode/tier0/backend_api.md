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

// === Text Acquisition ===
@app.route("/acquire", methods=["POST"])
FUNCTION handle_acquire_request():
    // TDD: Test triggering acquisition with valid text details
    // TDD: Test request missing required details returns 400
    // TDD: Test response when acquisition service returns search results for confirmation
    // TDD: Test handling errors from the text_acquisition service
    request_data = get_request_json()
    text_details = request_data.get('text_details') // e.g., {"title": "...", "author": "..."}

    IF not text_details:
        RETURN create_json_response({"error": "Missing 'text_details'"}, http_status_codes.BAD_REQUEST)

    TRY:
        // This might involve multiple steps (search, confirm, download)
        // The acquisition service should handle the state machine
        // Initial call might just start the search
        result = text_acquisition.start_acquisition_search(text_details)

        IF result['status'] == 'needs_confirmation':
            // TDD: Test response format for confirmation step
            RETURN create_json_response({
                "message": "Select book for acquisition",
                "options": result['search_results'],
                "acquisition_id": result['acquisition_id'] // ID to track this process
            }, http_status_codes.OK)
        ELSE IF result['status'] == 'error':
            RETURN create_json_response({"error": result['message']}, http_status_codes.INTERNAL_SERVER_ERROR)
        ELSE: // Should not happen if service logic is correct
            RETURN handle_generic_error(Exception("Unexpected acquisition status"))

    CATCH Exception as e:
        logging.exception("Error starting text acquisition", exc_info=e)
        RETURN handle_generic_error(e)
END FUNCTION

@app.route("/acquire/confirm", methods=["POST"])
FUNCTION handle_acquire_confirm():
    // TDD: Test confirming download with valid acquisition_id and bookDetails
    // TDD: Test confirming with invalid acquisition_id returns 404
    // TDD: Test response indicating download/processing started
    // TDD: Test handling errors from text_acquisition service during confirmation/download trigger
    request_data = get_request_json()
    acquisition_id = request_data.get('acquisition_id')
    selected_book_details = request_data.get('selected_book_details')

    IF not acquisition_id or not selected_book_details:
        RETURN create_json_response({"error": "Missing 'acquisition_id' or 'selected_book_details'"}, http_status_codes.BAD_REQUEST)

    TRY:
        // Trigger the download and processing via the acquisition service
        result = text_acquisition.confirm_and_trigger_download(acquisition_id, selected_book_details)

        IF result['status'] == 'processing':
            RETURN create_json_response({
                "message": "Download and processing initiated. Ingestion will follow.",
                "status_url": f"/acquire/status/{acquisition_id}" // Optional status endpoint
            }, http_status_codes.ACCEPTED)
        ELSE IF result['status'] == 'error':
            RETURN create_json_response({"error": result['message']}, http_status_codes.INTERNAL_SERVER_ERROR)
        ELSE IF result['status'] == 'not_found':
            RETURN create_json_response({"error": "Acquisition ID not found or invalid state"}, http_status_codes.NOT_FOUND)
        ELSE:
            RETURN handle_generic_error(Exception("Unexpected acquisition confirmation status"))

    CATCH Exception as e:
        logging.exception("Error confirming text acquisition", exc_info=e)
        RETURN handle_generic_error(e)
END FUNCTION

// Optional: Status endpoint for async acquisition/ingestion
@app.route("/acquire/status/<acquisition_id>", methods=["GET"])
FUNCTION get_acquisition_status(acquisition_id):
    // TDD: Test retrieving status for ongoing acquisition
    // TDD: Test retrieving status for completed acquisition
    // TDD: Test retrieving status for failed acquisition
    // TDD: Test retrieving status for invalid acquisition_id returns 404
    // Requires text_acquisition service to track status
    status_info = text_acquisition.get_status(acquisition_id)
    IF status_info:
        RETURN create_json_response(status_info, http_status_codes.OK)
    ELSE:
        RETURN handle_not_found_error(None)
END FUNCTION


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