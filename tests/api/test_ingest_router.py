import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi import status

# Assuming test_client fixture is available (e.g., in conftest.py)

# --- Test Ingest Router ---

@pytest.mark.asyncio
# Adjust patch path to the new location of process_document if it was moved,
# or keep patching where it's called from (e.g., the router file)
@patch("src.philograph.api.routers.ingest.ingestion_pipeline.process_document", new_callable=AsyncMock)
async def test_ingest_single_file_success(mock_process_document: AsyncMock, test_client: AsyncClient):
    """
    Test POST /ingest with a single file path returns 202 Accepted on success.
    Mocks the ingestion pipeline.
    """
    # Arrange
    mock_result = {"status": "Success", "message": "Ingested file.pdf", "document_id": 123}
    mock_process_document.return_value = mock_result
    request_payload = {"path": "valid/file.pdf"}

    # Act
    response = await test_client.post("/ingest", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_202_ACCEPTED
    expected_response = {
        "message": "Ingested file.pdf",
        "document_id": 123,
        "status": "Success",
        "details": None
    }
    # The router returns the model directly, check its JSON representation
    assert response.json() == expected_response
    mock_process_document.assert_awaited_once_with("valid/file.pdf")


@pytest.mark.asyncio
@patch("src.philograph.api.routers.ingest.ingestion_pipeline.process_document", new_callable=AsyncMock)
async def test_ingest_single_file_skipped(mock_process_document: AsyncMock, test_client: AsyncClient):
    """
    Test POST /ingest with a single file path returns 202 Accepted when skipped.
    Mocks the ingestion pipeline returning a 'Skipped' status.
    """
    # Arrange
    mock_result = {"status": "Skipped", "message": "Document already exists"}
    mock_process_document.return_value = mock_result
    request_payload = {"path": "existing/file.pdf"}

    # Act
    response = await test_client.post("/ingest", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_202_ACCEPTED
    expected_response = {
        "message": "Document already exists",
        "document_id": None, # No document_id when skipped
        "status": "Skipped",
        "details": None
    }
    assert response.json() == expected_response
    mock_process_document.assert_awaited_once_with("existing/file.pdf")

@pytest.mark.asyncio
@patch("src.philograph.api.routers.ingest.ingestion_pipeline.process_document", new_callable=AsyncMock)
async def test_ingest_directory_success(mock_process_document: AsyncMock, test_client: AsyncClient):
    """
    Test POST /ingest with a directory path returns 202 Accepted on success.
    Mocks the ingestion pipeline returning a 'Directory Processed' status.
    """
    # Arrange
    mock_result = {
        "status": "Directory Processed",
        "message": "Processed 2 files in directory.",
        "details": [
            {"path": "dir/file1.pdf", "status": "Success", "document_id": 1},
            {"path": "dir/file2.txt", "status": "Skipped"}
        ]
    }
    mock_process_document.return_value = mock_result
    request_payload = {"path": "valid/directory"}

    # Act
    response = await test_client.post("/ingest", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_202_ACCEPTED
    expected_response = {
        "message": "Processed 2 files in directory.",
        "document_id": None, # No single document_id for directory
        "status": "Directory Processed",
        "details": [
            {"path": "dir/file1.pdf", "status": "Success", "document_id": 1},
            {"path": "dir/file2.txt", "status": "Skipped"}
        ]
    }
    assert response.json() == expected_response
    mock_process_document.assert_awaited_once_with("valid/directory")

@pytest.mark.asyncio
@patch("src.philograph.api.routers.ingest.ingestion_pipeline.process_document", new_callable=AsyncMock)
async def test_ingest_pipeline_runtime_error(mock_process_document: AsyncMock, test_client: AsyncClient):
    """
    Test POST /ingest returns 500 Internal Server Error when the pipeline raises a RuntimeError.
    """
    # Arrange
    error_message = "Pipeline failed during embedding"
    mock_process_document.side_effect = RuntimeError(error_message)
    request_payload = {"path": "file/that/causes/error.pdf"}

    # Act
    response = await test_client.post("/ingest", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": error_message}
    mock_process_document.assert_awaited_once_with("file/that/causes/error.pdf")

@pytest.mark.asyncio
@patch("src.philograph.api.routers.ingest.ingestion_pipeline.process_document", new_callable=AsyncMock)
async def test_ingest_pipeline_value_error(mock_process_document: AsyncMock, test_client: AsyncClient):
    """
    Test POST /ingest returns 400 Bad Request when the pipeline raises a ValueError.
    """
    # Arrange
    error_message = "Invalid path provided"
    mock_process_document.side_effect = ValueError(error_message)
    request_payload = {"path": "invalid/path/!@#"}

    # Act
    response = await test_client.post("/ingest", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": error_message}
    mock_process_document.assert_awaited_once_with("invalid/path/!@#")

@pytest.mark.asyncio
async def test_ingest_missing_path(test_client: AsyncClient):
    """
    Test POST /ingest returns 422 Unprocessable Entity when 'path' is missing.
    """
    # Arrange
    request_payload = {} # Missing 'path'

    # Act
    response = await test_client.post("/ingest", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Optionally, assert details about the error message if needed
    # assert "Field required" in response.text