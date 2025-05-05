import pytest
from unittest.mock import patch, AsyncMock

# Assuming MCP server main logic is in src.philograph.mcp.main
# Adjust import path if necessary
from src.philograph.mcp import main as mcp_main
from src.philograph.utils import http_client # For mocking API calls

# TODO: Add fixtures if needed (e.g., for mocking config)

# --- Tests for Revised philograph_acquire Tool (ADR 009) ---

@patch("src.philograph.mcp.main.call_backend_api_sync")
def test_philograph_acquire_discovery_success(mock_call_api):
    """Test philograph_acquire tool successfully calls /acquire/discover."""
    # Arrange
    filters = {"author": "Kant"}
    args = {"filters": filters}
    expected_payload = {"filters": filters}
    expected_endpoint = "/acquire/discover"
    mock_api_response = {"discovery_id": "uuid-123", "candidates": [{"title": "Critique"}]}
    mock_call_api.return_value = mock_api_response

    # Act
    result = mcp_main.handle_acquire_tool(args)

    # Assert
    assert result == mock_api_response
    mock_call_api.assert_called_once_with("POST", expected_endpoint, json_data=expected_payload)

@patch("src.philograph.mcp.main.call_backend_api_sync")
def test_philograph_acquire_discovery_api_error(mock_call_api):
    """Test philograph_acquire tool handles API errors during discovery."""
    # Arrange
    filters = {"author": "Kant"}
    args = {"filters": filters}
    expected_payload = {"filters": filters}
    expected_endpoint = "/acquire/discover"
    error_message = "Backend service unavailable"
    mock_call_api.side_effect = mcp_main.MCPToolError(error_message) # Simulate error from helper

    # Act & Assert
    with pytest.raises(mcp_main.MCPToolError, match=error_message):
        mcp_main.handle_acquire_tool(args)

    mock_call_api.assert_called_once_with("POST", expected_endpoint, json_data=expected_payload)

@patch("src.philograph.mcp.main.call_backend_api_sync")
def test_philograph_acquire_confirmation_success(mock_call_api):
    """Test philograph_acquire tool successfully calls /acquire/confirm."""
    # Arrange
    discovery_id = "uuid-123"
    selected_items = [{"md5": "md5_abc"}]
    args = {"discovery_id": discovery_id, "selected_items": selected_items}
    expected_payload = {"selected_items": selected_items}
    expected_endpoint = f"/acquire/confirm/{discovery_id}"
    mock_api_response = {"message": "Processing started", "status_url": "/status/uuid-123"}
    mock_call_api.return_value = mock_api_response

    # Act
    result = mcp_main.handle_acquire_tool(args)

    # Assert
    assert result == mock_api_response
    mock_call_api.assert_called_once_with("POST", expected_endpoint, json_data=expected_payload)

@patch("src.philograph.mcp.main.call_backend_api_sync")
def test_philograph_acquire_confirmation_api_error(mock_call_api):
    """Test philograph_acquire tool handles API errors during confirmation."""
    # Arrange
    discovery_id = "uuid-123"
    selected_items = [{"md5": "md5_abc"}]
    args = {"discovery_id": discovery_id, "selected_items": selected_items}
    expected_payload = {"selected_items": selected_items}
    expected_endpoint = f"/acquire/confirm/{discovery_id}"
    error_message = "Session not found"
    mock_call_api.side_effect = mcp_main.MCPToolError(error_message) # Simulate error from helper

    # Act & Assert
    with pytest.raises(mcp_main.MCPToolError, match=error_message):
        mcp_main.handle_acquire_tool(args)

    mock_call_api.assert_called_once_with("POST", expected_endpoint, json_data=expected_payload)

def test_philograph_acquire_invalid_args_missing():
    """Test philograph_acquire tool validation when required args are missing."""
    # Arrange
    args = {} # Missing both filters and discovery_id/selected_items

    # Act & Assert
    with pytest.raises(mcp_main.MCPValidationError, match="Must provide either 'filters' for discovery or"):
        mcp_main.handle_acquire_tool(args)

def test_philograph_acquire_invalid_args_confirmation_missing_items():
    """Test philograph_acquire tool validation for confirmation missing selected_items."""
    # Arrange
    args = {"discovery_id": "uuid-123"} # Missing selected_items

    # Act & Assert
    with pytest.raises(mcp_main.MCPValidationError, match="Must provide either 'filters' for discovery or"):
        mcp_main.handle_acquire_tool(args)

def test_philograph_acquire_invalid_args_confirmation_missing_id():
    """Test philograph_acquire tool validation for confirmation missing discovery_id."""
    # Arrange
    args = {"selected_items": []} # Missing discovery_id

    # Act & Assert
    with pytest.raises(mcp_main.MCPValidationError, match="Must provide either 'filters' for discovery or"):
        mcp_main.handle_acquire_tool(args)

