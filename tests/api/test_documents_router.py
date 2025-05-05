import pytest
import psycopg
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi import status

# Assuming test_client fixture is available (e.g., in conftest.py)
# Import models used in responses/mocks
from src.philograph.data_access.models import Document

# --- Test Documents & Chunks Router ---

# --- Tests for /documents/{doc_id} ---

@pytest.mark.asyncio
# Patch the db_layer function as imported/used in the documents router
@patch("src.philograph.api.routers.documents.db_layer.get_document_by_id", new_callable=AsyncMock)
async def test_get_document_success(mock_get_doc: AsyncMock, test_client: AsyncClient):
    """
    Test GET /documents/{doc_id} returns 200 OK and document details for an existing ID.
    """
    # Arrange
    doc_id = 1
    mock_doc_data = {
        "id": doc_id,
        "title": "Found Document",
        "author": "Author C",
        "year": 2022,
        "source_path": "docs/found.txt",
        "metadata": {}
    }
    # Simulate the db_layer function returning a Pydantic model or dict
    mock_get_doc.return_value = Document(**mock_doc_data) # Return model instance

    # Act
    response = await test_client.get(f"/documents/{doc_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    # FastAPI automatically converts the Pydantic model to JSON
    assert response.json() == mock_doc_data
    mock_get_doc.assert_awaited_once()
    # Check the second argument passed to the mock (index 1), which should be doc_id
    assert mock_get_doc.await_args[0][1] == doc_id

@pytest.mark.asyncio
@patch("src.philograph.api.routers.documents.db_layer.get_document_by_id", new_callable=AsyncMock)
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
    mock_get_doc.assert_awaited_once()
    assert mock_get_doc.await_args[0][1] == doc_id

@pytest.mark.asyncio
@patch("src.philograph.api.routers.documents.db_layer.get_document_by_id", new_callable=AsyncMock)
async def test_get_document_db_error(mock_get_doc: AsyncMock, test_client: AsyncClient):
    """
    Test GET /documents/{doc_id} returns 500 Internal Server Error on database error.
    """
    # Arrange
    doc_id = 5
    error_message = "Simulated DB error"
    mock_get_doc.side_effect = psycopg.Error(error_message)

    # Act
    response = await test_client.get(f"/documents/{doc_id}")

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error retrieving document."}
    mock_get_doc.assert_awaited_once()
    assert mock_get_doc.await_args[0][1] == doc_id

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
    assert "detail" in response.json()
    assert response.json()["detail"][0]["type"] == "int_parsing"
    assert response.json()["detail"][0]["loc"] == ["path", "doc_id"]

# --- Tests for /documents/{doc_id}/references ---

@pytest.mark.asyncio
@patch('src.philograph.api.routers.documents.db_layer.get_document_by_id', new_callable=AsyncMock)
@patch('src.philograph.api.routers.documents.db_layer.get_relationships_for_document', new_callable=AsyncMock)
async def test_get_document_references_success(
    mock_get_relationships: AsyncMock,
    mock_get_doc: AsyncMock,
    test_client: AsyncClient
):
    """Tests successfully retrieving references for a document."""
    doc_id = 1
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
    assert response_data["references"][0]["id"] == 10
    assert response_data["references"][0]["source_node_id"] == "chunk:123"
    assert response_data["references"][0]["target_node_id"] == "doc:456"
    assert response_data["references"][0]["relation_type"] == "cites"
    assert response_data["references"][0]["metadata"] == {"text": "ref text 1"}

    mock_get_doc.assert_awaited_once()
    assert mock_get_doc.await_args[0][1] == doc_id
    mock_get_relationships.assert_awaited_once()
    assert mock_get_relationships.await_args[0][1] == doc_id

@pytest.mark.asyncio
@patch('src.philograph.api.routers.documents.db_layer.get_document_by_id', new_callable=AsyncMock)
@patch('src.philograph.api.routers.documents.db_layer.get_relationships_for_document', new_callable=AsyncMock)
async def test_get_document_references_not_found(
    mock_get_relationships: AsyncMock,
    mock_get_doc: AsyncMock,
    test_client: AsyncClient
):
    """Tests retrieving references for a non-existent document returns 404."""
    doc_id = 999
    mock_get_doc.return_value = None # Simulate document not found

    response = await test_client.get(f"/documents/{doc_id}/references")

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found."}
    mock_get_doc.assert_awaited_once()
    assert mock_get_doc.await_args[0][1] == doc_id
    mock_get_relationships.assert_not_awaited() # Should not be called if doc not found

@pytest.mark.asyncio
@patch('src.philograph.api.routers.documents.db_layer.get_document_by_id', new_callable=AsyncMock)
@patch('src.philograph.api.routers.documents.db_layer.get_relationships_for_document', new_callable=AsyncMock)
async def test_get_document_references_db_error(
    mock_get_relationships: AsyncMock,
    mock_get_doc: AsyncMock,
    test_client: AsyncClient
):
    """Tests that a DB error during relationship retrieval returns 500."""
    doc_id = 1
    mock_get_doc.return_value = Document(id=doc_id, title="Test Doc", source_path="/path/test.pdf", year=2023, author="Test Author")
    db_error = psycopg.Error("Simulated DB error")
    mock_get_relationships.side_effect = db_error

    response = await test_client.get(f"/documents/{doc_id}/references")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error retrieving document references."}
    mock_get_doc.assert_awaited_once()
    assert mock_get_doc.await_args[0][1] == doc_id
    mock_get_relationships.assert_awaited_once()
    assert mock_get_relationships.await_args[0][1] == doc_id

@pytest.mark.asyncio
@patch('src.philograph.api.routers.documents.db_layer.get_document_by_id', new_callable=AsyncMock)
@patch('src.philograph.api.routers.documents.db_layer.get_relationships_for_document', new_callable=AsyncMock)
async def test_get_document_references_empty(
    mock_get_relationships: AsyncMock,
    mock_get_doc: AsyncMock,
    test_client: AsyncClient
):
    """Tests retrieving references for a document with no references returns empty list."""
    doc_id = 2
    mock_get_doc.return_value = Document(id=doc_id, title="Test Doc 2", source_path="/path/test2.pdf", year=2024, author="Test Author 2")
    mock_get_relationships.return_value = [] # Simulate no relationships found

    response = await test_client.get(f"/documents/{doc_id}/references")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data == {"references": []}
    mock_get_doc.assert_awaited_once()
    assert mock_get_doc.await_args[0][1] == doc_id
    mock_get_relationships.assert_awaited_once()
    assert mock_get_relationships.await_args[0][1] == doc_id

# --- Tests for /chunks/{chunk_id} ---

@pytest.mark.asyncio
@patch('src.philograph.api.routers.documents.db_layer.get_chunk_by_id', new_callable=AsyncMock)
async def test_get_chunk_success(mock_get_chunk: AsyncMock, test_client: AsyncClient):
    """Tests successfully retrieving a chunk by ID."""
    chunk_id = 555
    expected_chunk_data = {
        "id": chunk_id,
        "section_id": 101,
        "text_content": "This is the chunk content.",
        "sequence": 1,
    }
    mock_get_chunk.return_value = expected_chunk_data

    response = await test_client.get(f"/chunks/{chunk_id}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == chunk_id
    assert response_data["section_id"] == expected_chunk_data["section_id"]
    assert response_data["text_content"] == expected_chunk_data["text_content"]
    assert response_data["sequence"] == expected_chunk_data["sequence"]
    mock_get_chunk.assert_awaited_once()
    assert mock_get_chunk.await_args[0][1] == chunk_id

@pytest.mark.asyncio
@patch('src.philograph.api.routers.documents.db_layer.get_chunk_by_id', new_callable=AsyncMock)
async def test_get_chunk_not_found(mock_get_chunk: AsyncMock, test_client: AsyncClient):
    """Tests retrieving a non-existent chunk returns 404."""
    chunk_id = 999
    mock_get_chunk.return_value = None # Simulate chunk not found

    response = await test_client.get(f"/chunks/{chunk_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Chunk not found."}
    mock_get_chunk.assert_awaited_once()
    assert mock_get_chunk.await_args[0][1] == chunk_id

@pytest.mark.asyncio
async def test_get_chunk_invalid_id_format(test_client: AsyncClient):
    """Tests retrieving a chunk with an invalid ID format returns 422."""
    invalid_chunk_id = "abc"

    response = await test_client.get(f"/chunks/{invalid_chunk_id}")

    assert response.status_code == 422
    assert "detail" in response.json()
    assert response.json()["detail"][0]["type"] == "int_parsing"
    assert response.json()["detail"][0]["loc"] == ["path", "chunk_id"]

@pytest.mark.asyncio
@patch('src.philograph.api.routers.documents.db_layer.get_chunk_by_id', new_callable=AsyncMock)
async def test_get_chunk_db_error(mock_get_chunk: AsyncMock, test_client: AsyncClient):
    """Tests that a DB error during chunk retrieval returns 500."""
    chunk_id = 777
    db_error = psycopg.Error("Simulated DB error")
    mock_get_chunk.side_effect = db_error

    response = await test_client.get(f"/chunks/{chunk_id}")

    assert response.status_code == 500
    assert response.json() == {"detail": "Error retrieving chunk."}
    mock_get_chunk.assert_awaited_once()
    assert mock_get_chunk.await_args[0][1] == chunk_id