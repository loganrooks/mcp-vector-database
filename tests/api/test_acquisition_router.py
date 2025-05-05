import pytest
import uuid
import time
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi import status

# Assuming test_client fixture is available (e.g., in conftest.py)

# --- Test Acquisition Router ---

# --- POST /acquire/discover ---

@pytest.mark.asyncio
# Patch the service function as imported in the acquisition router
@patch("src.philograph.api.routers.acquisition.acquisition_service.handle_discovery_request", new_callable=AsyncMock)
async def test_acquire_discover_success(mock_handle_discovery: AsyncMock, test_client: AsyncClient):
    """Test POST /acquire/discover success with filters."""
    # Arrange
    filters = {"author": "Test Author"}
    discovery_id = uuid.uuid4()
    candidates = [{"id": "zlib1", "title": "Found Book"}]
    mock_handle_discovery.return_value = {
        "status": "success",
        "discovery_id": str(discovery_id),
        "candidates": candidates
    }
    request_payload = {"filters": filters}

    # Act
    response = await test_client.post("/acquire/discover", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "discovery_id": str(discovery_id),
        "candidates": candidates
    }
    mock_handle_discovery.assert_awaited_once_with(filters)

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.handle_discovery_request", new_callable=AsyncMock)
async def test_acquire_discover_no_candidates(mock_handle_discovery: AsyncMock, test_client: AsyncClient):
    """Test POST /acquire/discover when service finds no candidates."""
    # Arrange
    filters = {"title": "Obscure"}
    discovery_id = uuid.uuid4()
    mock_handle_discovery.return_value = {
        "status": "no_candidates",
        "discovery_id": str(discovery_id),
        "candidates": []
    }
    request_payload = {"filters": filters}

    # Act
    response = await test_client.post("/acquire/discover", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "discovery_id": str(discovery_id),
        "candidates": []
    }
    mock_handle_discovery.assert_awaited_once_with(filters)

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.handle_discovery_request", new_callable=AsyncMock)
async def test_acquire_discover_service_error(mock_handle_discovery: AsyncMock, test_client: AsyncClient):
    """Test POST /acquire/discover when acquisition service returns an error status."""
    # Arrange
    filters = {"title": "Error"}
    error_message = "MCP search failed"
    mock_handle_discovery.return_value = {
        "status": "error",
        "message": error_message
    }
    request_payload = {"filters": filters}

    # Act
    response = await test_client.post("/acquire/discover", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": error_message}
    mock_handle_discovery.assert_awaited_once_with(filters)

@pytest.mark.asyncio
async def test_acquire_discover_validation_error(test_client: AsyncClient):
    """Test POST /acquire/discover with invalid request body (e.g., missing filters)."""
    # Arrange
    request_payload = {} # Missing 'filters'

    # Act
    response = await test_client.post("/acquire/discover", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Field required" in response.text
    assert '"filters"' in response.text

# --- POST /acquire/confirm/{discovery_id} ---

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.handle_confirmation_request", new_callable=AsyncMock)
async def test_acquire_confirm_success(mock_handle_confirm: AsyncMock, test_client: AsyncClient):
    """Test POST /acquire/confirm/{discovery_id} success returns 202."""
    # Arrange
    discovery_id = uuid.uuid4()
    selected_items = [{"md5": "confirm_md5", "title": "Confirmed Book"}]
    mock_handle_confirm.return_value = {"status": "processing_started"}
    request_payload = {"selected_items": selected_items}

    # Act
    response = await test_client.post(f"/acquire/confirm/{discovery_id}", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_202_ACCEPTED
    expected_url_path = f"/acquire/status/{discovery_id}" # Relative path
    assert response.json() == {
        "message": "Acquisition confirmed. Download and processing initiated.",
        "status_url": expected_url_path
    }
    mock_handle_confirm.assert_awaited_once_with(str(discovery_id), selected_items)

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.handle_confirmation_request", new_callable=AsyncMock)
async def test_acquire_confirm_not_found(mock_handle_confirm: AsyncMock, test_client: AsyncClient):
    """Test POST /acquire/confirm/{discovery_id} with invalid/expired ID returns 404."""
    # Arrange
    discovery_id = uuid.uuid4()
    selected_items = [{"md5": "any_md5"}]
    error_message = "Discovery session not found or expired."
    mock_handle_confirm.return_value = {
        "status": "not_found",
        "message": error_message
    }
    request_payload = {"selected_items": selected_items}

    # Act
    response = await test_client.post(f"/acquire/confirm/{discovery_id}", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": error_message}
    mock_handle_confirm.assert_awaited_once_with(str(discovery_id), selected_items)

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.handle_confirmation_request", new_callable=AsyncMock)
async def test_acquire_confirm_invalid_state(mock_handle_confirm: AsyncMock, test_client: AsyncClient):
    """Test POST /acquire/confirm/{discovery_id} with discovery_id in invalid state returns 409."""
    # Arrange
    discovery_id = uuid.uuid4()
    selected_items = [{"md5": "any_md5"}]
    error_message = "Discovery session is not awaiting confirmation." # Match router message
    mock_handle_confirm.return_value = {
        "status": "invalid_state",
        "message": "Discovery session is not awaiting confirmation" # Service message might differ slightly
    }
    request_payload = {"selected_items": selected_items}

    # Act
    response = await test_client.post(f"/acquire/confirm/{discovery_id}", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": error_message}
    mock_handle_confirm.assert_awaited_once_with(str(discovery_id), selected_items)

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.handle_confirmation_request", new_callable=AsyncMock)
async def test_acquire_confirm_invalid_items(mock_handle_confirm: AsyncMock, test_client: AsyncClient):
    """Test POST /acquire/confirm/{discovery_id} with invalid selected items returns 400."""
    # Arrange
    discovery_id = uuid.uuid4()
    invalid_items = ["invalid_item_id_format"]
    error_message = "No valid items selected."
    error_details = "ID 'invalid_item_id_format' not found in candidates."
    mock_handle_confirm.return_value = {
        "status": "invalid_selection",
        "message": error_message,
        "details": error_details
    }
    request_payload = {"selected_items": invalid_items}

    # Act
    response = await test_client.post(f"/acquire/confirm/{discovery_id}", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": f"Invalid items selected: {error_details}"}
    mock_handle_confirm.assert_awaited_once_with(str(discovery_id), invalid_items)

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.handle_confirmation_request", new_callable=AsyncMock)
async def test_acquire_confirm_service_error(mock_handle_confirm: AsyncMock, test_client: AsyncClient):
    """Test POST /acquire/confirm/{discovery_id} when service returns an error status."""
    # Arrange
    discovery_id = uuid.uuid4()
    selected_items = [{"md5": "error_md5"}]
    error_message = "Download rate limit exceeded."
    mock_handle_confirm.return_value = {
        "status": "error",
        "message": error_message
    }
    request_payload = {"selected_items": selected_items}

    # Act
    response = await test_client.post(f"/acquire/confirm/{discovery_id}", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": error_message}
    mock_handle_confirm.assert_awaited_once_with(str(discovery_id), selected_items)

@pytest.mark.asyncio
async def test_acquire_confirm_validation_error(test_client: AsyncClient):
    """Test POST /acquire/confirm/{discovery_id} with invalid request body."""
    # Arrange
    discovery_id = uuid.uuid4()
    request_payload = {} # Missing 'selected_items'

    # Act
    response = await test_client.post(f"/acquire/confirm/{discovery_id}", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Field required" in response.text
    assert '"selected_items"' in response.text

# --- GET /acquire/status/{discovery_id} ---

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.get_status", new_callable=AsyncMock)
async def test_get_acquire_status_pending(mock_get_status: AsyncMock, test_client: AsyncClient):
    """Test GET /acquire/status/{discovery_id} for pending state."""
    # Arrange
    discovery_id = uuid.uuid4()
    mock_status_data = {
        "status": "pending_confirmation",
        "created_at": time.time(),
        "candidates": [{"id": "zlib1"}],
        "selected_items": None,
        "processed_items": None,
        "error_message": None
    }
    mock_get_status.return_value = mock_status_data

    # Act
    response = await test_client.get(f"/acquire/status/{discovery_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == mock_status_data
    mock_get_status.assert_awaited_once_with(str(discovery_id))

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.get_status", new_callable=AsyncMock)
async def test_get_acquire_status_processing(mock_get_status: AsyncMock, test_client: AsyncClient):
    """Test GET /acquire/status/{discovery_id} for processing state."""
    # Arrange
    discovery_id = uuid.uuid4()
    mock_status_data = {
        "status": "processing",
        "created_at": time.time(),
        "candidates": None,
        "selected_items": [{"md5": "md5_1"}],
        "processed_items": [{"id": "md5_1", "status": "downloading", "error": None}],
        "error_message": None
    }
    mock_get_status.return_value = mock_status_data

    # Act
    response = await test_client.get(f"/acquire/status/{discovery_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == mock_status_data
    mock_get_status.assert_awaited_once_with(str(discovery_id))

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.get_status", new_callable=AsyncMock)
async def test_get_acquire_status_complete(mock_get_status: AsyncMock, test_client: AsyncClient):
    """Test GET /acquire/status/{discovery_id} for complete state."""
    # Arrange
    discovery_id = uuid.uuid4()
    mock_status_data = {
        "status": "complete",
        "created_at": time.time(),
        "candidates": None,
        "selected_items": [{"md5": "md5_c"}],
        "processed_items": [{"id": "md5_c", "status": "ingested", "document_id": "doc_c", "error": None}],
        "error_message": None
    }
    mock_get_status.return_value = mock_status_data

    # Act
    response = await test_client.get(f"/acquire/status/{discovery_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == mock_status_data
    mock_get_status.assert_awaited_once_with(str(discovery_id))

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.get_status", new_callable=AsyncMock)
async def test_get_acquire_status_error(mock_get_status: AsyncMock, test_client: AsyncClient):
    """Test GET /acquire/status/{discovery_id} for error state."""
    # Arrange
    discovery_id = uuid.uuid4()
    error_msg = "Download failed"
    mock_status_data = {
        "status": "error",
        "created_at": time.time(),
        "candidates": None,
        "selected_items": [{"md5": "md5_e"}],
        "processed_items": [{"id": "md5_e", "status": "download_failed", "error": error_msg}],
        "error_message": error_msg
    }
    mock_get_status.return_value = mock_status_data

    # Act
    response = await test_client.get(f"/acquire/status/{discovery_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK # Still 200, body contains error status
    assert response.json() == mock_status_data
    mock_get_status.assert_awaited_once_with(str(discovery_id))

@pytest.mark.asyncio
@patch("src.philograph.api.routers.acquisition.acquisition_service.get_status", new_callable=AsyncMock)
async def test_get_acquire_status_not_found(mock_get_status: AsyncMock, test_client: AsyncClient):
    """Test GET /acquire/status/{discovery_id} with invalid ID returns 404."""
    # Arrange
    discovery_id = uuid.uuid4()
    mock_get_status.return_value = None # Service returns None for not found

    # Act
    response = await test_client.get(f"/acquire/status/{discovery_id}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Discovery session not found or expired."}
    mock_get_status.assert_awaited_once_with(str(discovery_id))

# Note: Tests for deprecated endpoints are omitted as they just raise 410 GONE