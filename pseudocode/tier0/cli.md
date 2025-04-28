# PhiloGraph Tier 0 - Pseudocode: Command Line Interface (CLI)

## Overview

This module defines the command-line interface for interacting with the PhiloGraph backend. It uses a library like Typer or Click to parse commands and arguments, makes HTTP requests to the Backend API, and displays the results to the user.

**Dependencies:**

*   HTTP Client library (e.g., `requests`)
*   CLI framework library (e.g., `typer`, `click`)
*   Configuration:
    *   `{{BACKEND_API_URL}}`: Base URL for the Backend API (e.g., `http://localhost:5000`).

```pseudocode
IMPORT cli_framework // e.g., typer, click
IMPORT http_client // e.g., requests
IMPORT json
IMPORT logging
IMPORT sys // For exit codes

// --- Configuration ---
CONSTANT API_URL = get_config("{{BACKEND_API_URL}}", default="http://localhost:5000") // Get from env or config file

// --- CLI Application Setup ---
app = cli_framework.initialize_app()

// --- Helper Functions ---
FUNCTION make_api_request(method, endpoint, json_data=NULL, params=NULL):
    // TDD: Test successful GET request
    // TDD: Test successful POST request with JSON data
    // TDD: Test handling of API connection errors
    // TDD: Test handling of non-2xx HTTP status codes from API
    // TDD: Test handling of JSON decoding errors from API response
    url = API_URL + endpoint
    TRY:
        response = http_client.request(method, url, json=json_data, params=params, timeout=30) // Add timeout
        response.raise_for_status() // Raise exception for 4xx/5xx errors
        TRY:
            RETURN response.json()
        CATCH JSONDecodeError:
            logging.error(f"Failed to decode JSON response from {url}. Response text: {response.text}")
            print_error("Error: Invalid response format received from server.")
            sys.exit(1)
    CATCH http_client.exceptions.ConnectionError as e:
        logging.error(f"Connection error calling API endpoint {url}: {e}")
        print_error(f"Error: Could not connect to the PhiloGraph backend at {API_URL}.")
        sys.exit(1)
    CATCH http_client.exceptions.HTTPError as e:
        logging.error(f"HTTP error calling API endpoint {url}: {e.response.status_code} - {e.response.text}")
        error_detail = e.response.json().get('error', e.response.text) if e.response.content else str(e)
        print_error(f"Error from server ({e.response.status_code}): {error_detail}")
        sys.exit(1)
    CATCH Exception as e:
        logging.exception(f"Unexpected error calling API endpoint {url}", exc_info=e)
        print_error(f"An unexpected error occurred: {e}")
        sys.exit(1)
END FUNCTION

FUNCTION print_success(message):
    // Use framework's styling if available (e.g., color)
    cli_framework.print(f"Success: {message}")
END FUNCTION

FUNCTION print_error(message):
    // Use framework's styling if available (e.g., color)
    cli_framework.print(f"Error: {message}", error=True)
END FUNCTION

FUNCTION display_results(data):
    // Format and print JSON data nicely for the console
    // TDD: Test display of search results list
    // TDD: Test display of single document details
    // TDD: Test display of collection items
    // TDD: Test display of simple messages
    IF isinstance(data, dict) AND 'message' in data AND len(data) == 1:
         print_success(data['message']) // Handle simple status messages
    ELSE:
        // Use pretty printing for JSON or custom formatting
        cli_framework.print(json.dumps(data, indent=2))
END FUNCTION

// --- CLI Commands ---

@app.command()
FUNCTION ingest(path: STRING):
    // TDD: Test calling API /ingest endpoint with correct path
    // TDD: Test displaying success message from API
    // TDD: Test displaying error message from API
    """
    Ingest a document or directory into PhiloGraph.
    PATH: Path to the file or directory (relative to {{SOURCE_FILE_DIR}}).
    """
    logging.info(f"CLI: Initiating ingestion for path: {path}")
    response_data = make_api_request("POST", "/ingest", json_data={"path": path})
    display_results(response_data)
END FUNCTION

@app.command()
FUNCTION search(
    query: STRING,
    author: STRING = NULL,
    year: INTEGER = NULL,
    doc_id: STRING = NULL,
    limit: INTEGER = DEFAULT_TOP_K
):
    // TDD: Test calling API /search with query only
    // TDD: Test calling API /search with query and author filter
    // TDD: Test calling API /search with query and year filter
    // TDD: Test calling API /search with query and doc_id filter
    // TDD: Test calling API /search with limit parameter
    // TDD: Test displaying formatted search results
    """
    Search for text chunks in PhiloGraph.
    QUERY: The search query text.
    --author: Filter results by author.
    --year: Filter results by publication year.
    --doc-id: Filter results by source document ID.
    --limit: Maximum number of results to return.
    """
    logging.info(f"CLI: Searching for query: '{query}' with filters...")
    filters = {}
    IF author: filters['author'] = author
    IF year: filters['year'] = year
    IF doc_id: filters['doc_id'] = doc_id

    payload = {"query": query, "limit": limit}
    IF filters: payload['filters'] = filters

    response_data = make_api_request("POST", "/search", json_data=payload)
    display_results(response_data.get('results', [])) // Display the list of results
END FUNCTION

@app.command()
FUNCTION show(item_type: STRING, item_id: STRING):
    // TDD: Test showing a document calls /documents/<id>
    // TDD: Test showing an invalid item_type prints error
    // TDD: Test showing non-existent item_id displays API error
    """
    Show details for a specific item (e.g., document).
    ITEM_TYPE: Type of item (e.g., 'document').
    ITEM_ID: The ID of the item.
    """
    logging.info(f"CLI: Showing details for {item_type} {item_id}")
    IF item_type.lower() == 'document':
        endpoint = f"/documents/{item_id}"
        response_data = make_api_request("GET", endpoint)
        display_results(response_data)
    // Add other item types like 'chunk', 'section' if needed
    ELSE:
        print_error(f"Unsupported item type: {item_type}. Supported types: 'document'.")
        sys.exit(1)
END FUNCTION

@app.command(name="list") // Use specific name to avoid conflict with Python list
FUNCTION list_items(item_type: STRING, collection_id: STRING = NULL):
    // TDD: Test listing collections calls /collections
    // TDD: Test listing items in a specific collection calls /collections/<id>
    // TDD: Test listing unsupported item_type prints error
    """
    List items (e.g., collections, documents within a collection).
    ITEM_TYPE: Type of item to list (e.g., 'collections', 'collection-items').
    --collection-id: Required if item_type is 'collection-items'.
    """
    logging.info(f"CLI: Listing {item_type}...")
    IF item_type.lower() == 'collections':
        # Assuming a /collections GET endpoint exists in the API
        # response_data = make_api_request("GET", "/collections")
        # display_results(response_data)
        print_error("Listing all collections not yet implemented in API.") # Placeholder
    ELSE IF item_type.lower() == 'collection-items':
        IF not collection_id:
            print_error("--collection-id is required when listing 'collection-items'.")
            sys.exit(1)
        endpoint = f"/collections/{collection_id}"
        response_data = make_api_request("GET", endpoint)
        display_results(response_data.get('items', []))
    ELSE:
        print_error(f"Unsupported item type: {item_type}. Supported types: 'collections', 'collection-items'.")
        sys.exit(1)
END FUNCTION

@app.command()
FUNCTION add_to_collection(collection_id: STRING, item_type: STRING, item_id: STRING):
    // TDD: Test adding document to collection calls /collections/<id>/items
    // TDD: Test adding chunk to collection calls /collections/<id>/items
    // TDD: Test handling API errors (e.g., collection not found)
    """
    Add an item (document, chunk) to a collection.
    COLLECTION_ID: The ID of the collection.
    ITEM_TYPE: Type of item ('document' or 'chunk').
    ITEM_ID: The ID of the item to add.
    """
    logging.info(f"CLI: Adding {item_type} {item_id} to collection {collection_id}")
    endpoint = f"/collections/{collection_id}/items"
    payload = {"item_type": item_type, "item_id": item_id}
    response_data = make_api_request("POST", endpoint, json_data=payload)
    display_results(response_data)
END FUNCTION

@app.command()
FUNCTION acquire_missing_texts(threshold: INTEGER = 5):
    // TDD: Test calling API /acquire endpoint (initial search trigger)
    // TDD: Test handling API response requiring confirmation
    // TDD: Test prompting user for confirmation
    // TDD: Test calling API /acquire/confirm after user confirmation
    // TDD: Test handling API errors during acquisition process
    """
    Identify and attempt to acquire missing texts based on citation frequency.
    --threshold: Minimum citation count to trigger acquisition attempt.
    """
    logging.info(f"CLI: Starting process to acquire missing texts (threshold: {threshold})")

    # Step 1: Ask backend to identify missing texts and start search (simplified for pseudocode)
    # In a real scenario, might first call a dedicated endpoint like /acquire/find-missing
    # For now, assume /acquire handles the initial search trigger based on details (or lack thereof)
    print("Identifying potentially missing texts and searching sources...")
    # This might need refinement - how does the API know *which* texts to search for initially?
    # Option A: Backend has a function `find_missing_texts_from_citations` called by /acquire
    # Option B: CLI calls a separate endpoint first, then calls /acquire for specific items.
    # Assuming Option A for simplicity: /acquire without details triggers the find & search.
    initial_response = make_api_request("POST", "/acquire", json_data={"find_missing_threshold": threshold}) # Hypothetical payload

    IF initial_response.get('status') == 'needs_confirmation':
        acquisition_id = initial_response.get('acquisition_id')
        options = initial_response.get('options', [])
        IF not options or not acquisition_id:
            print_error("API returned confirmation status but no options or ID.")
            sys.exit(1)

        print("\nPlease select a book to acquire (enter number) or 0 to cancel:")
        FOR i, book in enumerate(options):
            # TDD: Test display formatting for book options
            print(f"  {i+1}. {book.get('title', 'N/A')} by {book.get('author', 'N/A')} ({book.get('year', 'N/A')}) - {book.get('extension', 'N/A')}")

        TRY:
            selection = int(input("> "))
            IF selection > 0 AND selection <= len(options):
                selected_book = options[selection - 1]
                print(f"Confirming acquisition for: {selected_book.get('title')}")
                # Step 2: Confirm selection with backend
                confirm_payload = {
                    "acquisition_id": acquisition_id,
                    "selected_book_details": selected_book
                }
                confirm_response = make_api_request("POST", "/acquire/confirm", json_data=confirm_payload)
                display_results(confirm_response)
            ELSE:
                print("Acquisition cancelled.")
        CATCH ValueError:
            print_error("Invalid input. Please enter a number.")
            sys.exit(1)

    ELSE: // Handle initial errors or unexpected status
        display_results(initial_response)

END FUNCTION


// --- Main Execution ---
IF __name__ == "__main__":
    // Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    // Run the CLI application
    app()
END IF