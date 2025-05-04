import pytest
import uuid
import time
from unittest.mock import patch, AsyncMock, MagicMock, call
from collections import deque

# Import the module/functions under test
from src.philograph.acquisition import service
from src.philograph.utils import mcp_utils
from src.philograph.ingestion import pipeline as ingestion_pipeline
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

# --- Tests for _validate_book_details (Kept from previous version, slightly adapted) ---

def test_validate_book_details_success():
    """Test validation passes with required and optional keys."""
    details = {
        "title": "Valid Book", "author": "Author", "md5": "validmd5",
        "download_url": "http://example.com/dl", "extension": "pdf",
        "unexpected_key": "allowed" # Unexpected keys are allowed but warned
    }
    assert service._validate_book_details(details) is True

def test_validate_book_details_missing_required_md5():
    """Test validation fails if md5 is missing."""
    details = {"title": "Missing MD5", "download_url": "http://example.com/dl"}
    assert service._validate_book_details(details) is False

def test_validate_book_details_missing_required_url():
    """Test validation fails if download_url is missing."""
    details = {"title": "Missing URL", "md5": "somemd5"}
    assert service._validate_book_details(details) is False

def test_validate_book_details_invalid_type_md5():
    """Test validation fails if md5 is not a string."""
    details = {"title": "Invalid MD5", "md5": 12345, "download_url": "http://example.com/dl"}
    assert service._validate_book_details(details) is False

def test_validate_book_details_invalid_type_url():
    """Test validation fails if download_url is not a string."""
    details = {"title": "Invalid URL", "md5": "somemd5", "download_url": None}
    assert service._validate_book_details(details) is False

def test_validate_book_details_not_dict():
    """Test validation fails if input is not a dictionary."""
    assert service._validate_book_details("not a dict") is False

# --- Tests for handle_confirmation_request ---

@pytest.mark.asyncio
async def test_handle_confirmation_request_success(mock_config):
    """Test handle_confirmation_request success path for one item."""
    discovery_id = service.create_discovery_session()
    candidate_book = {"id": "zlib1", "title": "Confirm Book", "md5": "confirm_md5", "download_url": "http://confirm.dl"}
    selected_item = candidate_book # Select the full details
    service.discovery_sessions[discovery_id]['candidates'] = [candidate_book, {"id": "zlib2", "title": "Other"}]
    service.discovery_sessions[discovery_id]['status'] = 'pending_confirmation' # Set correct initial state

    mock_mcp_download_response = {"success": True, "processed_path": "/path/to/processed.txt"}
    mock_ingestion_response = {"status": "Success", "document_id": "doc-123"}
    start_time = time.time()

    with patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock, return_value=mock_mcp_download_response) as mock_call_mcp, \
         patch('src.philograph.ingestion.pipeline.process_document', new_callable=AsyncMock, return_value=mock_ingestion_response) as mock_process_doc, \
         patch('src.philograph.acquisition.service.time.time', return_value=start_time): # Mock time for rate limiting

        result = await service.handle_confirmation_request(discovery_id, [selected_item])

        assert result == {"status": "processing_started"}

        # Check session state updates during processing (hard to check intermediate without async tasks)
        # Check final session state
        session = service.discovery_sessions[discovery_id]
        assert session['status'] == 'complete' # Should be complete as all items succeeded
        assert session['selected_items'] == [selected_item]
        assert len(session['processed_items']) == 1
        processed_item = session['processed_items'][0]
        assert processed_item['id'] == candidate_book['md5']
        assert processed_item['title'] == candidate_book['title']
        assert processed_item['status'] == 'ingested'
        assert processed_item['error'] is None
        assert processed_item['document_id'] == 'doc-123'

        mock_call_mcp.assert_awaited_once_with(
            config.ZLIBRARY_MCP_SERVER_NAME,
            "download_book_to_file",
            {"bookDetails": selected_item, "process_for_rag": True, "processed_output_format": "text"}
        )
        mock_process_doc.assert_awaited_once_with(mock_mcp_download_response['processed_path'])
        # Check rate limiting
        assert len(service._download_request_timestamps) == 1
        assert service._download_request_timestamps[0] == start_time

