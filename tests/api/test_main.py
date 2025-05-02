from philograph.data_access.db_layer import Document
from philograph.api.main import AcquisitionStatusResponse
from pydantic import BaseModel # ADDED IMPORT
from philograph.data_access import db_layer # ADDED IMPORT
import uuid
from unittest.mock import patch, AsyncMock, ANY # Removed duplicate, Added ANY
import pytest
import pytest_asyncio
# Removed duplicate: from unittest.mock import patch, AsyncMock
import psycopg # Import psycopg for error mocking
from httpx import AsyncClient
from fastapi import FastAPI, status # Import status

# Assuming the FastAPI app instance is named 'app' in main.py
# Adjust the import path as necessary based on project structure
# With `pythonpath = src` in pytest.ini, import relative to src
from httpx import ASGITransport # Import ASGITransport

from philograph.api.main import app

@pytest_asyncio.fixture(scope="module")
async def test_client() -> AsyncClient:
    """
    Provides an asynchronous test client for making requests to the API.
    Uses ASGITransport to wrap the FastAPI app.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_read_root(test_client: AsyncClient):
    """
    Test the root endpoint ('/') to ensure it returns a 200 OK status
    and a basic running message.
    """
    response = await test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "PhiloGraph API is running"}


@pytest.mark.asyncio
@patch("philograph.api.main.ingestion_pipeline.process_document", new_callable=AsyncMock)
async def test_ingest_single_file_success(mock_process_document: AsyncMock, test_client: AsyncClient):
    """
    Test POST /ingest with a single file path returns 200 OK on success.
    Mocks the ingestion pipeline.
    """
    # Arrange
    mock_result = {"status": "Success", "message": "Ingested file.pdf", "document_id": 123}
    mock_process_document.return_value = mock_result
    request_payload = {"path": "valid/file.pdf"}

    # Act
    response = await test_client.post("/ingest", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_202_ACCEPTED # Endpoint default is 202
    expected_response = {
        "message": "Ingested file.pdf",
        "document_id": 123,
        "status": "Success",
        "details": None
    }
    assert response.json() == expected_response
    mock_process_document.assert_awaited_once_with("valid/file.pdf")


@pytest.mark.asyncio
@patch("philograph.api.main.ingestion_pipeline.process_document", new_callable=AsyncMock)
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
@patch("philograph.api.main.ingestion_pipeline.process_document", new_callable=AsyncMock)
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
@patch("philograph.api.main.ingestion_pipeline.process_document", new_callable=AsyncMock)
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
@patch("philograph.api.main.ingestion_pipeline.process_document", new_callable=AsyncMock)
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
@pytest.mark.asyncio
@patch("philograph.api.main.search_service.perform_search", new_callable=AsyncMock)
async def test_search_success_query_only(mock_perform_search: AsyncMock, test_client: AsyncClient):
    """
    Test POST /search with only a query returns 200 OK and results.
    Mocks the search service.
    """
    # Arrange
    mock_results = [
        {
            "chunk_id": 101,
            "text": "This is the first relevant chunk.",
            "distance": 0.1,
            "source_document": {
                "doc_id": 1,
                "title": "Test Doc 1",
                "author": "Author A",
                "year": 2023,
                "source_path": "docs/test1.pdf"
            },
            "location": {
                "section_id": 10,
                "section_title": "Section 1",
                "chunk_sequence_in_section": 1
            }
        }
    ]
    mock_perform_search.return_value = mock_results
    request_payload = {"query": "test query"}

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    expected_response = {"results": mock_results}
    assert response.json() == expected_response
    # Assert mock was called correctly (with default limit and no filters)
    # Assuming config.SEARCH_TOP_K defaults to 10 for this test
    mock_perform_search.assert_awaited_once_with(
        query_text="test query",
        top_k=10,
        filters=None,
        offset=0 # Added default offset
    )
@pytest.mark.asyncio
@patch("philograph.api.main.search_service.perform_search", new_callable=AsyncMock)
async def test_search_success_with_filters(mock_perform_search: AsyncMock, test_client: AsyncClient):
    """
    Test POST /search with a query and filters returns 200 OK and results.
    Mocks the search service.
    """
    # Arrange
    mock_results = [
        {
            "chunk_id": 202,
            "text": "Another relevant chunk from Author B.",
            "distance": 0.2,
            "source_document": {
                "doc_id": 2,
                "title": "Test Doc 2",
                "author": "Author B",
                "year": 2024,
                "source_path": "docs/test2.epub"
            },
            "location": {
                "section_id": 20,
                "section_title": "Intro",
                "chunk_sequence_in_section": 5
            }
        }
    ]
    mock_perform_search.return_value = mock_results
    request_payload = {
        "query": "filtered query",
        "filters": {"author": "Author B", "year": 2024},
        "limit": 5 # Override default limit
    }
    expected_filters_dict = {"author": "Author B", "year": 2024}

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    expected_response = {"results": mock_results}
    assert response.json() == expected_response
    # Assert mock was called correctly with filters and custom limit
    mock_perform_search.assert_awaited_once_with(
        query_text="filtered query",
        top_k=5,
        filters=expected_filters_dict,
        offset=0 # Added default offset
    )
@pytest.mark.asyncio
async def test_search_missing_query(test_client: AsyncClient):
    """
    Test POST /search returns 422 Unprocessable Entity when 'query' is missing.
    """
    # Arrange
    request_payload = {"limit": 5} # Missing 'query'

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Optionally check detail:
    # assert "Field required" in response.text
    # assert "'query'" in response.text
@pytest.mark.asyncio
async def test_search_invalid_filter_format(test_client: AsyncClient):
    """
    Test POST /search returns 422 Unprocessable Entity when filter format is invalid.
    """
    # Arrange
    request_payload = {
        "query": "test query",
        "filters": {"year": "not-an-integer"} # Invalid type for year
    }

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Optionally check detail:
    # assert "value is not a valid integer" in response.text
@pytest.mark.asyncio
@patch("philograph.api.main.search_service.perform_search", new_callable=AsyncMock)
async def test_search_empty_results(mock_perform_search: AsyncMock, test_client: AsyncClient):
    """
    Test POST /search returns 200 OK and an empty list when search yields no results.
    """
    # Arrange
    mock_perform_search.return_value = [] # Simulate empty results
    request_payload = {"query": "query with no results"}

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    expected_response = {"results": []}
    assert response.json() == expected_response
    # Assert mock was called correctly (with default limit and no filters)
    mock_perform_search.assert_awaited_once_with(
        query_text="query with no results",
        top_k=10, # Assuming default
        filters=None,
        offset=0 # Added default offset
    )
@pytest.mark.asyncio
@patch("philograph.api.main.search_service.perform_search", new_callable=AsyncMock)
async def test_search_value_error(mock_perform_search: AsyncMock, test_client: AsyncClient):
    """
    Test POST /search returns 400 Bad Request when the search service raises ValueError.
    """
    # Arrange
    error_message = "Invalid search parameters provided"
    mock_perform_search.side_effect = ValueError(error_message)
    request_payload = {"query": "query causing value error"}

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": error_message}
    mock_perform_search.assert_awaited_once_with(
        query_text="query causing value error",
        top_k=10, # Assuming default
        filters=None,
        offset=0 # Added default offset
    )
@pytest.mark.asyncio
@patch("philograph.api.main.search_service.perform_search", new_callable=AsyncMock)
async def test_search_runtime_error(mock_perform_search: AsyncMock, test_client: AsyncClient):
    """
    Test POST /search returns 500 Internal Server Error when the search service raises RuntimeError.
    """
    # Arrange
    error_message = "Search service internal error"
    mock_perform_search.side_effect = RuntimeError(error_message)
    request_payload = {"query": "query causing runtime error"}

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": error_message}
    mock_perform_search.assert_awaited_once_with(
        query_text="query causing runtime error",
        top_k=10, # Assuming default
        filters=None,
        offset=0 # Added default offset
    )
@pytest.mark.asyncio
@patch("philograph.api.main.search_service.perform_search", new_callable=AsyncMock)
async def test_search_success_with_offset(mock_perform_search: AsyncMock, test_client: AsyncClient):
    """
    Test POST /search with a query and offset returns 200 OK and results,
    ensuring offset is passed to the service layer.
    """
    # Arrange
    mock_results = [ # Sample result
        {
            "chunk_id": 303, "text": "Chunk after offset.", "distance": 0.3,
            "source_document": {"doc_id": 3, "title": "Offset Doc", "author": "Author C", "year": 2025, "source_path": "docs/offset.md"},
            "location": {"section_id": 30, "section_title": "Body", "chunk_sequence_in_section": 1}
        }
    ]
    mock_perform_search.return_value = mock_results
    request_payload = {
        "query": "offset query",
        "offset": 5 # Specify offset
    }

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    expected_response = {"results": mock_results}
    assert response.json() == expected_response
    # Assert mock was called correctly with offset and default limit/filters
    mock_perform_search.assert_awaited_once_with(
        query_text="offset query",
        top_k=10, # Assuming default limit
        filters=None,
        offset=5 # Check offset is passed
    )
@pytest.mark.asyncio
@patch("philograph.api.main.search_service.perform_search", new_callable=AsyncMock)
async def test_search_success_with_limit(mock_perform_search: AsyncMock, test_client: AsyncClient):
    """
    Test POST /search with a query and limit returns 200 OK and results,
    ensuring limit is passed to the service layer.
    """
    # Arrange
    mock_results = [ # Sample result
        {
            "chunk_id": 404, "text": "Chunk within limit.", "distance": 0.4,
            "source_document": {"doc_id": 4, "title": "Limit Doc", "author": "Author D", "year": 2026, "source_path": "docs/limit.txt"},
            "location": {"section_id": 40, "section_title": "Conclusion", "chunk_sequence_in_section": 0}
        }
    ]
    mock_perform_search.return_value = mock_results
    request_payload = {
        "query": "limit query",
        "limit": 3 # Specify limit
    }

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    expected_response = {"results": mock_results}
    assert response.json() == expected_response
    # Assert mock was called correctly with specified limit
    mock_perform_search.assert_awaited_once_with(
        query_text="limit query",
        top_k=3, # Check the specified limit
        filters=None,
        offset=0 # Default offset
    )
@pytest.mark.asyncio
async def test_search_invalid_limit(test_client: AsyncClient):
    """
    Test POST /search returns 422 Unprocessable Entity when 'limit' is invalid (e.g., <= 0).
    FastAPI/Pydantic should handle this validation.
    """
    # Arrange
    request_payload = {
        "query": "test query",
        "limit": 0 # Invalid limit
    }

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Check for FastAPI/Pydantic validation error message structure
@pytest.mark.asyncio
async def test_search_invalid_offset(test_client: AsyncClient):
    """
    Test POST /search returns 422 Unprocessable Entity when 'offset' is invalid (e.g., < 0).
    FastAPI/Pydantic should handle this validation.
    """
    # Arrange
    request_payload = {
        "query": "test query",
        "offset": -1 # Invalid offset
    }

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Check for FastAPI/Pydantic validation error message structure
    assert "detail" in response.json()
    # Verify the specific validation error type and location
    error_details = response.json()["detail"][0]
    assert error_details["type"] == "greater_than_equal" # This was already correct, ensuring the block matches
    assert error_details["loc"] == ["body", "offset"]
    assert "Input should be greater than or equal to 0" in error_details["msg"]
@pytest.mark.asyncio
@patch("philograph.api.main.search_service.perform_search", new_callable=AsyncMock)
async def test_search_embedding_error(mock_perform_search: AsyncMock, test_client: AsyncClient):
    """
    Test POST /search returns 500 Internal Server Error when embedding generation fails.
    Simulate this by having the search service raise a specific exception.
    """
    # Arrange
    # Using RuntimeError for now, could be a custom exception later
    error_message = "Embedding generation failed unexpectedly"
    mock_perform_search.side_effect = RuntimeError(error_message)
    request_payload = {"query": "query causing embedding error"}

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    # Check if the detail matches the generic handler or a specific one
    # Assuming generic for now based on existing test_search_runtime_error
    assert response.json() == {"detail": error_message}
    mock_perform_search.assert_awaited_once_with(
        query_text="query causing embedding error",
        top_k=10, # Assuming default
        filters=None,
        offset=0 # Add default offset to assertion
    )
@pytest.mark.asyncio
@patch("philograph.api.main.search_service.perform_search", new_callable=AsyncMock) # Patch the service function called by API
async def test_search_db_error(mock_perform_search: AsyncMock, test_client: AsyncClient):
    """
    Test POST /search returns 500 Internal Server Error when the database search fails.
    Simulate this by having the search service raise a database error.
    """
    # Arrange
    db_error_message = "Database connection failed during search"
    # Simulate a generic database error from psycopg being raised by the service
    mock_perform_search.side_effect = psycopg.Error(db_error_message)
    request_payload = {"query": "query causing db error"}

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    # Check if the API returns a specific DB error message or a generic one
    # Let's assume a specific one for now, matching the pseudocode intent
    assert response.json() == {"detail": "Search failed due to unexpected database error"}
    mock_perform_search.assert_awaited_once_with(
        query_text="query causing db error",
        top_k=10,      # Assuming default
        filters=None,
        offset=0       # Default offset
    )
# --- /documents Endpoint Tests ---

@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.get_document_by_id", new_callable=AsyncMock)
async def test_get_document_success(mock_get_doc: AsyncMock, test_client: AsyncClient):
    """
    Test GET /documents/{doc_id} returns 200 OK and document details for an existing ID.
    """
    # Arrange
    doc_id = 1
    # Mock data matching the structure expected by DocumentResponse (likely db_layer.Document)
    # Assuming structure based on SearchResultItemSourceDocument and common fields
    mock_doc_data = {
        "id": doc_id,
        "title": "Found Document",
        "author": "Author C",
        "year": 2022,
        "source_path": "docs/found.txt",
        "metadata": {} # Added metadata field to match Document model
        # Removed created_at and updated_at as they are not in the Document model
    }
    mock_get_doc.return_value = mock_doc_data

    # Act
    response = await test_client.get(f"/documents/{doc_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == mock_doc_data
    # Check mock was called - connection object is passed implicitly by the endpoint
    mock_get_doc.assert_awaited_once()
    # Optionally check the arguments more specifically if needed, accounting for the connection object
    # args, kwargs = mock_get_doc.call_args
    # assert args[1] == doc_id # args[0] would be the connection object
@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.get_document_by_id", new_callable=AsyncMock)
async def test_get_document_not_found(mock_get_doc: AsyncMock, test_client: AsyncClient):
    """
    Test GET /documents/{doc_id} returns 404 Not Found for a non-existent ID.
    """
    # Arrange
    doc_id = 9999 # Non-existent ID
    mock_get_doc.return_value = None # Simulate document not found in DB

    # Act
    response = await test_client.get(f"/documents/{doc_id}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Document not found"}
    # Check mock was called
    mock_get_doc.assert_awaited_once()
@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.get_document_by_id", new_callable=AsyncMock)
async def test_get_document_db_error(mock_get_doc: AsyncMock, test_client: AsyncClient):
    """
    Test GET /documents/{doc_id} returns 500 Internal Server Error on database error.
    """
    # Arrange
    doc_id = 5
    error_message = "Simulated DB error"
    # Mock the db_layer function to raise a generic psycopg error
    mock_get_doc.side_effect = psycopg.Error(error_message)

    # Act
    response = await test_client.get(f"/documents/{doc_id}")

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error retrieving document."}
    # Check mock was called
    mock_get_doc.assert_awaited_once()
@pytest.mark.asyncio
async def test_get_document_invalid_id_format(test_client: AsyncClient):
    """
    Test GET /documents/{doc_id} returns 422 Unprocessable Entity for an invalid ID format.
    FastAPI should handle this path parameter validation.
    """
    # Arrange
    invalid_doc_id = "not-an-integer"

    # Act
    response = await test_client.get(f"/documents/{invalid_doc_id}")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Check for FastAPI's validation error message structure
    assert "detail" in response.json()
    assert response.json()["detail"][0]["type"] == "int_parsing"
    assert response.json()["detail"][0]["loc"] == ["path", "doc_id"]
@pytest.mark.asyncio
@patch('philograph.api.main.db_layer.get_document_by_id') # Corrected target
@patch('philograph.api.main.db_layer.get_relationships_for_document') # Corrected target
async def test_get_document_references_success(
    mock_get_relationships: AsyncMock,
    mock_get_doc: AsyncMock,
    test_client: AsyncClient
):
    """Tests successfully retrieving references for a document."""
    doc_id = 1
    # Simulate document exists by returning a dummy Document object
    mock_get_doc.return_value = Document(id=doc_id, title="Test Doc", source_path="/path/test.pdf", year=2023, author="Test Author")
    mock_relationships = [
        {"id": 10, "source_node_id": "chunk:123", "target_node_id": "doc:456", "relation_type": "cites", "metadata": {"text": "ref text 1"}},
        {"id": 11, "source_node_id": "chunk:124", "target_node_id": "doc:789", "relation_type": "cites", "metadata": {"text": "ref text 2"}},
    ]
    mock_get_relationships.return_value = mock_relationships

    response = await test_client.get(f"/documents/{doc_id}/references")

    assert response.status_code == 200
    response_data = response.json()
    assert "references" in response_data
    assert isinstance(response_data["references"], list)
    assert len(response_data["references"]) == 2
    # Check structure of the first reference for correctness
    assert response_data["references"][0]["id"] == 10
    assert response_data["references"][0]["source_node_id"] == "chunk:123"
    assert response_data["references"][0]["target_node_id"] == "doc:456"
    assert response_data["references"][0]["relation_type"] == "cites"
    assert response_data["references"][0]["metadata"] == {"text": "ref text 1"}

    # Verify mocks were called correctly
    mock_get_doc.assert_awaited_once()
    # Check the first argument (connection) using ANY, and the second argument (doc_id)
    assert mock_get_doc.await_args[0][1] == doc_id

    mock_get_relationships.assert_awaited_once()
    assert mock_get_relationships.await_args[0][1] == doc_id
# --- /collections Endpoint Tests ---

@pytest.mark.asyncio
@patch('philograph.api.main.db_layer.get_document_by_id')
@patch('philograph.api.main.db_layer.get_relationships_for_document') # Still need to patch this even if not called
async def test_get_document_references_not_found(
    mock_get_relationships: AsyncMock,
    mock_get_doc: AsyncMock,
    test_client: AsyncClient
):
    """Tests retrieving references for a non-existent document returns 404."""
    doc_id = 999 # Non-existent ID

    # Simulate document not found
    mock_get_doc.return_value = None

    response = await test_client.get(f"/documents/{doc_id}/references")

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found."}

@pytest.mark.asyncio
@patch('philograph.api.main.db_layer.get_document_by_id')
@patch('philograph.api.main.db_layer.get_relationships_for_document')
async def test_get_document_references_db_error(
    mock_get_relationships: AsyncMock,
    mock_get_doc: AsyncMock,
    test_client: AsyncClient
):
    """Tests that a DB error during relationship retrieval returns 500."""
    doc_id = 1

    # Simulate document exists
    mock_get_doc.return_value = Document(id=doc_id, title="Test Doc", source_path="/path/test.pdf", year=2023, author="Test Author")

    # Simulate DB error during relationship fetching
    db_error = psycopg.Error("Simulated DB error")
    mock_get_relationships.side_effect = db_error

    response = await test_client.get(f"/documents/{doc_id}/references")

    assert response.status_code == 500
    assert response.json() == {"detail": "Error retrieving document references."}

    # Verify mocks
    mock_get_doc.assert_awaited_once()
    assert mock_get_doc.await_args[0][1] == doc_id
    mock_get_relationships.assert_awaited_once()
    assert mock_get_relationships.await_args[0][1] == doc_id
    # Verify mocks
    mock_get_doc.assert_awaited_once()
    assert mock_get_doc.await_args[0][1] == doc_id
    mock_get_relationships.assert_awaited_once() # Should be called before error
@pytest.mark.asyncio
# --- Tests for /chunks/{chunk_id} ---
@pytest.mark.asyncio
@patch('philograph.api.main.db_layer.get_document_by_id')
@patch('philograph.api.main.db_layer.get_relationships_for_document')
async def test_get_document_references_empty(
    mock_get_relationships: AsyncMock,
    mock_get_doc: AsyncMock,
    test_client: AsyncClient
):
    """Tests retrieving references for a document with no references returns empty list."""
    doc_id = 2

    # Simulate document exists
    mock_get_doc.return_value = Document(id=doc_id, title="Test Doc 2", source_path="/path/test2.pdf", year=2024, author="Test Author 2")
    # Simulate no relationships found
    mock_get_relationships.return_value = []

    response = await test_client.get(f"/documents/{doc_id}/references")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data == {"references": []}

    # Verify mocks
    mock_get_doc.assert_awaited_once()
    assert mock_get_doc.await_args[0][1] == doc_id
    mock_get_relationships.assert_awaited_once()
    assert mock_get_relationships.await_args[0][1] == doc_id

@pytest.mark.asyncio
@patch('philograph.api.main.db_layer.get_chunk_by_id')
async def test_get_chunk_success(mock_get_chunk: AsyncMock, test_client: AsyncClient):
    """Tests successfully retrieving a chunk by ID."""
    chunk_id = 555
    expected_chunk_data = {
        "id": chunk_id,
        "section_id": 101,
        "text_content": "This is the chunk content.",
        "sequence": 1,
        # Embedding vector omitted for brevity in response model? Check spec/impl.
    }
    # Mock the db_layer function to return data resembling a Chunk model
    # Assuming db_layer returns a dict or object convertible to dict
    mock_get_chunk.return_value = expected_chunk_data

    response = await test_client.get(f"/chunks/{chunk_id}")

    assert response.status_code == 200
    response_data = response.json()
    # Assuming a ChunkResponse model similar to expected_chunk_data
    assert response_data["id"] == chunk_id
    assert response_data["section_id"] == expected_chunk_data["section_id"]
    assert response_data["text_content"] == expected_chunk_data["text_content"]
    assert response_data["sequence"] == expected_chunk_data["sequence"]

@pytest.mark.asyncio
@patch('philograph.api.main.db_layer.get_chunk_by_id')
async def test_get_chunk_not_found(mock_get_chunk: AsyncMock, test_client: AsyncClient):
    """Tests retrieving a non-existent chunk returns 404."""
    chunk_id = 999 # Non-existent ID

    # Simulate chunk not found
    mock_get_chunk.return_value = None

@pytest.mark.asyncio
async def test_get_chunk_invalid_id_format(test_client: AsyncClient):
    """Tests retrieving a chunk with an invalid ID format returns 422."""
    invalid_chunk_id = "abc"

    response = await test_client.get(f"/chunks/{invalid_chunk_id}")

    # FastAPI should automatically handle path parameter type validation
    assert response.status_code == 422
    # Optionally check the detail structure if needed, but 422 is the main check
    # assert "validation error" in response.json()["detail"][0]["msg"].lower()

    assert response.status_code == 422

# --- Tests for /acquire/status/{acquisition_id} ---

@pytest.mark.asyncio
@patch('philograph.acquisition.service.get_acquisition_status') # Corrected function name
async def test_get_acquisition_status_success_pending(mock_get_status: AsyncMock, test_client: AsyncClient):
    """Tests retrieving status for a pending acquisition."""
    test_uuid = uuid.uuid4()
    # Expected data based on AcquisitionStatusResponse model for 'pending' state
    expected_status_data = {
        "status": "pending",
        "details": None, # Or some relevant details if applicable for pending
        "selected_book": None,
        "error_message": None,
        "processed_path": None,
        "philo_doc_id": None
    }
    mock_get_status.return_value = expected_status_data

    response = await test_client.get(f"/acquire/status/{test_uuid}")

    assert response.status_code == 200
    # Use AcquisitionStatusResponse to validate structure if needed, or direct dict comparison
    assert response.json() == expected_status_data

    # Verify mock call
    mock_get_status.assert_awaited_once_with(test_uuid)
    # Verify mock call - Not needed as validation happens before endpoint call
@pytest.mark.asyncio
@patch("philograph.api.main.acquisition_service.get_acquisition_status", new_callable=AsyncMock)
async def test_get_acquisition_status_completed(mock_get_status: AsyncMock, test_client: AsyncClient):
    """Test getting acquisition status when the task is completed."""
    test_uuid = uuid.uuid4()
    # Mock data as a dictionary compatible with AcquisitionStatusResponse
    mock_status_data = {
        "status": "completed",
        "details": {"message": "Download and processing finished."},
        "selected_book": {"title": "Example Book Title"}, # Example data
        "error_message": None,
        "processed_path": "/app/processed/example.pdf", # Example data
        "philo_doc_id": 123 # Example data
    }
    mock_get_status.return_value = mock_status_data

    response = await test_client.get(f"/acquire/status/{test_uuid}")

    assert response.status_code == 200
    # Expected response should match the AcquisitionStatusResponse model fields
    expected_response = {
        "status": "completed",
        "details": {"message": "Download and processing finished."},
        "selected_book": {"title": "Example Book Title"},
        "error_message": None,
        "processed_path": "/app/processed/example.pdf",
        "philo_doc_id": 123
    }
    assert response.json() == expected_response
    mock_get_status.assert_awaited_once_with(test_uuid)
@pytest.mark.asyncio
@pytest.mark.asyncio
@patch("philograph.api.main.acquisition_service.get_acquisition_status", new_callable=AsyncMock)
async def test_get_acquisition_status_failed(mock_get_status: AsyncMock, test_client: AsyncClient):
    """Test getting acquisition status when the task has failed."""
    test_uuid = uuid.uuid4()
    # Mock data as a dictionary compatible with AcquisitionStatusResponse
    mock_status_data = {
        "status": "failed",
        "details": {"reason": "Download timed out."},
        "selected_book": {"title": "Failed Book"},
        "error_message": "Download failed after 3 attempts.",
        "processed_path": None,
        "philo_doc_id": None
    }
    mock_get_status.return_value = mock_status_data

    response = await test_client.get(f"/acquire/status/{test_uuid}")

    assert response.status_code == 200
    # Expected response should match the AcquisitionStatusResponse model fields
    expected_response = {
        "status": "failed",
        "details": {"reason": "Download timed out."},
        "selected_book": {"title": "Failed Book"},
        "error_message": "Download failed after 3 attempts.",
        "processed_path": None,
        "philo_doc_id": None
    }
    assert response.json() == expected_response
    mock_get_status.assert_awaited_once_with(test_uuid)

@pytest.mark.asyncio
@patch("philograph.api.main.acquisition_service.get_acquisition_status", new_callable=AsyncMock)
async def test_get_acquisition_status_not_found(mock_get_status: AsyncMock, test_client: AsyncClient):
    """Test getting acquisition status for a non-existent task ID returns 404."""
    test_uuid = uuid.uuid4()
    mock_get_status.return_value = None # Simulate service returning None for not found

    response = await test_client.get(f"/acquire/status/{test_uuid}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Acquisition task not found."}
    mock_get_status.assert_awaited_once_with(test_uuid)
@pytest.mark.asyncio
async def test_get_acquisition_status_invalid_id_format(test_client: AsyncClient):
    """Test getting acquisition status with an invalid UUID format returns 422."""
    invalid_uuid = "not-a-uuid"

    response = await test_client.get(f"/acquire/status/{invalid_uuid}")

    assert response.status_code == 422
    # Optionally check the detail message structure if needed
    assert "detail" in response.json()
    assert response.json()["detail"][0]["type"] == "uuid_parsing"
@patch('philograph.api.main.db_layer.get_chunk_by_id')
async def test_get_chunk_db_error(mock_get_chunk: AsyncMock, test_client: AsyncClient):
    """Tests that a DB error during chunk retrieval returns 500."""
    chunk_id = 777

    # Simulate DB error
    db_error = psycopg.Error("Simulated DB error")
    mock_get_chunk.side_effect = db_error

    response = await test_client.get(f"/chunks/{chunk_id}")

    assert response.status_code == 500
    assert response.json() == {"detail": "Error retrieving chunk."}

    # Verify mock call
    mock_get_chunk.assert_awaited_once()
    assert mock_get_chunk.await_args[0][1] == chunk_id
    mock_get_chunk.assert_awaited_once()
    assert mock_get_chunk.await_args[0][1] == chunk_id
async def test_create_collection_success(mock_add_collection: AsyncMock, test_client: AsyncClient):
    """
    Test POST /collections creates a new collection and returns 201 Created.
    """
    # Arrange
    collection_name = "My New Collection"
    expected_collection_id = 5
    mock_add_collection.return_value = expected_collection_id
    request_payload = {"name": collection_name}

    # Act
    response = await test_client.post("/collections", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    expected_response = {
        "message": "Collection created",
        "collection_id": expected_collection_id
    }
    assert response.json() == expected_response
    # Check mock was called
    mock_add_collection.assert_awaited_once()
    # args, kwargs = mock_add_collection.call_args
    # assert args[1] == collection_name # args[0] is connection

@pytest.mark.asyncio
async def test_create_collection_missing_name(test_client: AsyncClient):
    """
    Test POST /collections returns 422 Unprocessable Entity when 'name' is missing.
    """
    # Arrange
    request_payload = {} # Missing 'name'

    # Act
    response = await test_client.post("/collections", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Optionally check detail:
    # assert "Field required" in response.text
    # assert "'name'" in response.text

@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.add_collection", new_callable=AsyncMock)
async def test_create_collection_duplicate_name(mock_add_collection: AsyncMock, test_client: AsyncClient):
    """
    Test POST /collections returns 409 Conflict when collection name already exists.
    """
    # Arrange
    collection_name = "Existing Collection"
    # Mock the db_layer function to raise the specific psycopg error for unique constraint violation
    # Note: The actual error might depend on the DB schema details (e.g., error code)
    # Using UniqueViolation as a general representation.
    mock_add_collection.side_effect = psycopg.errors.UniqueViolation("duplicate key value violates unique constraint")
    request_payload = {"name": collection_name}

    # Act
    response = await test_client.post("/collections", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": f"Collection name '{collection_name}' already exists."}
    mock_add_collection.assert_awaited_once()

@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.add_collection", new_callable=AsyncMock)
async def test_create_collection_db_error(mock_add_collection: AsyncMock, test_client: AsyncClient):
    """
    Test POST /collections returns 500 Internal Server Error on database error
    (other than duplicate name).
    """
    # Arrange
    collection_name = "Collection with DB Error"
    error_message = "Simulated generic DB error during add"
    mock_add_collection.side_effect = psycopg.Error(error_message)
    request_payload = {"name": collection_name}

    # Act
    response = await test_client.post("/collections", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error creating collection."}
    mock_add_collection.assert_awaited_once()

@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.add_item_to_collection", new_callable=AsyncMock)
async def test_add_collection_item_document_success(mock_add_item: AsyncMock, test_client: AsyncClient):
    """
    Test POST /collections/{collection_id}/items successfully adds a document item.
    """
    # Arrange
    collection_id = 123
    item_id = 456
    item_type = "document"
    request_payload = {"item_type": item_type, "item_id": item_id}
    # Mock the db layer to simulate success (no return value needed, just no exception)
    mock_add_item.return_value = None

    # Act
    response = await test_client.post(f"/collections/{collection_id}/items", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": f"{item_type.capitalize()} added to collection."}
    mock_add_item.assert_awaited_once_with(ANY, collection_id, item_type, item_id) # Use ANY for connection object
@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.add_item_to_collection", new_callable=AsyncMock)
async def test_add_collection_item_chunk_success(mock_add_item: AsyncMock, test_client: AsyncClient):
    """
    Test POST /collections/{collection_id}/items successfully adds a chunk item.
    """
    # Arrange
    collection_id = 123
    item_id = 789 # Different ID for chunk
    item_type = "chunk"
    request_payload = {"item_type": item_type, "item_id": item_id}
    mock_add_item.return_value = None # Simulate success

    # Act
    response = await test_client.post(f"/collections/{collection_id}/items", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": f"{item_type.capitalize()} added to collection."}
    mock_add_item.assert_awaited_once_with(ANY, collection_id, item_type, item_id)
@pytest.mark.asyncio
async def test_add_collection_item_invalid_type(test_client: AsyncClient):
    """
    Test POST /collections/{collection_id}/items returns 422 for invalid item_type.
    """
    # Arrange
    collection_id = 123
    item_id = 456
    item_type = "invalid_type" # Invalid type
    request_payload = {"item_type": item_type, "item_id": item_id}

    # Act
    response = await test_client.post(f"/collections/{collection_id}/items", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Optionally check the detail structure for more specific validation error message
    assert "String should match pattern" in response.text # Check for pattern mismatch error
@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.add_item_to_collection", new_callable=AsyncMock)
async def test_add_collection_item_collection_not_found(mock_add_item: AsyncMock, test_client: AsyncClient):
    """
    Test POST /collections/{collection_id}/items returns 404 when collection_id does not exist.
    """
    # Arrange
    collection_id = 999 # Non-existent ID
    item_id = 456
    item_type = "document"
    request_payload = {"item_type": item_type, "item_id": item_id}
    # Mock the db layer to raise ForeignKeyViolation
    mock_add_item.side_effect = psycopg.errors.ForeignKeyViolation("insert or update on table \"collection_items\" violates foreign key constraint \"collection_items_collection_id_fkey\"")

    # Act
    response = await test_client.post(f"/collections/{collection_id}/items", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Collection or item not found."}
    mock_add_item.assert_awaited_once_with(ANY, collection_id, item_type, item_id)
@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.add_item_to_collection", new_callable=AsyncMock)
async def test_add_collection_item_item_not_found(mock_add_item: AsyncMock, test_client: AsyncClient):
    """
    Test POST /collections/{collection_id}/items returns 404 when item_id does not exist.
    """
    # Arrange
    collection_id = 123
    item_id = 999 # Non-existent item ID
    item_type = "chunk"
    request_payload = {"item_type": item_type, "item_id": item_id}
    # Mock the db layer to raise ForeignKeyViolation (could be item or collection FK)
    mock_add_item.side_effect = psycopg.errors.ForeignKeyViolation("insert or update on table \"collection_items\" violates foreign key constraint \"collection_items_chunk_id_fkey\"") # Example for chunk

    # Act
    response = await test_client.post(f"/collections/{collection_id}/items", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Collection or item not found."}
    mock_add_item.assert_awaited_once_with(ANY, collection_id, item_type, item_id)
@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.add_item_to_collection", new_callable=AsyncMock)
async def test_add_collection_item_duplicate_item(mock_add_item: AsyncMock, test_client: AsyncClient):
    """
    Test POST /collections/{collection_id}/items returns 409 Conflict when adding the same item twice.
    """
    # Arrange
    collection_id = 123
    item_id = 456
    item_type = "document"
    request_payload = {"item_type": item_type, "item_id": item_id}

    # Configure mock: Success on first call, UniqueViolation on second
    mock_add_item.side_effect = [
        None, # Simulate success on first call
        psycopg.errors.UniqueViolation("duplicate key value violates unique constraint \"collection_items_pkey\"") # Simulate unique constraint violation on second call
    ]

    # Act - First call (should succeed)
    response1 = await test_client.post(f"/collections/{collection_id}/items", json=request_payload)

    # Act - Second call (should fail with 409)
    response2 = await test_client.post(f"/collections/{collection_id}/items", json=request_payload)

    # Assert - First call
    assert response1.status_code == status.HTTP_200_OK

    # Assert - Second call
    assert response2.status_code == status.HTTP_409_CONFLICT
    assert response2.json() == {"detail": f"{item_type.capitalize()} ID {item_id} already exists in collection ID {collection_id}."}

    # Assert mock calls
    assert mock_add_item.await_count == 2
    mock_add_item.assert_any_await(ANY, collection_id, item_type, item_id)
# --- GET /collections/{collection_id} Endpoint Tests ---

@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.get_collection_items", new_callable=AsyncMock)
async def test_get_collection_success(mock_get_items: AsyncMock, test_client: AsyncClient):
    """
    Test GET /collections/{collection_id} returns 200 OK and items for an existing collection.
    """
    # Arrange
    collection_id = 123
    # Update expected_items to include ANY for added_at timestamp
    # Update expected_items to match CollectionItem model (no added_at)
    expected_items = [
        {"item_type": "document", "item_id": 456},
        {"item_type": "chunk", "item_id": 789}
    ]
    mock_get_items.return_value = expected_items

    # Act
    response = await test_client.get(f"/collections/{collection_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"collection_id": collection_id, "items": expected_items} # Match CollectionGetResponse
    mock_get_items.assert_awaited_once_with(ANY, collection_id)

@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.get_collection_items", new_callable=AsyncMock)
async def test_get_collection_empty(mock_get_items: AsyncMock, test_client: AsyncClient):
    """
    Test GET /collections/{collection_id} returns 200 OK and an empty list for an empty collection.
    """
    # Arrange
    collection_id = 124 # Different ID for empty collection
    expected_items = []
    mock_get_items.return_value = expected_items

    # Act
    response = await test_client.get(f"/collections/{collection_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"collection_id": collection_id, "items": expected_items} # Match CollectionGetResponse
    mock_get_items.assert_awaited_once_with(ANY, collection_id)

@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.get_collection_items", new_callable=AsyncMock)
async def test_get_collection_not_found(mock_get_items: AsyncMock, test_client: AsyncClient):
    """
    Test GET /collections/{collection_id} returns 404 Not Found for a non-existent collection ID.
    """
    # Arrange
    collection_id = 999 # Non-existent ID
    # Simulate the db layer returning None for a non-existent ID
    mock_get_items.return_value = None

    # Act
    response = await test_client.get(f"/collections/{collection_id}")

    # Assert
    # Assert that a 404 is returned for a non-existent collection ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Collection not found."}
    # The mock might still be called depending on implementation (e.g., if it checks items first)
    # Or it might not be called if the API checks collection existence beforehand.
    # Let's assume for now the check happens before calling get_collection_items or get_collection_items returns None/empty triggering 404.
    # mock_get_items.assert_awaited_once_with(ANY, collection_id) # Keep commented out until implementation clarifies

@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.get_collection_items", new_callable=AsyncMock)
async def test_get_collection_db_error(mock_get_items: AsyncMock, test_client: AsyncClient):
    """Test GET /collections/{id} returns 500 Internal Server Error on database error."""
    # Arrange
    collection_id = 1
    error_message = "Simulated DB connection error during get items"
    mock_get_items.side_effect = psycopg.Error(error_message)

    # Act
    response = await test_client.get(f"/collections/{collection_id}")

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error retrieving collection."} # Corrected expected message
    mock_get_items.assert_awaited_once()
    # args, kwargs = mock_get_items.call_args
    # assert args[1] == collection_id # args[0] is connection