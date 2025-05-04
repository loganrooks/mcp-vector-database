import logging
import json
from typing import Any, Dict, Optional, List, Union # Added List, Union

import httpx # For potential errors from http_client

from .. import config
# Assuming http_client might be used, though direct calls might be sync here
from ..utils import http_client

logger = logging.getLogger(__name__)
logging.basicConfig(level=config.LOG_LEVEL, format='%(asctime)s - MCP Server - %(levelname)s - %(message)s')

# --- Placeholder/Simulation for MCP Server Framework ---
# In a real scenario, this would be provided by the MCP library.

class MCPValidationError(Exception):
    """Custom exception for MCP input validation errors."""
    pass

class MCPToolError(Exception):
    """Custom exception for general errors during MCP tool execution."""
    pass

class MockMCPToolDecorator:
    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        logger.info(f"[MCP SIM] Registering tool: {self.name}")

    def __call__(self, func):
        # In a real framework, this would register the function `func`
        # as the handler for the tool `self.name`.
        # We store it for potential simulation later if needed.
        setattr(MockMCPFramework, f"handler_{self.name}", func)
        logger.debug(f"[MCP SIM] Handler for '{self.name}' set to {func.__name__}")
        return func

class MockMCPFramework:
    # Simulate the decorator as a class method for structure
    @staticmethod
    def tool(name: str, description: str, input_schema: Dict[str, Any]):
        return MockMCPToolDecorator(name, description, input_schema)

    @staticmethod
    def initialize_server(server_name: str):
        logger.info(f"[MCP SIM] Initializing MCP Server '{server_name}'")
        # Return self or a server instance in a real framework
        return MockMCPFramework

    @staticmethod
    def start():
        logger.info("[MCP SIM] Mock MCP Server started. Waiting for tool calls (simulation only).")
        # In a real server, this would start listening for MCP requests (e.g., via stdio or network).
        # This simulation doesn't actually listen.
        pass

# Use the simulated framework
mcp_server = MockMCPFramework.initialize_server("philograph-mcp-server")

# --- Helper: API Interaction (Synchronous for simplicity in simulation) ---
# If the real MCP framework is async, this should use the async http_client
def call_backend_api_sync(method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Any:
    """Makes a synchronous HTTP request to the backend API."""
    url = f"{config.API_URL}{endpoint}"
    logger.debug(f"[MCP Server] Calling Backend API: {method} {url}")
    try:
        # Use synchronous httpx client
        with httpx.Client(timeout=120.0) as client: # Longer timeout for potentially long ops
            response = client.request(method, url, json=json_data)
            response.raise_for_status()
            try:
                return response.json()
            except json.JSONDecodeError:
                logger.error(f"[MCP Server] Failed to decode JSON response from Backend API {url}. Status: {response.status_code}. Response: {response.text[:500]}...")
                raise MCPToolError("Invalid response format from backend service.")
    except httpx.ConnectError as e:
        logger.error(f"[MCP Server] Connection error calling Backend API {url}: {e}")
        raise MCPToolError(f"Cannot connect to PhiloGraph backend at {config.API_URL}.")
    except httpx.HTTPStatusError as e:
        logger.error(f"[MCP Server] HTTP error calling Backend API {url}: {e.response.status_code} - {e.response.text[:500]}...")
        try:
            error_detail = e.response.json().get('detail', e.response.text)
        except json.JSONDecodeError:
            error_detail = e.response.text
        raise MCPToolError(f"Backend service error ({e.response.status_code}): {error_detail}")
    except Exception as e:
        logger.exception(f"[MCP Server] Unexpected error calling Backend API {url}", exc_info=e)
        raise MCPToolError(f"An unexpected error occurred while contacting the backend: {e}")


# --- Tool Definition: philograph_ingest ---
@mcp_server.tool(
    name="philograph_ingest",
    description="Ingest a document or directory into the PhiloGraph knowledge base.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file or directory relative to the configured source directory (e.g., 'kant/critique_of_pure_reason.pdf')."
            }
        },
        "required": ["path"]
    }
)
def handle_ingest_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handles the 'philograph_ingest' MCP tool call."""
    logger.info(f"[MCP Tool] Received 'philograph_ingest' call with args: {arguments}")
    path = arguments.get("path")
    if not path:
        # Basic validation, though framework might handle schema
        raise MCPValidationError("Missing required argument: path")

    # Call the backend API's /ingest endpoint (using sync helper for simulation)
    response_data = call_backend_api_sync("POST", "/ingest", json_data={"path": path})

    # Return the result from the backend API directly
    return response_data

# --- Tool Definition: philograph_search ---
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
                "description": "Optional metadata filters (e.g., {'author': 'Kant', 'year': 1781, 'doc_id': 123}).",
                "properties": {
                    "author": {"type": "string"},
                    "year": {"type": "integer"},
                    "doc_id": {"type": "integer"}
                    # Add more filter properties here if needed
                },
                "additionalProperties": False # Disallow unknown filters for now
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return.",
                "default": config.SEARCH_TOP_K,
                "minimum": 1,
                "maximum": 100
            }
        },
        "required": ["query"]
    }
)
def handle_search_tool(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handles the 'philograph_search' MCP tool call."""
    logger.info(f"[MCP Tool] Received 'philograph_search' call with args: {arguments}")
    query = arguments.get("query")
    filters = arguments.get("filters", None)
    limit = arguments.get("limit", config.SEARCH_TOP_K)

    if not query:
        raise MCPValidationError("Missing required argument: query")

    payload = {"query": query, "limit": limit}
    if filters:
        payload["filters"] = filters

    # Call the backend API's /search endpoint
    response_data = call_backend_api_sync("POST", "/search", json_data=payload)

    # Return the results list from the backend API response
    return response_data.get("results", [])

