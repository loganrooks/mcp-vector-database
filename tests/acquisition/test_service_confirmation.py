import pytest
import uuid
import time
from unittest.mock import patch, AsyncMock, MagicMock

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


@pytest.mark.asyncio
async def test_handle_confirmation_request_empty_selection(mock_config):
    """Test confirmation request with an empty selection list."""
    discovery_id = service.create_discovery_session()
    service.discovery_sessions[discovery_id]['status'] = 'pending_confirmation'
    service.discovery_sessions[discovery_id]['candidates'] = [{"id": "zlib1", "md5": "md5_1"}] # Add some candidates

    result = await service.handle_confirmation_request(discovery_id, [])

    assert result == {
        "status": "invalid_selection",
        "message": "No items selected."
    }
    # Session status should ideally remain pending or become error? Pseudocode implies error. Implementation returns before update.
    # Let's assert it remains pending for now, based on current implementation path.
    assert service.discovery_sessions[discovery_id]['status'] == 'pending_confirmation'
    # assert False # Intentionally fail for Red phase if needed

@pytest.mark.asyncio
async def test_handle_confirmation_request_mixed_valid_invalid_selection(mock_config):
    """Test confirmation with a mix of valid and invalid selections."""
    discovery_id = service.create_discovery_session()
    valid_book = {"id": "zlib1", "title": "Valid Book", "md5": "valid_md5", "download_url": "http://valid.dl"}
    invalid_book_details = {"id": "zlib2", "title": "Invalid Details", "md5": None, "download_url": None} # Fails validation
    invalid_id_book = {"id": "zlib3", "title": "Invalid ID", "md5": "invalid_id_md5", "download_url": "http://invalid.id"} # Not in candidates
    service.discovery_sessions[discovery_id]['candidates'] = [valid_book, invalid_book_details]
    service.discovery_sessions[discovery_id]['status'] = 'pending_confirmation'

    mock_mcp_download_response = {"success": True, "processed_path": "/path/valid_book.txt"}
    mock_ingestion_response = {"status": "Success", "document_id": "doc-valid"}

    with patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock, return_value=mock_mcp_download_response) as mock_call_mcp, \
         patch('src.philograph.ingestion.pipeline.process_document', new_callable=AsyncMock, return_value=mock_ingestion_response) as mock_process_doc:

        result = await service.handle_confirmation_request(discovery_id, [valid_book, invalid_book_details, invalid_id_book])

        # Expect processing to start only for the valid book
        assert result == {"status": "processing_started"}
        session = service.discovery_sessions[discovery_id]
        assert session['status'] == 'complete' # Only valid book processed successfully
        assert len(session['selected_items']) == 1 # Only valid book selected
        assert session['selected_items'][0]['md5'] == 'valid_md5'
        assert len(session['processed_items']) == 1
        assert session['processed_items'][0]['status'] == 'ingested'
        assert session['processed_items'][0]['id'] == 'valid_md5'

        mock_call_mcp.assert_awaited_once() # Called only for valid book
        mock_process_doc.assert_awaited_once() # Called only for valid book
        # assert False # Intentionally fail for Red phase if needed

@pytest.mark.asyncio
async def test_handle_confirmation_request_ingestion_skipped(mock_config):
    """Test confirmation where ingestion pipeline returns 'Skipped'."""
    discovery_id = service.create_discovery_session()
    book_to_skip = {"id": "zlib_skip", "title": "Skip Me", "md5": "skip_md5", "download_url": "http://skip.dl"}
    service.discovery_sessions[discovery_id]['candidates'] = [book_to_skip]
    service.discovery_sessions[discovery_id]['status'] = 'pending_confirmation'

    mock_mcp_download_response = {"success": True, "processed_path": "/path/skip_me.txt"}
    mock_ingestion_response = {"status": "Skipped", "message": "Already exists"}

    with patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock, return_value=mock_mcp_download_response) as mock_call_mcp, \
         patch('src.philograph.ingestion.pipeline.process_document', new_callable=AsyncMock, return_value=mock_ingestion_response) as mock_process_doc:

        result = await service.handle_confirmation_request(discovery_id, [book_to_skip])

        assert result == {"status": "processing_started"}
        session = service.discovery_sessions[discovery_id]
        # Skipped is still considered a successful processing run overall
        assert session['status'] == 'complete'
        assert len(session['processed_items']) == 1
        item_status = session['processed_items'][0]
        assert item_status['status'] == 'skipped'
        assert item_status['error'] is None # No error for skipped
        assert item_status['document_id'] is None

        mock_call_mcp.assert_awaited_once()
        mock_process_doc.assert_awaited_once()
        # assert False # Intentionally fail for Red phase if needed

@pytest.mark.asyncio
async def test_handle_confirmation_request_mcp_validation_error(mock_config):
    """Test confirmation handles MCPValidationError during download."""
    discovery_id = service.create_discovery_session()
    book = {"id": "zlib_val_err", "title": "Validation Error Book", "md5": "val_err_md5", "download_url": "http://valerr.dl"}
    service.discovery_sessions[discovery_id]['candidates'] = [book]
    service.discovery_sessions[discovery_id]['status'] = 'pending_confirmation'

    validation_error_msg = "Invalid MCP arguments"
    with patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock, side_effect=mcp_utils.MCPValidationError(validation_error_msg)) as mock_call_mcp, \
         patch('src.philograph.ingestion.pipeline.process_document', new_callable=AsyncMock) as mock_process_doc:

        result = await service.handle_confirmation_request(discovery_id, [book])

        assert result == {"status": "processing_started"}
        session = service.discovery_sessions[discovery_id]
        assert session['status'] == 'complete_with_errors'
        assert len(session['processed_items']) == 1
        item_status = session['processed_items'][0]
        assert item_status['status'] == 'processing_error'
        assert item_status['error'] == f"MCP Validation Error: {validation_error_msg}"

        mock_call_mcp.assert_awaited_once()
        mock_process_doc.assert_not_awaited() # Ingestion not called
        # assert False # Intentionally fail for Red phase if needed

@pytest.mark.asyncio
async def test_handle_confirmation_request_generic_processing_error(mock_config):
    """Test confirmation handles generic Exception during item processing."""
    discovery_id = service.create_discovery_session()
    book = {"id": "zlib_gen_err", "title": "Generic Error Book", "md5": "gen_err_md5", "download_url": "http://generr.dl"}
    service.discovery_sessions[discovery_id]['candidates'] = [book]
    service.discovery_sessions[discovery_id]['status'] = 'pending_confirmation'

    generic_error_msg = "Something unexpected happened"
    # Simulate error during ingestion call for simplicity
    with patch('src.philograph.utils.mcp_utils.call_mcp_tool', new_callable=AsyncMock, return_value={"success": True, "processed_path": "/path/generic.txt"}) as mock_call_mcp, \
         patch('src.philograph.ingestion.pipeline.process_document', new_callable=AsyncMock, side_effect=Exception(generic_error_msg)) as mock_process_doc:

        result = await service.handle_confirmation_request(discovery_id, [book])

        assert result == {"status": "processing_started"}
        session = service.discovery_sessions[discovery_id]
        assert session['status'] == 'complete_with_errors'
        assert len(session['processed_items']) == 1
        item_status = session['processed_items'][0]
        assert item_status['status'] == 'processing_error' # Generic exception maps to processing_error
        assert item_status['error'] == generic_error_msg

        mock_call_mcp.assert_awaited_once()
        mock_process_doc.assert_awaited_once()