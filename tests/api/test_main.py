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
        filters=None
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
        filters=expected_filters_dict
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
        filters=None
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
        filters=None
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
        filters=None
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
# --- /collections Endpoint Tests ---

@pytest.mark.asyncio
@patch("philograph.api.main.db_layer.add_collection", new_callable=AsyncMock)
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
    # Simulate the db layer returning an empty list for a non-existent ID
    # (We might need to adjust the API logic to check this and return 404)
    mock_get_items.return_value = []

    # Act
    response = await test_client.get(f"/collections/{collection_id}")

    # Assert
    # Current API logic returns 200 OK with empty list for non-existent collection
    # TODO: Update API logic to check if collection exists before returning items, then update test to expect 404
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"collection_id": collection_id, "items": []} # Match CollectionGetResponse
    mock_get_items.assert_awaited_once_with(ANY, collection_id)
# --- /acquire Endpoint Tests ---

@pytest.mark.asyncio
@patch("philograph.api.main.acquisition_service.initiate_acquisition", new_callable=AsyncMock)
async def test_acquire_success(mock_initiate_acquisition: AsyncMock, test_client: AsyncClient):
    """
    Test POST /acquire successfully initiates an acquisition and returns 202 Accepted.
    """
    # Arrange
    acquisition_id = "acq_12345"
    mock_initiate_acquisition.return_value = acquisition_id
    request_payload = {
        "query": "Test Book Title",
        "search_type": "book_meta", # Example, adjust based on actual model
        "download": True
    }

    # Act
    response = await test_client.post("/acquire", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_202_ACCEPTED
    expected_response = {
        "message": "Acquisition initiated.",
        "acquisition_id": acquisition_id
    }
    assert response.json() == expected_response
    mock_initiate_acquisition.assert_awaited_once_with(
        query=request_payload["query"],
        search_type=request_payload["search_type"],
        download=request_payload["download"]
    )
@pytest.mark.asyncio
async def test_acquire_missing_query(test_client: AsyncClient):
    """
    Test POST /acquire returns 422 Unprocessable Entity when 'query' is missing.
    """
    # Arrange
    request_payload = {
        # "query": "Missing this field",
        "search_type": "book_meta",
        "download": True
    }

    # Act
    response = await test_client.post("/acquire", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Optionally check detail for more specific error message
    # assert "'query'" in response.text
    # assert "Field required" in response.text
@pytest.mark.asyncio
@patch("philograph.api.main.acquisition_service.confirm_and_trigger_download", new_callable=AsyncMock)
async def test_acquire_confirm_success(mock_confirm: AsyncMock, test_client: AsyncClient):
    """
    Test POST /acquire/confirm successfully confirms and processes acquisition.
    """
    # Arrange
    acquisition_id = uuid.uuid4() # Use a valid UUID
    philo_doc_id = 789
    selected_book = {"title": "Confirmed Book", "zlib_id": "z1"} # Example details
    mock_confirm.return_value = {
        "status": "complete",
        "message": f"Acquisition and ingestion successful. PhiloGraph Doc ID: {philo_doc_id}",
        "document_id": philo_doc_id
    }
    # Ensure acquisition_id is not in the payload
    request_payload = {
        "selected_book_details": selected_book
    }

    # Act
    response = await test_client.post(f"/acquire/confirm/{acquisition_id}", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    expected_response = {
        "status": "complete",
        "message": f"Acquisition and ingestion successful. PhiloGraph Doc ID: {philo_doc_id}",
        "document_id": philo_doc_id,
        "status_url": None # Assuming status_url is None for immediate completion
    }
    assert response.json() == expected_response
    mock_confirm.assert_awaited_once_with(acquisition_id, selected_book)
@pytest.mark.asyncio
async def test_acquire_confirm_invalid_id(test_client: AsyncClient):
    """
    Test POST /acquire/confirm returns 422 Unprocessable Entity for an invalid UUID format.
    """
    # Arrange
    invalid_acquisition_id = "not-a-uuid"
    request_payload = {"confirmed": True} # Payload content doesn't matter for this validation

    # Act
    response = await test_client.post(f"/acquire/confirm/{invalid_acquisition_id}", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Check for FastAPI's specific validation error message structure
    response_data = response.json()
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)
    assert len(response_data["detail"]) > 0
    assert "type" in response_data["detail"][0]
    assert response_data["detail"][0]["type"] == "uuid_parsing"
    assert "loc" in response_data["detail"][0]
    assert response_data["detail"][0]["loc"] == ["path", "acquisition_id"]
@pytest.mark.asyncio
@patch("philograph.api.main.acquisition_service.confirm_and_trigger_download", new_callable=AsyncMock)
async def test_acquire_confirm_not_found(mock_confirm: AsyncMock, test_client: AsyncClient):
    """
    Test POST /acquire/confirm returns 404 Not Found when the acquisition ID is not found.
    """
    # Arrange
    valid_but_nonexistent_id = uuid.uuid4()
    error_message = f"Acquisition task {valid_but_nonexistent_id} not found."
    mock_confirm.side_effect = ValueError(error_message) # Simulate service raising error
    request_payload = {
        "confirmed": True,
        "selected_book_details": {"id": "book123", "title": "Test Book"} # Example details
    }

    # Act
    response = await test_client.post(f"/acquire/confirm/{valid_but_nonexistent_id}", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": error_message}
    mock_confirm.assert_awaited_once_with(valid_but_nonexistent_id, request_payload["selected_book_details"])

@pytest.mark.asyncio
@patch("philograph.api.main.acquisition_service.confirm_and_trigger_download", new_callable=AsyncMock)
async def test_acquire_confirm_service_runtime_error(mock_confirm: AsyncMock, test_client: AsyncClient):
    """
    Test POST /acquire/confirm returns 500 Internal Server Error on unexpected service error.
    """
    # Arrange
    acquisition_id = uuid.uuid4()
    error_message = "Unexpected error during download trigger."
    mock_confirm.side_effect = RuntimeError(error_message) # Simulate service raising generic error
    request_payload = {
        "confirmed": True,
        "selected_book_details": {"id": "book456", "title": "Another Book"}
    }

    # Act
    response = await test_client.post(f"/acquire/confirm/{acquisition_id}", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": f"Failed to confirm acquisition: {error_message}"}
    mock_confirm.assert_awaited_once_with(acquisition_id, request_payload["selected_book_details"])

# --- /acquire/status Endpoint Tests ---

@pytest.mark.asyncio
@patch("philograph.api.main.acquisition_service.get_acquisition_status", new_callable=AsyncMock)
async def test_get_acquisition_status_pending(mock_get_status: AsyncMock, test_client: AsyncClient):
    """
    Test GET /acquire/status/{id} returns 200 OK and 'pending' status.
    """
    # Arrange
    acquisition_id = uuid.uuid4()
    mock_status_data = {
        "status": "pending",
        "details": {"message": "Search initiated."},
        "selected_book": None,
        "error_message": None,
        "processed_path": None,
        "philo_doc_id": None
    }
    mock_get_status.return_value = mock_status_data

    # Act
    response = await test_client.get(f"/acquire/status/{acquisition_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    # Assuming the endpoint returns the dict directly or uses AcquisitionStatusResponse model
    assert response.json() == mock_status_data
    mock_get_status.assert_awaited_once_with(acquisition_id)
@pytest.mark.asyncio
@patch("philograph.api.main.acquisition_service.get_acquisition_status", new_callable=AsyncMock)
async def test_get_acquisition_status_completed(mock_get_status: AsyncMock, test_client: AsyncClient):
    """
    Test GET /acquire/status/{acquisition_id} returns 200 OK and status for a completed task.
    """
    # Arrange
    acquisition_id = uuid.uuid4()
    mock_status_data = {
        "status": "completed",
        "details": {"files_processed": 1, "errors": 0},
        "selected_book": None,
        "error_message": None,
        "processed_path": None,
        "philo_doc_id": None
    }
    mock_get_status.return_value = mock_status_data

    # Act
    response = await test_client.get(f"/acquire/status/{acquisition_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == mock_status_data
    mock_get_status.assert_awaited_once()
    assert mock_get_status.await_args.args[0] == acquisition_id # Check positional arg
@pytest.mark.asyncio
@patch("philograph.api.main.acquisition_service.get_acquisition_status", new_callable=AsyncMock)
async def test_get_acquisition_status_failed(mock_get_status: AsyncMock, test_client: AsyncClient):
    """
    Test GET /acquire/status/{acquisition_id} returns 200 OK and status for a failed task.
    """
    # Arrange
    acquisition_id = uuid.uuid4()
    mock_status_data = {
        "status": "failed",
        "details": None,
        "selected_book": {"title": "Failed Book"}, # Example book data
        "error_message": "Download timed out.",
        "processed_path": None,
        "philo_doc_id": None
    }
    mock_get_status.return_value = mock_status_data

    # Act
    response = await test_client.get(f"/acquire/status/{acquisition_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == mock_status_data
    mock_get_status.assert_awaited_once()
    assert mock_get_status.await_args.args[0] == acquisition_id

@pytest.mark.asyncio
@patch("philograph.api.main.acquisition_service.get_acquisition_status", new_callable=AsyncMock)
async def test_get_acquisition_status_not_found(mock_get_status: AsyncMock, test_client: AsyncClient):
    """
    Test GET /acquire/status/{acquisition_id} returns 404 Not Found for a non-existent ID.
    """
    # Arrange
    acquisition_id = uuid.uuid4()
    mock_get_status.return_value = None # Simulate service returning None for not found

    # Act
    response = await test_client.get(f"/acquire/status/{acquisition_id}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Acquisition ID not found."}
    mock_get_status.assert_awaited_once()
    assert mock_get_status.await_args.args[0] == acquisition_id

@pytest.mark.asyncio
async def test_get_acquisition_status_invalid_id_format(test_client: AsyncClient):
    """
    Test GET /acquire/status/{acquisition_id} returns 422 Unprocessable Entity for an invalid UUID format.
    """
    # Arrange
    invalid_id = "not-a-uuid"

    # Act
    response = await test_client.get(f"/acquire/status/{invalid_id}")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Check for Pydantic/FastAPI's validation error message structure
    assert '"type":"uuid_parsing"' in response.text # Check for specific error type