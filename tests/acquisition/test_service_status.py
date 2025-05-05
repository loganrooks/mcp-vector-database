import pytest
import uuid
import time
from unittest.mock import patch, MagicMock

# Import the module/functions under test
from src.philograph.acquisition import service
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


# --- Tests for get_status ---

@pytest.mark.asyncio
async def test_get_status_pending(mock_config):
    """Test get_status for a session pending confirmation."""
    discovery_id = service.create_discovery_session()
    # Default state is pending_confirmation
    result = await service.get_status(discovery_id)
    assert result is not None
    assert result['status'] == 'pending_confirmation'

@pytest.mark.asyncio
async def test_get_status_processing(mock_config):
    """Test get_status for a session currently processing."""
    discovery_id = service.create_discovery_session()
    service.update_discovery_session(discovery_id, {"status": "processing", "selected_items": ["item1"]})
    result = await service.get_status(discovery_id)
    assert result is not None
    assert result['status'] == 'processing'
    assert result['selected_items'] == ["item1"]

@pytest.mark.asyncio
async def test_get_status_complete(mock_config):
    """Test get_status for a completed session."""
    discovery_id = service.create_discovery_session()
    final_state = {
        "status": "complete",
        "selected_items": [{"md5": "md5_c"}],
        "processed_items": [{"id": "md5_c", "status": "ingested", "document_id": "doc_c"}]
    }
    service.update_discovery_session(discovery_id, final_state)
    result = await service.get_status(discovery_id)
    assert result is not None
    assert result['status'] == 'complete'
    assert result['processed_items'][0]['document_id'] == 'doc_c'

@pytest.mark.asyncio
async def test_get_status_error(mock_config):
    """Test get_status for a session that ended in error."""
    discovery_id = service.create_discovery_session()
    service.update_discovery_session(discovery_id, {"status": "error", "error_message": "Something failed"})
    result = await service.get_status(discovery_id)
    assert result is not None
    assert result['status'] == 'error'
    assert result['error_message'] == "Something failed"

@pytest.mark.asyncio
async def test_get_status_not_found(mock_config):
    """Test get_status with an invalid session ID."""
    result = await service.get_status("invalid-id")
    assert result is None