import pytest
from unittest.mock import patch, AsyncMock

# Assuming MCP server main logic is in src.philograph.mcp.main
# Adjust import path if necessary
from src.philograph.mcp import main as mcp_main
from src.philograph.utils import http_client # For mocking API calls

# TODO: Add fixtures if needed (e.g., for mocking config)

# --- Tests for Revised philograph_acquire Tool (ADR 009) ---

@pytest.mark.asyncio
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

@pytest.mark.asyncio
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

@pytest.mark.asyncio
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

@pytest.mark.asyncio
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

@pytest.mark.asyncio
def test_philograph_acquire_invalid_args_missing():
    """Test philograph_acquire tool validation when required args are missing."""
    # Arrange
    args = {} # Missing both filters and discovery_id/selected_items

    # Act & Assert
    with pytest.raises(mcp_main.MCPValidationError, match="Must provide either 'filters' for discovery or"):
        mcp_main.handle_acquire_tool(args)

@pytest.mark.asyncio
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

@pytest.mark.asyncio
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