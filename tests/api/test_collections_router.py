import pytest
import psycopg
import uuid
from unittest.mock import AsyncMock, patch, ANY # Keep AsyncMock for patching async functions
# from httpx import AsyncClient # No longer needed
from fastapi import status
from fastapi.testclient import TestClient # Import TestClient

# Import the app
from src.philograph.api.main import app

# Remove module-level client instantiation

@pytest.fixture(scope="module") # Use module scope for efficiency if tests don't interfere
def client():
    with TestClient(app) as c:
        yield c

# --- Test Collections Router ---

# TestClient is synchronous, remove async decorators/keywords
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.add_collection", new_callable=AsyncMock)
def test_create_collection_success(mock_add_collection, client): # Correct: mock_add_collection is injected by @patch decorator
    """
    Test POST /collections creates a new collection and returns 201 Created.
    """
    # Arrange
    collection_name = "My New Collection"
    expected_collection_id = 5
    mock_add_collection.return_value = expected_collection_id
    request_payload = {"name": collection_name}

    # Act
    response = client.post("/collections", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    expected_response = {
        "message": "Collection created",
        "collection_id": expected_collection_id
    }
    assert response.json() == expected_response
    # The patched function is async, but called within sync TestClient context.
    # Mock assertion should still check await if original function was async.
    mock_add_collection.assert_awaited_once()
    # Check args passed to the mock (connection object is first arg)
    assert mock_add_collection.await_args[0][1] == collection_name # Use await_args

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
def test_create_collection_missing_name(client):
    """
    Test POST /collections returns 422 Unprocessable Entity when 'name' is missing.
    """
    # Arrange
    request_payload = {} # Missing 'name'

    # Act
    response = client.post("/collections", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.add_collection", new_callable=AsyncMock)
def test_create_collection_duplicate_name(mock_add_collection, client): # Correct: mock_add_collection is injected by @patch decorator
    """
    Test POST /collections returns 409 Conflict when collection name already exists.
    """
    # Arrange
    collection_name = "Existing Collection"
    mock_add_collection.side_effect = psycopg.errors.UniqueViolation("duplicate key value violates unique constraint")
    request_payload = {"name": collection_name}

    # Act
    response = client.post("/collections", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": f"Collection name '{collection_name}' already exists."}
    mock_add_collection.assert_awaited_once()

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.add_collection", new_callable=AsyncMock)
def test_create_collection_db_error(mock_add_collection, client): # Correct: mock_add_collection is injected by @patch decorator
    """
    Test POST /collections returns 500 Internal Server Error on database error.
    """
    # Arrange
    collection_name = "Collection with DB Error"
    error_message = "Simulated generic DB error during add"
    mock_add_collection.side_effect = psycopg.Error(error_message)
    request_payload = {"name": collection_name}

    # Act
    response = client.post("/collections", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error creating collection."}
    mock_add_collection.assert_awaited_once()

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.add_item_to_collection", new_callable=AsyncMock)
def test_add_collection_item_document_success(mock_add_item, client): # Correct: mock_add_item is injected by @patch decorator
    """
    Test POST /collections/{collection_id}/items successfully adds a document item.
    """
    # Arrange
    collection_id = uuid.uuid4()
    item_id = uuid.uuid4()
    item_type = "document"
    request_payload = {"item_type": item_type, "item_id": str(item_id)}
    mock_add_item.return_value = None

    # Act
    response = client.post(f"/collections/{collection_id}/items", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": f"{item_type.capitalize()} added to collection."}
    mock_add_item.assert_awaited_once_with(ANY, collection_id, item_type, item_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.add_item_to_collection", new_callable=AsyncMock)
def test_add_collection_item_chunk_success(mock_add_item, client): # Correct: mock_add_item is injected by @patch decorator
    """
    Test POST /collections/{collection_id}/items successfully adds a chunk item.
    """
    # Arrange
    collection_id = uuid.uuid4()
    item_id = uuid.uuid4()
    item_type = "chunk"
    request_payload = {"item_type": item_type, "item_id": str(item_id)}
    mock_add_item.return_value = None

    # Act
    response = client.post(f"/collections/{collection_id}/items", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": f"{item_type.capitalize()} added to collection."}
    mock_add_item.assert_awaited_once_with(ANY, collection_id, item_type, item_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
def test_add_collection_item_invalid_type(client):
    """
    Test POST /collections/{collection_id}/items returns 422 for invalid item_type.
    """
    # Arrange
    collection_id = uuid.uuid4() # Path param needs valid format
    item_id = uuid.uuid4()
    item_type = "invalid_type"
    request_payload = {"item_type": item_type, "item_id": str(item_id)}

    # Act
    response = client.post(f"/collections/{collection_id}/items", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "String should match pattern" in response.text

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.add_item_to_collection", new_callable=AsyncMock)
def test_add_collection_item_collection_not_found(mock_add_item, client): # Correct: mock_add_item is injected by @patch decorator
    """
    Test POST /collections/{collection_id}/items returns 404 when collection_id does not exist.
    """
    # Arrange
    collection_id = uuid.uuid4()
    item_id = uuid.uuid4()
    item_type = "document"
    request_payload = {"item_type": item_type, "item_id": str(item_id)}
    mock_add_item.side_effect = psycopg.errors.ForeignKeyViolation("FK violation on collections")

    # Act
    response = client.post(f"/collections/{collection_id}/items", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Collection or item not found."}
    mock_add_item.assert_awaited_once_with(ANY, collection_id, item_type, item_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.add_item_to_collection", new_callable=AsyncMock)
def test_add_collection_item_item_not_found(mock_add_item, client): # Correct: mock_add_item is injected by @patch decorator
    """
    Test POST /collections/{collection_id}/items returns 404 when item_id does not exist.
    """
    # Arrange
    collection_id = uuid.uuid4()
    item_id = uuid.uuid4() # Non-existent item ID
    item_type = "chunk"
    request_payload = {"item_type": item_type, "item_id": str(item_id)}
    mock_add_item.side_effect = psycopg.errors.ForeignKeyViolation("FK violation on chunks/documents")

    # Act
    response = client.post(f"/collections/{collection_id}/items", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Collection or item not found."}
    mock_add_item.assert_awaited_once_with(ANY, collection_id, item_type, item_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.add_item_to_collection", new_callable=AsyncMock)
def test_add_collection_item_duplicate_item(mock_add_item, client): # Correct: mock_add_item is injected by @patch decorator
    """
    Test POST /collections/{collection_id}/items returns 409 Conflict when adding the same item twice.
    """
    # Arrange
    collection_id = uuid.uuid4()
    item_id = uuid.uuid4()
    item_type = "document"
    request_payload = {"item_type": item_type, "item_id": str(item_id)}
    mock_add_item.side_effect = psycopg.errors.UniqueViolation("duplicate key")

    # Act
    response = client.post(f"/collections/{collection_id}/items", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"detail": f"{item_type.capitalize()} ID {item_id} already exists in collection ID {collection_id}."}
    mock_add_item.assert_awaited_once_with(ANY, collection_id, item_type, item_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
def test_add_collection_item_missing_fields(client):
    """
    Test POST /collections/{id}/items returns 422 when required fields are missing.
    """
    # Arrange
    collection_id = uuid.uuid4()
    request_payload = {"item_type": "document"} # Missing item_id

    # Act
    response = client.post(f"/collections/{collection_id}/items", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Field required" in response.text
    assert '"item_id"' in response.text

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.add_item_to_collection", new_callable=AsyncMock)
def test_add_collection_item_db_error(mock_add_item, client): # Correct: mock_add_item is injected by @patch decorator
    """
    Test POST /collections/{id}/items returns 500 when a database error occurs.
    """
    # Arrange
    collection_id = uuid.uuid4()
    item_id = uuid.uuid4()
    item_type = "document"
    request_payload = {"item_type": item_type, "item_id": str(item_id)}
    mock_add_item.side_effect = psycopg.Error("Simulated database error")

    # Act
    response = client.post(f"/collections/{collection_id}/items", json=request_payload) # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Database error adding item to collection."}
    mock_add_item.assert_awaited_once_with(ANY, collection_id, item_type, item_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.get_collection_items", new_callable=AsyncMock)
def test_get_collection_success(mock_get_items, client): # Correct: mock_get_items is injected by @patch decorator
    """
    Test GET /collections/{collection_id} returns 200 OK and items for an existing collection.
    """
    # Arrange
    collection_id = 123 # Use int as per router path param
    # Simulate db_layer returning list of tuples
    db_items = [("document", 456), ("chunk", 789)]
    mock_get_items.return_value = db_items
    # Expected response structure based on CollectionGetResponse model
    expected_response_items = [
        {"item_type": "document", "item_id": 456},
        {"item_type": "chunk", "item_id": 789}
    ]

    # Act
    response = client.get(f"/collections/{collection_id}") # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"collection_id": collection_id, "items": expected_response_items}
    mock_get_items.assert_awaited_once_with(ANY, collection_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.get_collection_items", new_callable=AsyncMock)
def test_get_collection_empty(mock_get_items, client): # Correct: mock_get_items is injected by @patch decorator
    """
    Test GET /collections/{collection_id} returns 200 OK and an empty list for an empty collection.
    """
    # Arrange
    collection_id = 124
    expected_items = []
    mock_get_items.return_value = expected_items

    # Act
    response = client.get(f"/collections/{collection_id}") # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"collection_id": collection_id, "items": expected_items}
    mock_get_items.assert_awaited_once_with(ANY, collection_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.get_collection_items", new_callable=AsyncMock)
def test_get_collection_not_found(mock_get_items, client): # Correct: mock_get_items is injected by @patch decorator
    """
    Test GET /collections/{collection_id} returns 404 Not Found for a non-existent collection ID.
    """
    # Arrange
    collection_id = 999
    mock_get_items.return_value = None # Simulate db layer returning None

    # Act
    response = client.get(f"/collections/{collection_id}") # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Collection not found."}
    mock_get_items.assert_awaited_once_with(ANY, collection_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.get_collection_items", new_callable=AsyncMock)
def test_get_collection_db_error(mock_get_items, client): # Correct: mock_get_items is injected by @patch decorator
    """Test GET /collections/{id} returns 500 Internal Server Error on database error."""
    # Arrange
    collection_id = 1
    mock_get_items.side_effect = psycopg.Error("Simulated DB connection error")

    # Act
    response = client.get(f"/collections/{collection_id}") # Use synchronous client

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Error retrieving collection."}
    mock_get_items.assert_awaited_once_with(ANY, collection_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.remove_item_from_collection", new_callable=AsyncMock)
@patch("src.philograph.api.routers.collections.db_layer.get_db_connection") # Patch connection used by router
def test_delete_collection_item_success(mock_get_conn, mock_remove_item, client): # Correct: mock_remove_item injected by @patch
    """Test successful deletion of an item from a collection."""
    mock_conn = AsyncMock()
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_remove_item.return_value = True
    collection_id = uuid.uuid4()
    item_type = "document"
    item_id = uuid.uuid4()

    response = client.delete(f"/collections/{collection_id}/items/{item_type}/{item_id}") # Use synchronous client

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_remove_item.assert_awaited_once_with(conn=mock_conn, collection_id=collection_id, item_type=item_type, item_id=item_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.remove_item_from_collection", new_callable=AsyncMock)
@patch("src.philograph.api.routers.collections.db_layer.get_db_connection")
def test_delete_collection_item_not_found(mock_get_conn, mock_remove_item, client): # Correct: mock_remove_item injected by @patch
    """Test deleting a non-existent item from a collection returns 404."""
    mock_conn = AsyncMock()
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_remove_item.return_value = False # Simulate item not found
    collection_id = uuid.uuid4()
    item_type = "document"
    item_id = uuid.uuid4()

    response = client.delete(f"/collections/{collection_id}/items/{item_type}/{item_id}") # Use synchronous client

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Item not found in collection or collection does not exist."}
    mock_remove_item.assert_awaited_once_with(conn=mock_conn, collection_id=collection_id, item_type=item_type, item_id=item_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.remove_item_from_collection", new_callable=AsyncMock)
@patch("src.philograph.api.routers.collections.db_layer.get_db_connection")
def test_delete_collection_item_db_error(mock_get_conn, mock_remove_item, client): # Correct: mock_remove_item injected by @patch
    """Test deleting an item returns 500 on database error."""
    mock_conn = AsyncMock()
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_remove_item.side_effect = psycopg.Error("Simulated DB error")
    collection_id = uuid.uuid4()
    item_type = "document"
    item_id = uuid.uuid4()

    response = client.delete(f"/collections/{collection_id}/items/{item_type}/{item_id}") # Use synchronous client

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Database error removing item from collection."}
    mock_remove_item.assert_awaited_once_with(conn=mock_conn, collection_id=collection_id, item_type=item_type, item_id=item_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.delete_collection", new_callable=AsyncMock)
@patch("src.philograph.api.routers.collections.db_layer.get_db_connection")
def test_delete_collection_success(mock_get_conn, mock_delete_collection, client): # Correct: mock_delete_collection injected by @patch
    """Test successful deletion of a collection returns 204."""
    mock_conn = AsyncMock()
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_delete_collection.return_value = True # Simulate successful deletion
    collection_id = uuid.uuid4()

    response = client.delete(f"/collections/{collection_id}") # Use synchronous client

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_delete_collection.assert_awaited_once_with(conn=mock_conn, collection_id=collection_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.delete_collection", new_callable=AsyncMock)
@patch("src.philograph.api.routers.collections.db_layer.get_db_connection")
def test_delete_collection_not_found(mock_get_conn, mock_delete_collection, client): # Correct: mock_delete_collection injected by @patch
    """Test deleting a non-existent collection returns 404."""
    mock_conn = AsyncMock()
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_delete_collection.return_value = False # Simulate collection not found
    collection_id = uuid.uuid4()

    response = client.delete(f"/collections/{collection_id}") # Use synchronous client

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Collection not found."}
    mock_delete_collection.assert_awaited_once_with(conn=mock_conn, collection_id=collection_id)

# Remove @pytest.mark.asyncio and async/await
# Add client fixture as argument
@patch("src.philograph.api.routers.collections.db_layer.delete_collection", new_callable=AsyncMock)
@patch("src.philograph.api.routers.collections.db_layer.get_db_connection")
def test_delete_collection_db_error(mock_get_conn, mock_delete_collection, client): # Correct: mock_delete_collection injected by @patch
    """Test deleting a collection returns 500 on database error."""
    mock_conn = AsyncMock()
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_delete_collection.side_effect = psycopg.Error("Simulated DB error")
    collection_id = uuid.uuid4()

    response = client.delete(f"/collections/{collection_id}") # Use synchronous client

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Database error deleting collection."}
    mock_delete_collection.assert_awaited_once_with(conn=mock_conn, collection_id=collection_id)