# --- Tool Definition: philograph_acquire (Updated Workflow - ADR 009) ---
@mcp_server.tool(
    name="philograph_acquire", # Renamed from philograph_acquire_missing
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
                "type": "string", # UUID string
                "description": "ID of a previous discovery session. Required for confirmation phase."
            },
            "selected_items": {
                "type": "array",
                "description": "List of candidate IDs (md5 or index_*) or full book details objects selected for acquisition. Required for confirmation phase.",
                "items": {
                    "oneOf": [
                        {"type": "string", "description": "Candidate ID (md5 or index_*)"},
                        {"type": "object", "description": "Full book details object"}
                    ]
                }
            }
        },
        # Complex validation (either filters OR discovery_id+selected_items) handled in function
    }
)
def handle_acquire_tool(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handles the 'philograph_acquire' MCP tool call for discovery or confirmation."""
    logger.info(f"[MCP Tool] Received 'philograph_acquire' call with args: {arguments}")

    discovery_id = arguments.get("discovery_id")
    selected_items = arguments.get("selected_items")
    filters = arguments.get("filters")

    # --- Input Validation ---
    is_discovery = filters is not None
    is_confirmation = discovery_id is not None and selected_items is not None

    if is_discovery and is_confirmation:
        raise MCPValidationError("Cannot provide both 'filters' and ('discovery_id', 'selected_items'). Use 'filters' for discovery or ('discovery_id', 'selected_items') for confirmation.")
    if not is_discovery and not is_confirmation:
        raise MCPValidationError("Must provide either 'filters' for discovery or ('discovery_id' AND 'selected_items') for confirmation.")
    if is_confirmation and not isinstance(selected_items, list):
         raise MCPValidationError("'selected_items' must be a list.")
    # Add more specific validation for filter contents if needed

    # --- API Call Logic ---
    if is_confirmation:
        # Confirmation Phase
        logger.info(f"[MCP Tool] Confirming acquisition for discovery session {discovery_id}")
        payload = {"selected_items": selected_items}
        endpoint = f"/acquire/confirm/{discovery_id}" # Use discovery_id in path
        response_data = call_backend_api_sync("POST", endpoint, json_data=payload)
        # Return backend response (e.g., {"message": "...", "status_url": "..."})
        return response_data

    else: # is_discovery
        # Discovery Phase
        logger.info(f"[MCP Tool] Starting acquisition discovery with filters: {filters}")
        payload = {"filters": filters}
        endpoint = "/acquire/discover"
        response_data = call_backend_api_sync("POST", endpoint, json_data=payload)
        # Return backend response (e.g., {"discovery_id": "...", "candidates": [...]})
        return response_data

    # Note: The agent calling this tool needs to handle the multi-step workflow.
    # 1. Call with 'filters' -> Receive 'discovery_id' and 'candidates'.
    # 2. Agent reviews 'candidates'.
    # 3. Call with 'discovery_id' and 'selected_items' -> Receive confirmation/status.


# --- Main Execution (Simulation) ---
if __name__ == "__main__":
    # In a real scenario, the MCP framework's start() method would handle everything.
    # This just logs that the simulated server is "running".
    mcp_server.start()
    # The start method in the simulation doesn't block,
    # so the script would normally exit here.
    # In a real server, start() would block or run indefinitely.