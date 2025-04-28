import pytest
import importlib

# Assuming utils and config are importable from tests context
from src.philograph.utils import mcp_utils
from src.philograph import config # Needed because mcp_utils imports config

# Reload modules for each test to ensure clean state
@pytest.fixture(autouse=True)
def reload_modules():
    importlib.reload(config)
    importlib.reload(mcp_utils)

# --- Tests for call_mcp_tool ---

@pytest.mark.asyncio
async def test_call_mcp_tool_zlib_search_success():
    """Test successful simulated call to zlibrary-mcp/search_books."""
    server = config.ZLIBRARY_MCP_SERVER_NAME
    tool = "search_books"
    args = {"query": "test query"}
    result = await mcp_utils.call_mcp_tool(server, tool, args)
    assert isinstance(result, list)
    assert len(result) == 2 # Based on current mock
    assert result[0]["id"] == "mock123"

@pytest.mark.asyncio
async def test_call_mcp_tool_zlib_download_success():
    """Test successful simulated call to zlibrary-mcp/download_book_to_file."""
    server = config.ZLIBRARY_MCP_SERVER_NAME
    tool = "download_book_to_file"
    args = {
        "bookDetails": {"id": "mock456", "title": "Test Book"},
        "process_for_rag": True
    }
    result = await mcp_utils.call_mcp_tool(server, tool, args)
    assert result["success"] is True
    assert "processed_path" in result
    assert result["processed_path"].endswith("mock456.txt") # Based on mock

@pytest.mark.asyncio
async def test_call_mcp_tool_zlib_search_missing_query():
    """Test zlibrary-mcp/search_books raises MCPValidationError if query is missing."""
    server = config.ZLIBRARY_MCP_SERVER_NAME
    tool = "search_books"
    args = {} # Missing query
    with pytest.raises(mcp_utils.MCPValidationError) as excinfo:
        await mcp_utils.call_mcp_tool(server, tool, args)
    assert "Missing 'query' argument" in str(excinfo.value)

@pytest.mark.asyncio
async def test_call_mcp_tool_zlib_download_missing_details():
    """Test zlibrary-mcp/download raises MCPValidationError if bookDetails missing."""
    server = config.ZLIBRARY_MCP_SERVER_NAME
    tool = "download_book_to_file"
    args = {"process_for_rag": True} # Missing bookDetails
    with pytest.raises(mcp_utils.MCPValidationError) as excinfo:
        await mcp_utils.call_mcp_tool(server, tool, args)
    assert "Missing or invalid 'bookDetails' argument" in str(excinfo.value)

@pytest.mark.asyncio
async def test_call_mcp_tool_zlib_unknown_tool():
    """Test calling an unknown tool on zlibrary-mcp raises MCPToolError."""
    server = config.ZLIBRARY_MCP_SERVER_NAME
    tool = "unknown_tool"
    args = {}
    with pytest.raises(mcp_utils.MCPToolError) as excinfo:
        await mcp_utils.call_mcp_tool(server, tool, args)
    assert f"Unknown tool '{tool}' for server '{server}'" in str(excinfo.value)

@pytest.mark.asyncio
async def test_call_mcp_tool_unknown_server():
    """Test calling a tool on an unknown server raises MCPToolError."""
    server = "unknown_server"
    tool = "any_tool"
    args = {}
    with pytest.raises(mcp_utils.MCPToolError) as excinfo:
        await mcp_utils.call_mcp_tool(server, tool, args)
    assert f"Unknown server '{server}'" in str(excinfo.value)