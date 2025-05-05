import pytest
import uuid
import time
from unittest.mock import patch, AsyncMock, MagicMock

# Import the module/functions under test
from src.philograph.acquisition import service
from src.philograph.utils import mcp_utils
from src.philograph import config # Import config directly

# --- Fixtures ---

@pytest.fixture(autouse=True)
def clear_discovery_sessions():
    """Clears the global discovery_sessions dict before each test."""
    service.discovery_sessions.clear()
    # Also clear rate limiting deques for isolation
    service._search_request_timestamps.clear()
    service._download_request_timestamps.clear()
    yield # Test runs here
    service.discovery_sessions.clear()
    service._search_request_timestamps.clear()
    service._download_request_timestamps.clear()


@pytest.fixture
def mock_config(mocker):
    """Fixture to mock config values."""
    mocker.patch.object(config, 'ZLIBRARY_MCP_SERVER_NAME', 'zlibrary-mcp')
    mocker.patch.object(service, 'SESSION_TIMEOUT_SECONDS', 3600)
    mocker.patch.object(service, 'SEARCH_RATE_LIMIT_WINDOW_SECONDS', 60)
    mocker.patch.object(service, 'SEARCH_RATE_LIMIT_MAX_REQUESTS', 3) # Lower for testing
    mocker.patch.object(service, 'DOWNLOAD_RATE_LIMIT_WINDOW_SECONDS', 60)
    mocker.patch.object(service, 'DOWNLOAD_RATE_LIMIT_MAX_REQUESTS', 2) # Lower for testing


# --- Tests for handle_discovery_request ---

@pytest.mark.asyncio
async def test_handle_discovery_request_success_with_filters(mock_config):
    """Test handle_discovery_request success path with basic filters."""
    filters = {"title": "Test Book", "author": "Test Author"}
    expected_query = "Test Book Test Author"
    mock_mcp_results = [{"id": "zlib1", "title": "Test Book", "md5": "md5_1"}]
    test_uuid = uuid.uuid4()
    start_time = time.time()

    with patch('src.philograph.acquisition.service.create_discovery_session', return_value=str(test_uuid)) as mock_create, \
         patch('src.philograph.acquisition.service.update_discovery_session') as mock_update, \
         patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock, return_value=mock_mcp_results) as mock_call_mcp, \
         patch('src.philograph.acquisition.service.time.time', return_value=start_time): # Mock time for rate limiting

        result = await service.handle_discovery_request(filters)

        assert result == {
            "status": "success",
            "discovery_id": str(test_uuid),
            "candidates": mock_mcp_results
        }
        mock_create.assert_called_once()
        mock_call_mcp.assert_awaited_once_with(
            config.ZLIBRARY_MCP_SERVER_NAME,
            "search_books",
            {"query": expected_query, "count": 5}
        )
        # Check that update_discovery_session was called to store candidates
        mock_update.assert_called_once_with(str(test_uuid), {"candidates": mock_mcp_results})
        # Check rate limiting timestamp was added
        assert len(service._search_request_timestamps) == 1
        assert service._search_request_timestamps[0] == start_time

@pytest.mark.asyncio
async def test_handle_discovery_request_no_candidates(mock_config):
    """Test handle_discovery_request when zlibrary-mcp returns no results."""
    filters = {"title": "Obscure"}
    expected_query = "Obscure"
    test_uuid = uuid.uuid4()

    with patch('src.philograph.acquisition.service.create_discovery_session', return_value=str(test_uuid)) as mock_create, \
         patch('src.philograph.acquisition.service.update_discovery_session') as mock_update, \
         patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock, return_value=[]) as mock_call_mcp:

        result = await service.handle_discovery_request(filters)

        assert result == {
            "status": "no_candidates",
            "discovery_id": str(test_uuid),
            "candidates": []
        }
        mock_create.assert_called_once()
        mock_call_mcp.assert_awaited_once_with(
            config.ZLIBRARY_MCP_SERVER_NAME,
            "search_books",
            {"query": expected_query, "count": 5}
        )
        # Check session status was updated to complete with empty candidates
        mock_update.assert_called_once_with(str(test_uuid), {"status": "complete", "candidates": []})

