import pytest
import psycopg
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi import status

# Assuming test_client fixture is available (e.g., in conftest.py)
# Assuming config is available for default values if needed
from src.philograph import config

# --- Test Search Router ---

@pytest.mark.asyncio
# Adjust patch path to the search_service as imported in the router
@patch("src.philograph.api.routers.search.search_service.perform_search", new_callable=AsyncMock)
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
    mock_perform_search.assert_awaited_once_with(
        query_text="test query",
        top_k=config.SEARCH_TOP_K, # Use config default
        filters=None,
        offset=0
    )

@pytest.mark.asyncio
@patch("src.philograph.api.routers.search.search_service.perform_search", new_callable=AsyncMock)
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
        offset=0
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

@pytest.mark.asyncio
@patch("src.philograph.api.routers.search.search_service.perform_search", new_callable=AsyncMock)
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
    mock_perform_search.assert_awaited_once_with(
        query_text="query with no results",
        top_k=config.SEARCH_TOP_K, # Use config default
        filters=None,
        offset=0
    )

@pytest.mark.asyncio
@patch("src.philograph.api.routers.search.search_service.perform_search", new_callable=AsyncMock)
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
        top_k=config.SEARCH_TOP_K, # Use config default
        filters=None,
        offset=0
    )

@pytest.mark.asyncio
@patch("src.philograph.api.routers.search.search_service.perform_search", new_callable=AsyncMock)
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
        top_k=config.SEARCH_TOP_K, # Use config default
        filters=None,
        offset=0
    )

@pytest.mark.asyncio
@patch("src.philograph.api.routers.search.search_service.perform_search", new_callable=AsyncMock)
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
    mock_perform_search.assert_awaited_once_with(
        query_text="offset query",
        top_k=config.SEARCH_TOP_K, # Use config default
        filters=None,
        offset=5 # Check offset is passed
    )

@pytest.mark.asyncio
@patch("src.philograph.api.routers.search.search_service.perform_search", new_callable=AsyncMock)
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
    mock_perform_search.assert_awaited_once_with(
        query_text="limit query",
        top_k=3, # Check the specified limit
        filters=None,
        offset=0
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
    assert "detail" in response.json()
    error_details = response.json()["detail"][0]
    assert error_details["type"] == "greater_than_equal"
    assert error_details["loc"] == ["body", "offset"]
    assert "Input should be greater than or equal to 0" in error_details["msg"]

@pytest.mark.asyncio
@patch("src.philograph.api.routers.search.search_service.perform_search", new_callable=AsyncMock)
async def test_search_embedding_error(mock_perform_search: AsyncMock, test_client: AsyncClient):
    """
    Test POST /search returns 500 Internal Server Error when embedding generation fails.
    Simulate this by having the search service raise a specific exception.
    """
    # Arrange
    error_message = "Embedding generation failed unexpectedly"
    mock_perform_search.side_effect = RuntimeError(error_message)
    request_payload = {"query": "query causing embedding error"}

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": error_message}
    mock_perform_search.assert_awaited_once_with(
        query_text="query causing embedding error",
        top_k=config.SEARCH_TOP_K, # Use config default
        filters=None,
        offset=0
    )

@pytest.mark.asyncio
@patch("src.philograph.api.routers.search.search_service.perform_search", new_callable=AsyncMock)
async def test_search_db_error(mock_perform_search: AsyncMock, test_client: AsyncClient):
    """
    Test POST /search returns 500 Internal Server Error when the database search fails.
    Simulate this by having the search service raise a database error.
    """
    # Arrange
    db_error_message = "Database connection failed during search"
    mock_perform_search.side_effect = psycopg.Error(db_error_message)
    request_payload = {"query": "query causing db error"}

    # Act
    response = await test_client.post("/search", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    # The router's exception handler catches psycopg.Error specifically
    assert response.json() == {"detail": "Search failed due to unexpected database error"}
    mock_perform_search.assert_awaited_once_with(
        query_text="query causing db error",
        top_k=config.SEARCH_TOP_K, # Use config default
        filters=None,
        offset=0
    )