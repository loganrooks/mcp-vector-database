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

// --- Tool Definition: philograph_acquire ---
// Renamed from philograph_acquire_missing to reflect broader scope (discovery + confirmation)
@mcp_server.tool(
    name="philograph_acquire",
    description="Discover potential missing texts based on filters, or confirm acquisition for a previous discovery session.",
    input_schema={
        "type": "object",
        "properties": {
            "filters": {
                "type": "object",
                "description": "Filters for discovering missing texts (e.g., {'threshold': 5, 'author': 'Kant', 'tags': ['ethics']}). Used for discovery phase.",
                "additionalProperties": True
            },
            "discovery_id": {
                "type": "string",
                "description": "ID of a previous discovery session. Required for confirmation phase."
            },
            "selected_items": {
                "type": "array",
                "description": "List of candidate IDs or full book details objects selected for acquisition. Required for confirmation phase.",
                "items": {
                    "oneOf": [
                        {"type": "string", "description": "Candidate ID"},
                        {"type": "object", "description": "Full book details object"}
                    ]
                }
            }
        },
        // Logic requires either 'filters' (for discovery) OR ('discovery_id' AND 'selected_items') (for confirmation)
        // This complex validation might need to be handled within the tool function if not supported by schema directly.
    }
)
FUNCTION handle_acquire_tool(arguments):
    // TDD: Test discovery call with 'filters' triggers backend /acquire/discover
    // TDD: Test discovery call returns candidates and discovery_id
    // TDD: Test confirmation call with 'discovery_id' and 'selected_items' triggers backend /acquire/confirm/{discovery_id}
    // TDD: Test confirmation call returns processing status
    // TDD: Test handling of backend errors for both discovery and confirmation
    // TDD: Test call with invalid argument combination (e.g., filters + discovery_id) raises MCPValidationError
    // TDD: Test call missing required args for either phase raises MCPValidationError

    logging.info(f"MCP Tool: Received 'philograph_acquire' call with args: {arguments}")

    discovery_id = arguments.get("discovery_id")
    selected_items = arguments.get("selected_items")
    filters = arguments.get("filters")

    // --- Input Validation ---
    is_discovery = filters is not None
    is_confirmation = discovery_id is not None and selected_items is not None

    IF is_discovery AND is_confirmation:
        RAISE MCPValidationError("Cannot provide both 'filters' and ('discovery_id', 'selected_items'). Use 'filters' for discovery or ('discovery_id', 'selected_items') for confirmation.")
    IF NOT is_discovery AND NOT is_confirmation:
        RAISE MCPValidationError("Must provide either 'filters' for discovery or ('discovery_id' AND 'selected_items') for confirmation.")
    IF is_confirmation AND not isinstance(selected_items, list):
         RAISE MCPValidationError("'selected_items' must be a list.")
    // Add more specific validation for filter contents if needed

    // --- API Call Logic ---
    IF is_confirmation:
        // Confirmation Phase
        logging.info(f"MCP Tool: Confirming acquisition for discovery session {discovery_id}")
        payload = {"selected_items": selected_items}
        endpoint = f"/acquire/confirm/{discovery_id}"
        response_data = call_backend_api("POST", endpoint, json_data=payload)
        // Return backend response (e.g., {"message": "...", "status_url": "..."})
        RETURN response_data

    ELSE: // is_discovery
        // Discovery Phase
        logging.info(f"MCP Tool: Starting acquisition discovery with filters: {filters}")
        payload = {"filters": filters}
        endpoint = "/acquire/discover"
        response_data = call_backend_api("POST", endpoint, json_data=payload)
        // Return backend response (e.g., {"discovery_id": "...", "candidates": [...]})
        RETURN response_data

    // Note: The agent calling this tool needs to handle the multi-step workflow.
    // 1. Call with 'filters' -> Receive 'discovery_id' and 'candidates'.
    // 2. Agent reviews 'candidates'.
    // 3. Call with 'discovery_id' and 'selected_items' -> Receive confirmation/status.

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