def test_philograph_acquire_conflicting_args():
    """Test philograph_acquire tool validation for conflicting arguments."""
    # Arrange
    args = {
        "filters": {"author": "Kant"},
        "discovery_id": "uuid-123",
        "selected_items": []
    }

    # Act & Assert
    with pytest.raises(mcp_main.MCPValidationError, match="Cannot provide both 'filters' and"):
        mcp_main.handle_acquire_tool(args)
# --- Tests for philograph_ingest Tool ---

@patch("src.philograph.mcp.main.call_backend_api_sync")
def test_philograph_ingest_success(mock_call_api):
    """Test philograph_ingest tool successfully calls /ingest."""
    # Arrange
    path = "kant/critique.pdf"
    args = {"path": path}
    expected_payload = {"path": path}
    expected_endpoint = "/ingest"
    mock_api_response = {"message": "Ingestion started for kant/critique.pdf", "status": "pending"}
    mock_call_api.return_value = mock_api_response

    # Act
    result = mcp_main.handle_ingest_tool(args)

    # Assert
    assert result == mock_api_response
    mock_call_api.assert_called_once_with("POST", expected_endpoint, json_data=expected_payload)

@patch("src.philograph.mcp.main.call_backend_api_sync")
def test_philograph_ingest_api_error(mock_call_api):
    """Test philograph_ingest tool handles API errors."""
    # Arrange
    path = "kant/critique.pdf"
    args = {"path": path}
    expected_payload = {"path": path}
    expected_endpoint = "/ingest"
    error_message = "File not found on server"
    mock_call_api.side_effect = mcp_main.MCPToolError(error_message) # Simulate error from helper

    # Act & Assert
    with pytest.raises(mcp_main.MCPToolError, match=error_message):
        mcp_main.handle_ingest_tool(args)

    mock_call_api.assert_called_once_with("POST", expected_endpoint, json_data=expected_payload)

def test_philograph_ingest_missing_path():
    """Test philograph_ingest tool validation for missing path."""
    # Arrange
    args = {} # Missing path

    # Act & Assert
    with pytest.raises(mcp_main.MCPValidationError, match="Missing required argument: path"):
        mcp_main.handle_ingest_tool(args)

# --- Tests for philograph_search Tool ---

@patch("src.philograph.mcp.main.call_backend_api_sync")
def test_philograph_search_success_query_only(mock_call_api):
    """Test philograph_search tool success with only query."""
    # Arrange
    query = "What is critique?"
    limit = 5 # Example limit
    args = {"query": query, "limit": limit}
    expected_payload = {"query": query, "limit": limit}
    expected_endpoint = "/search"
    mock_api_response = {"results": [{"chunk_id": 1, "text": "...", "score": 0.9}]}
    mock_call_api.return_value = mock_api_response

    # Act
    result = mcp_main.handle_search_tool(args)

    # Assert
    assert result == mock_api_response["results"]
    mock_call_api.assert_called_once_with("POST", expected_endpoint, json_data=expected_payload)

@patch("src.philograph.mcp.main.call_backend_api_sync")
def test_philograph_search_success_with_filters(mock_call_api):
    """Test philograph_search tool success with query and filters."""
    # Arrange
    query = "What is critique?"
    filters = {"author": "Kant"}
    limit = 10 # Default limit
    args = {"query": query, "filters": filters} # Use default limit
    expected_payload = {"query": query, "limit": limit, "filters": filters}
    expected_endpoint = "/search"
    mock_api_response = {"results": [{"chunk_id": 2, "text": "...", "score": 0.8}]}
    mock_call_api.return_value = mock_api_response

    # Act
    result = mcp_main.handle_search_tool(args)

    # Assert
    assert result == mock_api_response["results"]
    mock_call_api.assert_called_once_with("POST", expected_endpoint, json_data=expected_payload)


@patch("src.philograph.mcp.main.call_backend_api_sync")
def test_philograph_search_api_error(mock_call_api):
    """Test philograph_search tool handles API errors."""
    # Arrange
    query = "What is critique?"
    args = {"query": query}
    expected_payload = {"query": query, "limit": mcp_main.config.SEARCH_TOP_K} # Check default limit usage
    expected_endpoint = "/search"
    error_message = "Embedding generation failed"
    mock_call_api.side_effect = mcp_main.MCPToolError(error_message) # Simulate error from helper

    # Act & Assert
    with pytest.raises(mcp_main.MCPToolError, match=error_message):
        mcp_main.handle_search_tool(args)

    mock_call_api.assert_called_once_with("POST", expected_endpoint, json_data=expected_payload)

def test_philograph_search_missing_query():
    """Test philograph_search tool validation for missing query."""
    # Arrange
    args = {"limit": 5} # Missing query

    # Act & Assert
    with pytest.raises(mcp_main.MCPValidationError, match="Missing required argument: query"):
        mcp_main.handle_search_tool(args)