@pytest.mark.asyncio
async def test_handle_confirmation_request_invalid_session_id(mock_config):
    """Test handle_confirmation_request with an invalid session ID."""
    result = await service.handle_confirmation_request("invalid-id", [{"md5": "any"}])
    assert result == {"status": "not_found", "message": "Discovery session not found or expired."}

@pytest.mark.asyncio
async def test_handle_confirmation_request_invalid_session_state(mock_config):
    """Test handle_confirmation_request when session is not in 'pending_confirmation' state."""
    discovery_id = service.create_discovery_session()
    service.discovery_sessions[discovery_id]['status'] = 'processing' # Set wrong state
    result = await service.handle_confirmation_request(discovery_id, [{"md5": "any"}])
    assert result == {"status": "invalid_state", "message": "Discovery session is not awaiting confirmation (status: processing)."}

@pytest.mark.asyncio
async def test_handle_confirmation_request_invalid_items_not_in_candidates(mock_config):
    """Test handle_confirmation_request with selected items not in session candidates."""
    discovery_id = service.create_discovery_session()
    service.discovery_sessions[discovery_id]['candidates'] = [{"id": "zlib1", "title": "Real Candidate", "md5": "real_md5"}]
    service.discovery_sessions[discovery_id]['status'] = 'pending_confirmation'
    invalid_item = {"id": "zlib_invalid", "title": "Fake", "md5": "fake_md5", "download_url": "http://fake.dl"} # Not in candidates

    result = await service.handle_confirmation_request(discovery_id, [invalid_item])

    assert result == {
        "status": "invalid_selection",
        "message": "No valid items selected.",
        "details": "Item with md5 'fake_md5' not found in candidates."
    }
    session = service.discovery_sessions[discovery_id]
    assert session['status'] == 'error' # Status updated to error
    assert session['error_message'] == "No valid items selected for confirmation."

@pytest.mark.asyncio
async def test_handle_confirmation_request_invalid_items_validation_fail(mock_config):
    """Test handle_confirmation_request with selected items failing validation."""
    discovery_id = service.create_discovery_session()
    invalid_item = {"id": "zlib_invalid", "title": "Fake", "md5": 123} # Invalid md5 type
    service.discovery_sessions[discovery_id]['candidates'] = [invalid_item] # Add to candidates to pass that check
    service.discovery_sessions[discovery_id]['status'] = 'pending_confirmation'

    result = await service.handle_confirmation_request(discovery_id, [invalid_item])

    assert result == {
        "status": "invalid_selection",
        "message": "No valid items selected.",
        "details": "Validation failed for item ID '123'." # ID used in message is md5
    }
    session = service.discovery_sessions[discovery_id]
    assert session['status'] == 'error'
    assert session['error_message'] == "No valid items selected for confirmation."


@pytest.mark.asyncio
async def test_handle_confirmation_request_mcp_download_error(mock_config):
    """Test handle_confirmation_request when MCP download fails for one item."""
    discovery_id = service.create_discovery_session()
    book1 = {"id": "zlib1", "title": "Book 1", "md5": "md5_1", "download_url": "http://dl1"}
    book2 = {"id": "zlib2", "title": "Book 2 Fail", "md5": "md5_2_fail", "download_url": "http://dl2"}
    service.discovery_sessions[discovery_id]['candidates'] = [book1, book2]
    service.discovery_sessions[discovery_id]['status'] = 'pending_confirmation'

    mock_mcp_responses = [
        {"success": True, "processed_path": "/path/book1.txt"}, # Success for book1
        mcp_utils.MCPToolError("Download failed") # Error for book2
    ]
    mock_ingestion_response = {"status": "Success", "document_id": "doc-1"}

    with patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock, side_effect=mock_mcp_responses) as mock_call_mcp, \
         patch('src.philograph.ingestion.pipeline.process_document', new_callable=AsyncMock, return_value=mock_ingestion_response) as mock_process_doc:

        result = await service.handle_confirmation_request(discovery_id, [book1, book2])

        assert result == {"status": "processing_started"}
        session = service.discovery_sessions[discovery_id]
        assert session['status'] == 'complete_with_errors'
        assert len(session['processed_items']) == 2

        item1_status = next(item for item in session['processed_items'] if item['id'] == 'md5_1')
        item2_status = next(item for item in session['processed_items'] if item['id'] == 'md5_2_fail')

        assert item1_status['status'] == 'ingested'
        assert item1_status['document_id'] == 'doc-1'
        assert item1_status['error'] is None

        assert item2_status['status'] == 'processing_error' # MCPToolError maps to processing_error
        assert item2_status['error'] == 'MCP Tool Error: Download failed'
        assert item2_status['document_id'] is None

        assert mock_call_mcp.await_count == 2
        mock_process_doc.assert_awaited_once() # Only called for book1

