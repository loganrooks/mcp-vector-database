# PhiloGraph Tier 0 - Pseudocode: MCP Server

## Overview

This module defines the PhiloGraph MCP (Model Context Protocol) Server. It runs locally (likely as part of the Backend Service container or a separate process) and exposes PhiloGraph's core functionalities as tools callable by AI agents (like RooCode) using the `use_mcp_tool` mechanism. It acts as a bridge between the MCP world and the PhiloGraph Backend API.

**Dependencies:**

*   HTTP Client library (e.g., `requests`)
*   MCP Server framework/library (specifics depend on implementation, e.g., `@modelcontextprotocol/server-nodejs` or a Python equivalent)
*   Configuration:
    *   `{{BACKEND_API_URL}}`: Base URL for the PhiloGraph Backend API (e.g., `http://localhost:5000`).

```pseudocode
IMPORT mcp_server_framework // Library for creating MCP servers
IMPORT http_client // e.g., requests
IMPORT json
IMPORT logging

// --- Configuration ---
CONSTANT API_URL = get_config("{{BACKEND_API_URL}}", default="http://localhost:5000") // Get from env or config file
CONSTANT SERVER_NAME = "philograph-mcp-server" // Or as configured

// --- MCP Server Setup ---
mcp_server = mcp_server_framework.initialize_server(SERVER_NAME)

// --- Helper: API Interaction ---
FUNCTION call_backend_api(method, endpoint, json_data=NULL):
    // TDD: Test successful POST request to backend API
    // TDD: Test successful GET request to backend API
    // TDD: Test handling of connection errors to backend API
    // TDD: Test handling of non-2xx responses from backend API
    // TDD: Test handling of JSON decoding errors from backend API response
    url = API_URL + endpoint
    TRY:
        response = http_client.request(method, url, json=json_data, timeout=60) // Longer timeout for potential long ops
        response.raise_for_status()
        TRY:
            RETURN response.json()
        CATCH JSONDecodeError:
            logging.error(f"MCP Server: Failed to decode JSON response from Backend API {url}. Response: {response.text}")
            RAISE MCPToolError("Invalid response format from backend service.") // Use appropriate MCP error
    CATCH http_client.exceptions.ConnectionError as e:
        logging.error(f"MCP Server: Connection error calling Backend API {url}: {e}")
        RAISE MCPToolError(f"Cannot connect to PhiloGraph backend at {API_URL}.")
    CATCH http_client.exceptions.HTTPError as e:
        logging.error(f"MCP Server: HTTP error calling Backend API {url}: {e.response.status_code} - {e.response.text}")
        error_detail = e.response.json().get('error', e.response.text) if e.response.content else str(e)
        RAISE MCPToolError(f"Backend service error ({e.response.status_code}): {error_detail}")
    CATCH Exception as e:
        logging.exception(f"MCP Server: Unexpected error calling Backend API {url}", exc_info=e)
        RAISE MCPToolError(f"An unexpected error occurred while contacting the backend: {e}")
END FUNCTION

// --- Tool Definition: philograph_ingest ---
@mcp_server.tool(
    name="philograph_ingest",
    description="Ingest a document or directory into the PhiloGraph knowledge base.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file or directory relative to the configured source directory ({{SOURCE_FILE_DIR}})."
            }
        },
        "required": ["path"]
    }
)
FUNCTION handle_ingest_tool(arguments):
    // TDD: Test successful ingestion call returns backend success message
    // TDD: Test call with missing 'path' argument raises MCPValidationError
    // TDD: Test handling of errors returned from backend API during ingestion
    logging.info(f"MCP Tool: Received 'philograph_ingest' call with args: {arguments}")
    path = arguments.get("path")
    IF not path:
        // Framework should ideally handle schema validation, but double-check
        RAISE MCPValidationError("Missing required argument: path")

    // Call the backend API's /ingest endpoint
    response_data = call_backend_api("POST", "/ingest", json_data={"path": path})

    // Return the result from the backend API directly
    // TDD: Test that the exact response from the backend is returned
    RETURN response_data
END FUNCTION

// --- Tool Definition: philograph_search ---
@mcp_server.tool(
    name="philograph_search",
    description="Search for relevant text chunks within the PhiloGraph knowledge base.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The natural language search query."
            },
            "filters": {
                "type": "object",
                "description": "Optional metadata filters (e.g., {'author': 'Kant', 'year': 1781}).",
                "additionalProperties": True // Allow arbitrary key-value pairs for filters
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return.",
                "default": 10
            }
        },
        "required": ["query"]
    }
)
FUNCTION handle_search_tool(arguments):
    // TDD: Test successful search call returns formatted results from backend
    // TDD: Test search call with filters passes filters correctly to backend
    // TDD: Test call with missing 'query' argument raises MCPValidationError
    // TDD: Test handling of errors returned from backend API during search
    logging.info(f"MCP Tool: Received 'philograph_search' call with args: {arguments}")
    query = arguments.get("query")
    filters = arguments.get("filters", None)
    limit = arguments.get("limit", 10)

    IF not query:
        RAISE MCPValidationError("Missing required argument: query")

    payload = {"query": query, "limit": limit}
    IF filters:
        payload["filters"] = filters

    // Call the backend API's /search endpoint
    response_data = call_backend_api("POST", "/search", json_data=payload)

    // Return the results list from the backend API response
    // TDD: Test that only the 'results' part of the backend response is returned
    RETURN response_data.get("results", [])
END FUNCTION

// --- Tool Definition: philograph_acquire_missing ---
@mcp_server.tool(
    name="philograph_acquire_missing",
    description="Attempt to identify, acquire via zlibrary-mcp, and ingest missing texts based on citation frequency or specific details.",
    input_schema={
        "type": "object",
        "properties": {
            "threshold": {
                "type": "integer",
                "description": "Minimum citation count to trigger automatic search (if text_details not provided).",
                "default": 5
            },
            "text_details": {
                "type": "object",
                "description": "Specific details of the text to acquire (e.g., {'title': '...', 'author': '...'}). If provided, threshold is ignored.",
                "additionalProperties": True
            },
            "acquisition_id": {
                "type": "string",
                "description": "ID of an ongoing acquisition process (used for confirmation)."
            },
            "selected_book_details": {
                "type": "object",
                "description": "The full book details object selected by the user/agent for download (used for confirmation)."
            }
        },
        // No single required field, logic depends on combination
    }
)
FUNCTION handle_acquire_tool(arguments):
    // TDD: Test initial call with threshold triggers backend /acquire (find & search)
    // TDD: Test initial call with text_details triggers backend /acquire (direct search)
    // TDD: Test confirmation call with acquisition_id and selected_book_details triggers backend /acquire/confirm
    // TDD: Test handling of 'needs_confirmation' response from backend
    // TDD: Test handling of processing/completion/error responses from backend
    // TDD: Test call with invalid argument combination raises MCPValidationError

    logging.info(f"MCP Tool: Received 'philograph_acquire_missing' call with args: {arguments}")

    acquisition_id = arguments.get("acquisition_id")
    selected_book_details = arguments.get("selected_book_details")
    text_details = arguments.get("text_details")
    threshold = arguments.get("threshold", 5)

    IF acquisition_id AND selected_book_details:
        // This is a confirmation call
        logging.info(f"MCP Tool: Confirming acquisition {acquisition_id}")
        payload = {
            "acquisition_id": acquisition_id,
            "selected_book_details": selected_book_details
        }
        response_data = call_backend_api("POST", "/acquire/confirm", json_data=payload)
        // Return backend response (e.g., {"message": "...", "status_url": "..."})
        RETURN response_data

    ELSE IF text_details:
        // This is an initial call to acquire a specific text
        logging.info(f"MCP Tool: Starting acquisition search for specific details: {text_details}")
        payload = {"text_details": text_details}
        response_data = call_backend_api("POST", "/acquire", json_data=payload)
        // Return backend response (likely needs_confirmation with options)
        RETURN response_data

    ELSE:
        // This is an initial call to find missing texts based on threshold
        logging.info(f"MCP Tool: Starting acquisition search for missing texts (threshold: {threshold})")
        payload = {"find_missing_threshold": threshold} # Assuming API supports this
        response_data = call_backend_api("POST", "/acquire", json_data=payload)
        // Return backend response (likely needs_confirmation with options, or error if none found)
        RETURN response_data

    // Note: The agent calling this tool needs to handle the multi-step confirmation workflow
    // based on the responses received (e.g., if 'status' is 'needs_confirmation').

END FUNCTION


// --- Main Execution ---
IF __name__ == "__main__":
    // Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - MCP Server - %(levelname)s - %(message)s')
    // Start the MCP server (blocking call)
    logging.info(f"Starting PhiloGraph MCP Server '{SERVER_NAME}'...")
    mcp_server.start()
    logging.info("PhiloGraph MCP Server stopped.")
END IF