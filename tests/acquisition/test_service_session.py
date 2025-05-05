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


# --- Tests for Session Management Helpers ---
# Testing these indirectly via the main handlers is generally preferred,
# but adding a few direct tests for clarity on core session logic.

def test_create_discovery_session(mock_config):
    """Test the internal session creation logic."""
    test_uuid = uuid.uuid4()
    start_time = time.time()
    with patch('src.philograph.acquisition.service.uuid.uuid4', return_value=test_uuid), \
         patch('src.philograph.acquisition.service.time.time', return_value=start_time):
        discovery_id = service.create_discovery_session()

        assert discovery_id == str(test_uuid)
        assert discovery_id in service.discovery_sessions
        session = service.discovery_sessions[discovery_id]
        assert session['status'] == 'pending_confirmation'
        assert session['created_at'] == start_time
        assert session['candidates'] == []
        assert session['selected_items'] == []
        assert session['processed_items'] == []
        assert session['error_message'] is None

def test_get_discovery_session_valid(mock_config):
    """Test retrieving a valid, non-expired session."""
    discovery_id = service.create_discovery_session() # Use the real creation logic
    retrieved_session = service.get_discovery_session(discovery_id)
    assert retrieved_session is not None
    assert retrieved_session == service.discovery_sessions[discovery_id]

def test_get_discovery_session_invalid(mock_config):
    """Test retrieving a non-existent session."""
    retrieved_session = service.get_discovery_session("non-existent-id")
    assert retrieved_session is None

def test_get_discovery_session_expired(mock_config):
    """Test retrieving an expired session."""
    discovery_id = service.create_discovery_session()
    session = service.discovery_sessions[discovery_id]
    # Manually set creation time far in the past
    session['created_at'] = time.time() - (service.SESSION_TIMEOUT_SECONDS + 10)

    retrieved_session = service.get_discovery_session(discovery_id)
    assert retrieved_session is None
    # Optional: Check if session was deleted (current implementation doesn't delete)
    # assert discovery_id not in service.discovery_sessions

def test_update_discovery_session_success(mock_config):
    """Test updating an existing session."""
    discovery_id = service.create_discovery_session()
    updates = {"status": "processing", "candidates": ["candidate1"]}
    result = service.update_discovery_session(discovery_id, updates)
    assert result is True
    session = service.discovery_sessions[discovery_id]
    assert session['status'] == "processing"
    assert session['candidates'] == ["candidate1"]

def test_update_discovery_session_invalid_id(mock_config):
    """Test updating a non-existent session."""
    updates = {"status": "processing"}
    result = service.update_discovery_session("non-existent-id", updates)
    assert result is False

def test_update_discovery_session_expired(mock_config):
    """Test updating an expired session."""
    discovery_id = service.create_discovery_session()
    session = service.discovery_sessions[discovery_id]
    session['created_at'] = time.time() - (service.SESSION_TIMEOUT_SECONDS + 10)
    updates = {"status": "processing"}
    result = service.update_discovery_session(discovery_id, updates)
    assert result is False # Update should fail as get_discovery_session returns None