@pytest.mark.asyncio
async def test_handle_confirmation_request_ingestion_error(mock_config):
    """Test handle_confirmation_request when ingestion pipeline fails for one item."""
    discovery_id = service.create_discovery_session()
    book1 = {"id": "zlib1", "title": "Book 1 Fail", "md5": "md5_1_fail", "download_url": "http://dl1"}
    service.discovery_sessions[discovery_id]['candidates'] = [book1]
    service.discovery_sessions[discovery_id]['status'] = 'pending_confirmation'

    mock_mcp_download_response = {"success": True, "processed_path": "/path/book1_fail.txt"}
    mock_ingestion_response = {"status": "Error", "message": "Ingestion pipeline error"}

    with patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock, return_value=mock_mcp_download_response) as mock_call_mcp, \
         patch('src.philograph.ingestion.pipeline.process_document', new_callable=AsyncMock, return_value=mock_ingestion_response) as mock_process_doc:

        result = await service.handle_confirmation_request(discovery_id, [book1])

        assert result == {"status": "processing_started"}
        session = service.discovery_sessions[discovery_id]
        assert session['status'] == 'complete_with_errors'
        assert len(session['processed_items']) == 1
        item_status = session['processed_items'][0]

        assert item_status['status'] == 'ingestion_failed'
        assert item_status['error'] == 'Ingestion pipeline error'
        assert item_status['document_id'] is None

        mock_call_mcp.assert_awaited_once()
        mock_process_doc.assert_awaited_once()

@pytest.mark.asyncio
async def test_handle_confirmation_request_rate_limit_exceeded(mock_config):
    """Test confirmation requests fail when exceeding the rate limit."""
    discovery_id = service.create_discovery_session()
    book1 = {"id": "zlib1", "title": "Book 1", "md5": "md5_1", "download_url": "http://dl1"}
    service.discovery_sessions[discovery_id]['candidates'] = [book1]
    service.discovery_sessions[discovery_id]['status'] = 'pending_confirmation'
    start_time = time.time()

    # Pre-fill timestamps
    timestamps = [start_time - service.DOWNLOAD_RATE_LIMIT_WINDOW_SECONDS + 1 + i for i in range(service.DOWNLOAD_RATE_LIMIT_MAX_REQUESTS)]
    service._download_request_timestamps.extend(timestamps)

    with patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock) as mock_call_mcp, \
         patch('src.philograph.ingestion.pipeline.process_document', new_callable=AsyncMock) as mock_process_doc, \
         patch('src.philograph.acquisition.service.time.time', return_value=start_time):

        result = await service.handle_confirmation_request(discovery_id, [book1])

        assert result == {
            "status": "error",
            "message": "Download rate limit exceeded. Please try again later."
        }
        mock_call_mcp.assert_not_awaited()
        mock_process_doc.assert_not_awaited()
        # Session status should NOT be updated to error by rate limit check itself
        assert service.discovery_sessions[discovery_id]['status'] == 'pending_confirmation'


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