@pytest.mark.asyncio
async def test_handle_discovery_request_mcp_error(mock_config):
    """Test handle_discovery_request when zlibrary-mcp search fails."""
    filters = {"title": "Error Book"}
    expected_query = "Error Book"
    test_uuid = uuid.uuid4()
    error_message = "MCP search failed"

    with patch('src.philograph.acquisition.service.create_discovery_session', return_value=str(test_uuid)) as mock_create, \
         patch('src.philograph.acquisition.service.update_discovery_session') as mock_update, \
         patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock, side_effect=mcp_utils.MCPToolError(error_message)) as mock_call_mcp:

        result = await service.handle_discovery_request(filters)

        assert result == {
            "status": "error",
            "message": f"Z-Library search failed: Tool Error: {error_message}"
        }
        mock_create.assert_called_once()
        mock_call_mcp.assert_awaited_once_with(
            config.ZLIBRARY_MCP_SERVER_NAME,
            "search_books",
            {"query": expected_query, "count": 5}
        )
        # Check session status was updated to error
        mock_update.assert_called_once_with(str(test_uuid), {"status": "error", "error_message": f"All Z-Library searches failed: Tool Error: {error_message}"})

@pytest.mark.asyncio
async def test_handle_discovery_request_db_error(mock_config):
    """Test handle_discovery_request when a (simulated) database error occurs."""
    # In Tier 0, DB interaction is minimal/skipped, but we test the error handling path
    filters = {"threshold": 5}
    test_uuid = uuid.uuid4()
    db_error_message = "Simulated DB connection error"

    # Mock the necessary components using nested with statements
    with patch('src.philograph.acquisition.service.create_discovery_session', return_value=str(test_uuid)) as mock_create:
        with patch('src.philograph.acquisition.service.update_discovery_session') as mock_update:
            with patch('src.philograph.acquisition.service.logger.error') as mock_logger_error:
                # Simulate an error occurring during the candidate finding phase (inside the try block)
                # Patching logger.warning which is called conditionally inside the try block.
                with patch('src.philograph.acquisition.service.logger.warning', side_effect=Exception(db_error_message)):
                    result = await service.handle_discovery_request(filters)

                # Assert the expected error response
                assert result == {
                    "status": "error",
                    "message": f"Candidate finding failed: {db_error_message}"
                }
                # Assert session creation and update calls
                mock_create.assert_called_once()
                mock_update.assert_called_once_with(str(test_uuid), {"status": "error", "error_message": f"Candidate finding failed: {db_error_message}"})
                # Assert logger.error was called within the except block
                mock_logger_error.assert_called_once()
                assert db_error_message in mock_logger_error.call_args[0][0]

@pytest.mark.asyncio
async def test_handle_discovery_request_rate_limit_exceeded(mock_config):
    """Test discovery requests fail when exceeding the rate limit."""
    filters = {"title": "Rate Limit Exceed"}
    start_time = time.time()

    # Pre-fill timestamps within the window
    timestamps = [start_time - service.SEARCH_RATE_LIMIT_WINDOW_SECONDS + 1 + i for i in range(service.SEARCH_RATE_LIMIT_MAX_REQUESTS)]
    service._search_request_timestamps.extend(timestamps)

    with patch('src.philograph.acquisition.service.create_discovery_session') as mock_create, \
         patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock) as mock_call_mcp, \
         patch('src.philograph.acquisition.service.time.time', return_value=start_time):

        result = await service.handle_discovery_request(filters)

        assert result == {
            "status": "error",
            "message": "Search rate limit exceeded. Please try again later."
        }
        mock_create.assert_not_called()
        mock_call_mcp.assert_not_awaited()