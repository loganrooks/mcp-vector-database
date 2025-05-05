import pytest
import psycopg
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Tuple

# Import functions from the new queries module
from src.philograph.data_access.queries import collections as coll_queries

# --- Mock Fixtures (Example - Define or import actual fixtures) ---
@pytest.fixture
def mock_get_conn(mocker):
    """Fixture to mock the get_db_connection context manager."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    mock_cm = mocker.patch('src.philograph.data_access.connection.get_db_connection')
    mock_cm.return_value.__aenter__.return_value = mock_conn
    return mock_conn, mock_cursor

# --- Test Collection Operations ---

@pytest.mark.asyncio
async def test_add_collection_success(mock_get_conn):
    """Tests successfully adding a new collection."""
    mock_conn, mock_cursor = mock_get_conn
    mock_cursor.fetchone.return_value = (1,) # Simulate returning ID tuple

    collection_name = "My Test Collection"
    expected_id = 1
    expected_sql = """
        INSERT INTO collections (name)
        VALUES (%s)
        RETURNING id;
    """
    expected_params = (collection_name,)

    returned_id = await coll_queries.add_collection(mock_conn, collection_name)

    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    # mock_conn.commit.assert_awaited_once() # Handled by context manager
    assert returned_id == expected_id

@pytest.mark.asyncio
async def test_add_collection_db_error(mock_get_conn):
    """Tests that add_collection propagates database errors."""
    mock_conn, mock_cursor = mock_get_conn
    collection_name = "Error Collection"
    db_error = psycopg.Error("Simulated DB error during collection insert")
    mock_cursor.execute.side_effect = db_error

    expected_sql = """
        INSERT INTO collections (name)
        VALUES (%s)
        RETURNING id;
    """
    expected_params = (collection_name,)

    with pytest.raises(psycopg.Error) as excinfo:
        await coll_queries.add_collection(mock_conn, collection_name)

    assert excinfo.value is db_error
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_not_awaited()
    # mock_conn.commit.assert_not_called()

@pytest.mark.asyncio
async def test_add_item_to_collection_document_success(mock_get_conn):
    """Tests successfully adding a document item to a collection."""
    mock_conn, mock_cursor = mock_get_conn
    mock_cursor.rowcount = 1

    collection_id = 1
    item_type = "document"
    item_id = 123
    expected_sql = """
        INSERT INTO collection_items (collection_id, item_type, item_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (collection_id, item_type, item_id) DO NOTHING;
    """
    expected_params = (collection_id, item_type, item_id)

    await coll_queries.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    # mock_conn.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_item_to_collection_chunk_success(mock_get_conn):
    """Tests successfully adding a chunk item to a collection."""
    mock_conn, mock_cursor = mock_get_conn
    mock_cursor.rowcount = 1

    collection_id = 2
    item_type = "chunk"
    item_id = 456
    expected_sql = """
        INSERT INTO collection_items (collection_id, item_type, item_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (collection_id, item_type, item_id) DO NOTHING;
    """
    expected_params = (collection_id, item_type, item_id)

    await coll_queries.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    # mock_conn.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_item_to_collection_invalid_collection_id(mock_get_conn):
    """Tests adding an item with an invalid collection_id raises IntegrityError."""
    mock_conn, mock_cursor = mock_get_conn
    collection_id = 999
    item_type = "document"
    item_id = 123
    mock_cursor.execute.side_effect = psycopg.IntegrityError("FK violation")

    with pytest.raises(psycopg.IntegrityError):
        await coll_queries.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    mock_cursor.execute.assert_awaited_once()
    # mock_conn.commit.assert_not_called()

# @pytest.mark.asyncio
# async def test_add_item_to_collection_invalid_item_type(mock_get_conn):
#     """Tests adding an item with an invalid item_type raises DB error."""
#     mock_conn, mock_cursor = mock_get_conn
#     collection_id = 1
#     item_type = "invalid_type"
#     item_id = 123
#     mock_cursor.execute.side_effect = psycopg.errors.CheckViolation("check constraint violated")
#
#     with pytest.raises(psycopg.errors.CheckViolation):
#          await coll_queries.add_item_to_collection(mock_conn, collection_id, item_type, item_id)
#
#     mock_conn.commit.assert_not_called()

@pytest.mark.asyncio
async def test_add_item_to_collection_db_error(mock_get_conn):
    """Tests that add_item_to_collection propagates database errors."""
    mock_conn, mock_cursor = mock_get_conn
    collection_id = 1
    item_type = "document"
    item_id = 123
    db_error = psycopg.Error("Simulated DB error")
    mock_cursor.execute.side_effect = db_error

    expected_sql = """
        INSERT INTO collection_items (collection_id, item_type, item_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (collection_id, item_type, item_id) DO NOTHING;
    """
    expected_params = (collection_id, item_type, item_id)

    with pytest.raises(psycopg.Error) as excinfo:
        await coll_queries.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    assert excinfo.value is db_error
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    # mock_conn.commit.assert_not_called()

@pytest.mark.asyncio
async def test_get_collection_items_success(mock_get_conn):
    """Tests retrieving items from a collection with multiple items."""
    mock_conn, mock_cursor = mock_get_conn
    collection_id = 1
    expected_items = [("document", 123), ("chunk", 456)]
    mock_cursor.fetchone.return_value = (True,) # Exists check
    mock_cursor.fetchall.return_value = expected_items # Item fetch

    expected_check_sql = "SELECT EXISTS (SELECT 1 FROM collections WHERE id = %s);"
    expected_items_sql = """
        SELECT item_type, item_id
        FROM collection_items
        WHERE collection_id = %s
        ORDER BY added_at;
    """
    expected_params = (collection_id,)

    items = await coll_queries.get_collection_items(mock_conn, collection_id)

    # Match exact SQL strings from source
    mock_cursor.execute.assert_any_await(expected_check_sql, expected_params)
    mock_cursor.execute.assert_any_await(expected_items_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_cursor.fetchall.assert_awaited_once()
    assert items == expected_items

@pytest.mark.asyncio
async def test_get_collection_items_empty(mock_get_conn):
    """Tests retrieving items from an empty collection."""
    mock_conn, mock_cursor = mock_get_conn
    collection_id = 2
    expected_items = []
    mock_cursor.fetchone.return_value = (True,) # Exists check
    mock_cursor.fetchall.return_value = expected_items # Item fetch

    expected_check_sql = "SELECT EXISTS (SELECT 1 FROM collections WHERE id = %s);"
    expected_items_sql = """
        SELECT item_type, item_id
        FROM collection_items
        WHERE collection_id = %s
        ORDER BY added_at;
    """
    expected_params = (collection_id,)

    items = await coll_queries.get_collection_items(mock_conn, collection_id)

    # Match exact SQL strings from source
    mock_cursor.execute.assert_any_await(expected_check_sql, expected_params)
    mock_cursor.execute.assert_any_await(expected_items_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_cursor.fetchall.assert_awaited_once()
    assert items == expected_items

@pytest.mark.asyncio
async def test_get_collection_items_non_existent_id(mock_get_conn):
    """Tests retrieving items for a non-existent collection ID returns None."""
    mock_conn, mock_cursor = mock_get_conn
    non_existent_collection_id = 999
    mock_cursor.fetchone.return_value = (False,) # Exists check fails

    expected_check_sql = "SELECT EXISTS (SELECT 1 FROM collections WHERE id = %s);"
    expected_params = (non_existent_collection_id,)

    items = await coll_queries.get_collection_items(mock_conn, non_existent_collection_id)

    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_check_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_cursor.fetchall.assert_not_awaited()
    assert items is None

@pytest.mark.asyncio
async def test_get_collection_items_db_error_on_check(mock_get_conn):
    """Tests DB error during the existence check."""
    mock_conn, mock_cursor = mock_get_conn
    collection_id = 105
    db_error = psycopg.Error("Simulated DB error during check")
    mock_cursor.execute.side_effect = db_error

    with pytest.raises(psycopg.Error) as excinfo:
        await coll_queries.get_collection_items(mock_conn, collection_id)

    assert excinfo.value is db_error
    expected_check_sql = "SELECT EXISTS (SELECT 1 FROM collections WHERE id = %s);"
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_check_sql, (collection_id,))
    mock_cursor.fetchone.assert_not_awaited()
    mock_cursor.fetchall.assert_not_awaited()

@pytest.mark.asyncio
async def test_get_collection_items_db_error_on_fetch(mock_get_conn):
    """Tests DB error during the item fetch."""
    mock_conn, mock_cursor = mock_get_conn
    collection_id = 105
    db_error = psycopg.Error("Simulated DB error during fetch")
    mock_cursor.fetchone.return_value = (True,) # Simulate collection exists
    # Simulate error on the second execute call (the fetch)
    mock_cursor.execute.side_effect = [None, db_error]

    with pytest.raises(psycopg.Error) as excinfo:
        await coll_queries.get_collection_items(mock_conn, collection_id)

    assert excinfo.value is db_error
    expected_check_sql = "SELECT EXISTS (SELECT 1 FROM collections WHERE id = %s);"
    expected_items_sql = """
        SELECT item_type, item_id
        FROM collection_items
        WHERE collection_id = %s
        ORDER BY added_at;
    """
    # Match exact SQL strings from source
    mock_cursor.execute.assert_any_await(expected_check_sql, (collection_id,))
    mock_cursor.execute.assert_any_await(expected_items_sql, (collection_id,))
    mock_cursor.fetchone.assert_awaited_once()
    mock_cursor.fetchall.assert_not_awaited()

@pytest.mark.asyncio
async def test_remove_item_from_collection_success(mock_get_conn):
    """Tests successfully removing an item from a collection."""
    mock_conn, mock_cursor = mock_get_conn
    collection_id = 1
    item_type = 'document'
    item_id = 123
    mock_cursor.rowcount = 1 # Simulate 1 row deleted

    expected_sql = """
        DELETE FROM collection_items
        WHERE collection_id = %s AND item_type = %s AND item_id = %s;
    """
    expected_params = (collection_id, item_type, item_id)

    removed = await coll_queries.remove_item_from_collection(mock_conn, collection_id, item_type, item_id)

    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    # mock_conn.commit.assert_awaited_once() # Handled by context manager
    assert removed is True

@pytest.mark.asyncio
async def test_remove_item_from_collection_not_found(mock_get_conn):
    """Tests removing a non-existent item from a collection returns False."""
    mock_conn, mock_cursor = mock_get_conn
    collection_id = 1
    item_type = 'document'
    item_id = 999
    mock_cursor.rowcount = 0 # Simulate 0 rows deleted

    expected_sql = """
        DELETE FROM collection_items
        WHERE collection_id = %s AND item_type = %s AND item_id = %s;
    """
    expected_params = (collection_id, item_type, item_id)

    removed = await coll_queries.remove_item_from_collection(mock_conn, collection_id, item_type, item_id)

    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    # mock_conn.commit.assert_awaited_once() # Handled by context manager
    assert removed is False

@pytest.mark.asyncio
async def test_delete_collection_success(mock_get_conn):
    """Tests successfully deleting a collection."""
    mock_conn, mock_cursor = mock_get_conn
    collection_id = 1
    mock_cursor.rowcount = 1 # Simulate 1 row deleted

    expected_sql = """
        DELETE FROM collections
        WHERE id = %s;
    """
    expected_params = (collection_id,)

    deleted = await coll_queries.delete_collection(mock_conn, collection_id)

    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    # mock_conn.commit.assert_awaited_once() # Handled by context manager
    assert deleted is True

@pytest.mark.asyncio
async def test_delete_collection_not_found(mock_get_conn):
    """Tests deleting a non-existent collection returns False."""
    mock_conn, mock_cursor = mock_get_conn
    collection_id = 999
    mock_cursor.rowcount = 0 # Simulate 0 rows deleted

    expected_sql = """
        DELETE FROM collections
        WHERE id = %s;
    """
    expected_params = (collection_id,)

    deleted = await coll_queries.delete_collection(mock_conn, collection_id)

    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    # mock_conn.commit.assert_awaited_once() # Handled by context manager
    assert deleted is False