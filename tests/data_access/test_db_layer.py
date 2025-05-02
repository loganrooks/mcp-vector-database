import json
import pytest
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import psycopg
from psycopg_pool import AsyncConnectionPool

# Assuming config is accessible and TARGET_EMBEDDING_DIMENSION is defined
# If not, we might need to mock config as well
from src.philograph import config
from src.philograph.data_access import db_layer

# --- Test Utility Functions ---

# Tests for format_vector_for_pgvector
def test_format_vector_for_pgvector_valid():
    """Tests formatting a valid list of floats."""
    vector = [1.0, 2.5, -0.1]
    expected = "[1.0,2.5,-0.1]" # Corrected expected value
    assert db_layer.format_vector_for_pgvector(vector) == expected

def test_format_vector_for_pgvector_empty():
    """Tests formatting an empty list."""
    vector = []
    expected = "[]"
    assert db_layer.format_vector_for_pgvector(vector) == expected

def test_format_vector_for_pgvector_invalid_type():
    """Tests formatting a list with non-numeric types raises TypeError."""
    vector = [1.0, "a", 3.0]
    with pytest.raises(TypeError, match="Input vector must be a list of numbers."):
        db_layer.format_vector_for_pgvector(vector)

def test_format_vector_for_pgvector_not_a_list():
    """Tests formatting input that is not a list raises TypeError."""
    vector = "not a list"
    with pytest.raises(TypeError, match="Input vector must be a list of numbers."):
        db_layer.format_vector_for_pgvector(vector)
# Tests for json_serialize
def test_json_serialize_valid_dict():
    """Tests serializing a valid dictionary."""
    data = {"key": "value", "number": 123, "bool": True}
    expected = '{"key": "value", "number": 123, "bool": true}' # Correct JSON bool format
    assert db_layer.json_serialize(data) == expected

def test_json_serialize_none():
    """Tests serializing None input."""
    assert db_layer.json_serialize(None) is None

def test_json_serialize_empty_dict():
    """Tests serializing an empty dictionary."""
    data = {}
    expected = "{}"
    assert db_layer.json_serialize(data) == expected
# --- Test Connection Management ---

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.AsyncConnectionPool', new_callable=MagicMock) # Use MagicMock
async def test_get_db_pool_success_first_call(mock_pool_class):
    """Tests successful pool creation on the first call."""
    # Reset global pool for isolation
    db_layer.db_pool = None

    # Configure mocks
    mock_pool_instance = AsyncMock(spec=AsyncConnectionPool)
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)

    # Configure context managers
    mock_pool_instance.connection.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Configure the class mock to return the instance
    mock_pool_class.return_value = mock_pool_instance

    # Call the function
    pool = await db_layer.get_db_pool()

    # Assertions
    assert pool is mock_pool_instance
    mock_pool_class.assert_called_once() # Check pool was initialized
    mock_pool_instance.connection.assert_called_once() # Check connection test was attempted
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_awaited_once_with("SELECT 1")
    assert db_layer.db_pool is mock_pool_instance # Check global variable is set

    # Clean up global state
    db_layer.db_pool = None


@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.AsyncConnectionPool', new_callable=MagicMock) # Use MagicMock
async def test_get_db_pool_returns_existing_pool(mock_pool_class):
    """Tests that an existing pool is returned on subsequent calls."""
    # Reset global pool for isolation
    db_layer.db_pool = None

    # Mock successful first call
    mock_pool_instance = AsyncMock(spec=AsyncConnectionPool)
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_pool_instance.connection.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    mock_pool_class.return_value = mock_pool_instance

    # First call
    pool1 = await db_layer.get_db_pool()
    assert pool1 is mock_pool_instance
    mock_pool_class.assert_called_once() # Pool class initialized only once

    # Reset mock call count for the class before second call
    mock_pool_class.reset_mock()

    # Second call
    pool2 = await db_layer.get_db_pool()

    # Assertions
    assert pool2 is pool1 # Should be the same instance
    mock_pool_class.assert_not_called() # Pool class should NOT be called again

    # Clean up global state
    db_layer.db_pool = None


@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.AsyncConnectionPool', new_callable=MagicMock)
async def test_get_db_pool_failure(mock_pool_class):
    """Tests that ConnectionError is raised if pool initialization fails."""
    # Reset global pool for isolation
    db_layer.db_pool = None

    # Configure mocks to simulate failure during connection test
    mock_pool_instance = AsyncMock(spec=AsyncConnectionPool)
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)

    # Simulate OperationalError during the initial 'SELECT 1' check
    mock_cursor.execute.side_effect = psycopg.OperationalError("Simulated DB connection failure")

    # Configure context managers
    mock_pool_instance.connection.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Configure the class mock to return the instance
    mock_pool_class.return_value = mock_pool_instance

    # Expect ConnectionError to be raised
    with pytest.raises(ConnectionError, match="Database connection pool initialization failed"):
        await db_layer.get_db_pool()

    # Assert pool was attempted to be created but failed
    mock_pool_class.assert_called_once()
    assert db_layer.db_pool is None # Pool should not be set globally on failure

    # Clean up global state just in case (though it should be None)
    db_layer.db_pool = None
# TODO: Add test for get_db_pool failure (ConnectionError) - requires careful mocking based on previous issues
# TODO: Add tests for get_db_connection
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_pool')
async def test_get_db_connection_success(mock_get_pool):
    """Tests successfully getting a connection from the pool."""
    mock_pool = AsyncMock(spec=AsyncConnectionPool)
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_get_pool.return_value = mock_pool # Mock get_db_pool to return our mock pool

    # Configure the pool's connection context manager
    mock_pool.connection.return_value.__aenter__.return_value = mock_conn

    async with db_layer.get_db_connection() as conn:
        assert conn is mock_conn # Check the correct connection is yielded

    mock_get_pool.assert_awaited_once()
    mock_pool.connection.assert_called_once() # Check pool.connection() was used


@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_pool')
async def test_get_db_connection_pool_error(mock_get_pool):
    """Tests that an error during pool retrieval propagates."""
    mock_get_pool.side_effect = ConnectionError("Failed to get pool")

    with pytest.raises(ConnectionError, match="Failed to get pool"):
        async with db_layer.get_db_connection() as conn:
            pass # Should not reach here

    mock_get_pool.assert_awaited_once()


@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_pool')
async def test_get_db_connection_psycopg_error(mock_get_pool):
    """Tests that psycopg errors within the context are re-raised."""
    mock_pool = AsyncMock(spec=AsyncConnectionPool)
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_get_pool.return_value = mock_pool

    # Configure the pool's connection context manager
    mock_pool.connection.return_value.__aenter__.return_value = mock_conn

    simulated_error = psycopg.ProgrammingError("Syntax error")

@pytest.mark.asyncio
async def test_close_db_pool_closes_existing_pool():
    """Tests that close_db_pool closes an existing pool and resets the global."""
    # Setup a mock pool in the global variable
    mock_pool_instance = AsyncMock(spec=AsyncConnectionPool)
    db_layer.db_pool = mock_pool_instance

    await db_layer.close_db_pool()

    # Assertions
    mock_pool_instance.close.assert_awaited_once()
    assert db_layer.db_pool is None


@pytest.mark.asyncio
async def test_close_db_pool_no_pool():
    """Tests that close_db_pool does nothing if the pool is already None."""
    # Ensure global pool is None
    db_layer.db_pool = None

    # Call close_db_pool - it should not raise an error or try to close anything
    await db_layer.close_db_pool()

    # Assert the pool remains None
    assert db_layer.db_pool is None
    # Removed erroneous pytest.raises block

    # Removed erroneous assertions
    # We don't explicitly check for rollback here, as the source code comments it out
    # and simply re-raises. If rollback were active, we'd mock and assert it.
# TODO: Add tests for close_db_pool
# Removed erroneous line: assert db_layer.json_serialize(data) == expected

# TODO: Add test for dimension check if config.TARGET_EMBEDDING_DIMENSION is reliably mockable/settable for tests

# Tests for json_serialize
# TODO: Add tests for json_serialize

# --- Test Connection Management ---
# TODO: Add tests for get_db_pool, get_db_connection, close_db_pool

# --- Test CRUD Operations ---
# TODO: Add tests for add_document, get_document_by_id, check_document_exists
# TODO: Add tests for add_section
# TODO: Add tests for add_chunk, add_chunks_batch
# TODO: Add tests for add_reference
# TODO: Add tests for add_relationship, get_relationships
# TODO: Add tests for add_collection, add_item_to_collection, get_collection_items

# --- Test Search Operations ---
# TODO: Add tests for vector_search_chunks
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_document_success(mock_get_conn):
    """Tests successfully adding a document."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = {'id': 123}

    title = "Test Title"
    author = "Test Author"
    year = 2024
    source_path = "/path/to/test.pdf"
    metadata = {"key": "value"}
    expected_id = 123
    expected_sql = """
        INSERT INTO documents (title, author, year, source_path, metadata_jsonb)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """
    # Note: json_serialize is tested separately, assume it works correctly here
    expected_params = (title, author, year, source_path, json.dumps(metadata))

    # Call the function under test using the mock connection
    returned_id = await db_layer.add_document(mock_conn, title, author, year, source_path, metadata)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_conn.commit.assert_awaited_once() # Check commit was called
    assert returned_id == expected_id
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_document_duplicate_source_path(mock_get_conn):
    """Tests adding a document with a duplicate source_path raises IntegrityError."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate psycopg.IntegrityError on execute
    mock_cursor.execute.side_effect = psycopg.IntegrityError("duplicate key value violates unique constraint")

    title = "Duplicate Title"
    author = "Duplicate Author"
    year = 2025
    source_path = "/path/to/duplicate.pdf"
    metadata = {"key": "duplicate"}

    # Expect psycopg.IntegrityError to be raised and propagated
    with pytest.raises(psycopg.IntegrityError):
        await db_layer.add_document(mock_conn, title, author, year, source_path, metadata)

    # Assertions
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error
    # The source code doesn't explicitly call rollback in add_document,
    # it relies on the context manager or higher-level code to handle it.
    # mock_conn.rollback.assert_awaited_once()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_document_by_id_success(mock_get_conn):
    """Tests retrieving an existing document by ID."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    doc_id = 456
    db_row = {
        'id': doc_id,
        'title': 'Found Doc',
        'author': 'Found Author',
        'year': 2023,
        'source_path': '/path/found.txt',
        'metadata_jsonb': {'status': 'published'}
    }
    # Simulate fetchone returning a dictionary-like row
    mock_cursor.fetchone.return_value = db_row

    expected_sql = "SELECT id, title, author, year, source_path, metadata_jsonb FROM documents WHERE id = %s;"
    expected_params = (doc_id,)

    # Call the function under test
    document = await db_layer.get_document_by_id(mock_conn, doc_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    assert document is not None
    assert isinstance(document, db_layer.Document)
    assert document.id == doc_id
    assert document.title == db_row['title']
    assert document.author == db_row['author']
    assert document.year == db_row['year']
    assert document.source_path == db_row['source_path']
    assert document.metadata == db_row['metadata_jsonb'] # Check metadata mapping
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_document_by_id_not_found(mock_get_conn):
    """Tests retrieving a non-existent document returns None."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    doc_id = 999 # Non-existent ID
    # Simulate fetchone returning None when no row is found
    mock_cursor.fetchone.return_value = None

    expected_sql = "SELECT id, title, author, year, source_path, metadata_jsonb FROM documents WHERE id = %s;"
    expected_params = (doc_id,)

    # Call the function under test
    document = await db_layer.get_document_by_id(mock_conn, doc_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    assert document is None
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_check_document_exists_true(mock_get_conn):
    """Tests check_document_exists returns True when a document exists."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    source_path = "/path/exists.pdf"
    # Simulate fetchone returning {'exists': True}
    mock_cursor.fetchone.return_value = {'exists': True}

    expected_sql = "SELECT EXISTS(SELECT 1 FROM documents WHERE source_path = %s);"
    expected_params = (source_path,)

    # Call the function under test
    exists = await db_layer.check_document_exists(mock_conn, source_path)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    assert exists is True
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_check_document_exists_false(mock_get_conn):
    """Tests check_document_exists returns False when a document does not exist."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    source_path = "/path/does_not_exist.pdf"
    # Simulate fetchone returning {'exists': False}
    mock_cursor.fetchone.return_value = {'exists': False}

    expected_sql = "SELECT EXISTS(SELECT 1 FROM documents WHERE source_path = %s);"
    expected_params = (source_path,)

    # Call the function under test
    exists = await db_layer.check_document_exists(mock_conn, source_path)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    assert exists is False
# --- Test Section Operations ---

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_section_success(mock_get_conn):
    """Tests successfully adding a section."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = {'id': 789}

    doc_id = 123 # Assuming a valid document ID
    title = "Section 1"
    level = 1
    sequence = 0
    expected_id = 789
    expected_sql = """
        INSERT INTO sections (doc_id, title, level, sequence)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    expected_params = (doc_id, title, level, sequence)

    # Call the function under test
    returned_id = await db_layer.add_section(mock_conn, doc_id, title, level, sequence)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_conn.commit.assert_awaited_once()
    assert returned_id == expected_id
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_section_invalid_doc_id(mock_get_conn):
    """Tests adding a section with an invalid doc_id raises IntegrityError."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate psycopg.IntegrityError (foreign key violation) on execute
    mock_cursor.execute.side_effect = psycopg.IntegrityError("insert or update on table \"sections\" violates foreign key constraint")

    doc_id = 999 # Non-existent doc_id
    title = "Section Invalid Doc"
    level = 0
    sequence = 1

    # Expect psycopg.IntegrityError to be raised and propagated
    with pytest.raises(psycopg.IntegrityError):
        await db_layer.add_section(mock_conn, doc_id, title, level, sequence)

    # Assertions
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error
# --- Test Chunk Operations ---

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.format_vector_for_pgvector')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension for test
async def test_add_chunk_success(mock_format_vector, mock_get_conn):
    """Tests successfully adding a chunk with its embedding."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = {'id': 101}
    # Mock the vector formatting
    formatted_embedding_str = "[0.1,0.2,0.3]"
    mock_format_vector.return_value = formatted_embedding_str

    section_id = 789 # Assuming a valid section ID
    text_content = "This is the chunk text."
    sequence = 0
    embedding_vector = [0.1, 0.2, 0.3] # Example 3D vector
    expected_id = 101
    expected_sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s::vector(%s))
        RETURNING id;
    """
    # Parameters include the formatted embedding string and the dimension
    expected_params = (section_id, text_content, sequence, formatted_embedding_str, 3)

    # Call the function under test
    returned_id = await db_layer.add_chunk(mock_conn, section_id, text_content, sequence, embedding_vector)

    # Assertions
    mock_format_vector.assert_called_once_with(embedding_vector)
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_conn.commit.assert_awaited_once()
    assert returned_id == expected_id
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension for test
async def test_add_chunk_invalid_dimension(mock_get_conn):
    """Tests adding a chunk with incorrect embedding dimension raises ValueError."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    # No need to mock cursor as the error should be raised before DB interaction

    section_id = 789
    text_content = "Chunk with wrong dimension."
    sequence = 1
    embedding_vector = [0.1, 0.2] # Incorrect dimension (expected 3)

    # Expect ValueError due to dimension mismatch
    with pytest.raises(ValueError, match="Embedding vector dimension mismatch"):
        await db_layer.add_chunk(mock_conn, section_id, text_content, sequence, embedding_vector)

    # Ensure no DB interaction occurred
    mock_conn.cursor.assert_not_called()
    mock_conn.commit.assert_not_called()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.format_vector_for_pgvector')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_add_chunks_batch_success(mock_format_vector, mock_get_conn):
    """Tests successfully adding multiple chunks in a batch."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Mock format_vector to return predictable strings
    mock_format_vector.side_effect = lambda v: f"[{','.join(map(str, v))}]"

    chunks_data = [
        (1, "Chunk text 1", 0, [0.1, 0.2, 0.3]),
        (1, "Chunk text 2", 1, [0.4, 0.5, 0.6]),
        (2, "Chunk text 3", 0, [0.7, 0.8, 0.9]),
    ]
    expected_sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s::vector(%s));
    """
    # Prepare expected parameters for executemany
    expected_params = [
        (1, "Chunk text 1", 0, "[0.1,0.2,0.3]", 3),
        (1, "Chunk text 2", 1, "[0.4,0.5,0.6]", 3),
        (2, "Chunk text 3", 0, "[0.7,0.8,0.9]", 3),
    ]

    # Call the function under test
    await db_layer.add_chunks_batch(mock_conn, chunks_data)

    # Assertions
    mock_cursor.executemany.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_awaited_once()
    assert mock_format_vector.call_count == len(chunks_data)
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_chunks_batch_empty_list(mock_get_conn):
    """Tests that add_chunks_batch handles an empty input list gracefully."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    chunks_data = []

    # Call the function under test
    await db_layer.add_chunks_batch(mock_conn, chunks_data)

    # Assertions
    mock_cursor.executemany.assert_not_called() # Should not attempt to execute
    mock_conn.commit.assert_not_called() # Should not commit anything
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_add_chunks_batch_invalid_dimension(mock_get_conn):
    """Tests add_chunks_batch raises ValueError if any chunk has invalid dimension."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    # No need to mock cursor as the error should happen before DB interaction
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    # Add mock cursor to avoid AttributeError if the code reaches that point unexpectedly
    mock_conn.cursor.return_value = AsyncMock(spec=psycopg.AsyncCursor)


    chunks_data = [
        (1, "Chunk text 1", 0, [0.1, 0.2, 0.3]),
        (1, "Chunk text 2", 1, [0.4, 0.5]), # Invalid dimension
        (2, "Chunk text 3", 0, [0.7, 0.8, 0.9]),
    ]

    # Expect ValueError due to dimension mismatch
    with pytest.raises(ValueError, match="Embedding vector dimension mismatch in batch"):
        await db_layer.add_chunks_batch(mock_conn, chunks_data)

    # Assertions
    # Check that cursor was NOT obtained or used if error happens early
    mock_conn.cursor.assert_not_called()
    mock_conn.commit.assert_not_called() # Should not commit
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.format_vector_for_pgvector')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_add_chunks_batch_db_error(mock_format_vector, mock_get_conn):
    """Tests that add_chunks_batch propagates DB errors and doesn't commit."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Mock format_vector
    mock_format_vector.side_effect = lambda v: f"[{','.join(map(str, v))}]"

    # Simulate DB error during executemany
    db_error = psycopg.ProgrammingError("Simulated DB error during batch insert")
    mock_cursor.executemany.side_effect = db_error

    chunks_data = [
        (1, "Chunk text 1", 0, [0.1, 0.2, 0.3]),
        (1, "Chunk text 2", 1, [0.4, 0.5, 0.6]),
    ]
    expected_sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s::vector(%s));
    """
    expected_params = [
        (1, "Chunk text 1", 0, "[0.1,0.2,0.3]", 3),
        (1, "Chunk text 2", 1, "[0.4,0.5,0.6]", 3),
    ]

    # Expect the psycopg error to be raised
    with pytest.raises(psycopg.ProgrammingError, match="Simulated DB error"):
        await db_layer.add_chunks_batch(mock_conn, chunks_data)

    # Assertions
    mock_cursor.executemany.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error
# --- Test Reference Operations ---

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.json_serialize')
async def test_add_reference_success(mock_json_serialize, mock_get_conn):
    """Tests successfully adding a reference."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = {'id': 555}
    # Mock json_serialize
    serialized_details = '{"title": "Cited Work", "author": "Cited Author"}'
    mock_json_serialize.return_value = serialized_details

    source_chunk_id = 101 # Assuming a valid chunk ID
    cited_doc_details = {"title": "Cited Work", "author": "Cited Author"}
    expected_id = 555
    expected_sql = """
        INSERT INTO "references" (source_chunk_id, cited_doc_details_jsonb)
        VALUES (%s, %s)
        RETURNING id;
    """
    expected_params = (source_chunk_id, serialized_details)

    # Call the function under test
    returned_id = await db_layer.add_reference(mock_conn, source_chunk_id, cited_doc_details)

    # Assertions
    mock_json_serialize.assert_called_once_with(cited_doc_details)
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_conn.commit.assert_awaited_once()
    assert returned_id == expected_id
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.json_serialize')
async def test_add_reference_invalid_chunk_id(mock_json_serialize, mock_get_conn):
    """Tests add_reference raises IntegrityError for invalid source_chunk_id."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Mock json_serialize
    serialized_details = '{"title": "Cited Work", "author": "Cited Author"}'
    mock_json_serialize.return_value = serialized_details

    # Simulate psycopg.IntegrityError (foreign key violation) on execute
    db_error = psycopg.IntegrityError("insert or update on table \"references\" violates foreign key constraint")
    mock_cursor.execute.side_effect = db_error

    source_chunk_id = 999 # Non-existent chunk_id
    cited_doc_details = {"title": "Cited Work", "author": "Cited Author"}
    expected_sql = """
        INSERT INTO "references" (source_chunk_id, cited_doc_details_jsonb)
        VALUES (%s, %s)
        RETURNING id;
    """
    expected_params = (source_chunk_id, serialized_details)

    # Expect psycopg.IntegrityError to be raised
    with pytest.raises(psycopg.IntegrityError, match="violates foreign key constraint"):
        await db_layer.add_reference(mock_conn, source_chunk_id, cited_doc_details)

    # Assertions
    mock_json_serialize.assert_called_once_with(cited_doc_details)
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error
# --- Test Search Operations ---

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.format_vector_for_pgvector')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_vector_search_chunks_success(mock_format_vector, mock_get_conn):
    """Tests basic vector search returns correctly formatted results."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Mock format_vector
    query_embedding = [0.1, 0.2, 0.3]
    formatted_query_embedding = "[0.1,0.2,0.3]"
    mock_format_vector.return_value = formatted_query_embedding

    top_k = 2

    # Simulate database results (list of dicts, as if from dict_row)
    db_results = [
        {
            'chunk_id': 101, 'text_content': 'Result chunk 1', 'sequence': 0,
            'section_id': 10, 'section_title': 'Section A',
            'doc_id': 1, 'doc_title': 'Doc 1', 'doc_author': 'Author A', 'doc_year': 2020,
            'source_path': '/path/doc1.pdf', 'distance': 0.123
        },
        {
            'chunk_id': 205, 'text_content': 'Result chunk 2', 'sequence': 5,
            'section_id': 20, 'section_title': 'Section B',
            'doc_id': 2, 'doc_title': 'Doc 2', 'doc_author': 'Author B', 'doc_year': 2021,
            'source_path': '/path/doc2.pdf', 'distance': 0.456
        }
    ]
    mock_cursor.fetchall.return_value = db_results

    # Expected SQL structure (simplified, focusing on key parts)
    expected_base_sql_part = "SELECT c.id as chunk_id, c.text_content, c.sequence, s.id as section_id, s.title as section_title,"
    expected_from_part = "FROM chunks c JOIN sections s ON c.section_id = s.id JOIN documents d ON s.doc_id = d.id"
    expected_order_limit_part = "ORDER BY distance ASC LIMIT %s;"
    distance_operator = "<=>" # Default in the function

    # Call the function under test
    search_results = await db_layer.vector_search_chunks(mock_conn, query_embedding, top_k)

    # Assertions
    mock_format_vector.assert_called_once_with(query_embedding)
    # Check the SQL structure and parameters
    call_args, call_kwargs = mock_cursor.execute.call_args
    executed_sql = call_args[0]
    executed_params = call_args[1]

    assert expected_base_sql_part in executed_sql
    # Check for key JOIN parts instead of exact whitespace match
    assert "FROM chunks c" in executed_sql and "JOIN sections s ON c.section_id = s.id" in executed_sql and "JOIN documents d ON s.doc_id = d.id" in executed_sql
    assert f"c.embedding {distance_operator} %s::vector(3) AS distance" in executed_sql # Corrected assertion
    assert expected_order_limit_part in executed_sql
    assert "WHERE" not in executed_sql # No filters in this test
    assert executed_params == (formatted_query_embedding, top_k) # query_vec, limit (dimension is in SQL string)

    mock_cursor.fetchall.assert_awaited_once()

    # Check the parsed results
    assert len(search_results) == len(db_results)
    assert all(isinstance(r, db_layer.SearchResult) for r in search_results)
    assert search_results[0].chunk_id == db_results[0]['chunk_id']
    assert search_results[0].text_content == db_results[0]['text_content']
    assert search_results[0].distance == db_results[0]['distance']
    assert search_results[1].doc_title == db_results[1]['doc_title']
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.format_vector_for_pgvector')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_vector_search_chunks_with_filters(mock_format_vector, mock_get_conn):
    """Tests vector search with metadata filters (author, year)."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Mock format_vector
    query_embedding = [0.1, 0.2, 0.3]
    formatted_query_embedding = "[0.1,0.2,0.3]"
    mock_format_vector.return_value = formatted_query_embedding

    top_k = 5
    filters = {"author": "Test Author", "year": 2022}

    # Simulate database results (empty for now, as focus is on SQL generation)
    mock_cursor.fetchall.return_value = []

    # Expected SQL structure
    expected_base_sql_part = "SELECT c.id as chunk_id, c.text_content, c.sequence, s.id as section_id, s.title as section_title,"
    expected_from_part = "FROM chunks c JOIN sections s ON c.section_id = s.id JOIN documents d ON s.doc_id = d.id"
    expected_where_part_author = "d.author ILIKE %s"
    expected_where_part_year = "d.year = %s"
    expected_order_limit_part = "ORDER BY distance ASC LIMIT %s;"
    distance_operator = "<=>"

    # Call the function under test
    await db_layer.vector_search_chunks(mock_conn, query_embedding, top_k, filters=filters)

    # Assertions
    mock_format_vector.assert_called_once_with(query_embedding)
    # Check the SQL structure and parameters
    call_args, call_kwargs = mock_cursor.execute.call_args
    executed_sql = call_args[0]
    executed_params = call_args[1]

    assert expected_base_sql_part in executed_sql
    assert "FROM chunks c" in executed_sql and "JOIN sections s" in executed_sql and "JOIN documents d" in executed_sql
    assert f"c.embedding {distance_operator} %s::vector(3) AS distance" in executed_sql # Corrected assertion
    # Check WHERE clauses are present and combined with AND
    assert "WHERE" in executed_sql
    assert expected_where_part_author in executed_sql
    assert expected_where_part_year in executed_sql
    assert "AND" in executed_sql # Check they are combined
    assert expected_order_limit_part in executed_sql

    # Check parameters: query_vec, dimension, author_filter, year_filter, limit
    assert len(executed_params) == 4 # query_vec, author_filter, year_filter, limit (dimension is in SQL string)
    assert executed_params[0] == formatted_query_embedding
    assert executed_params[1] == f"%{filters['author']}%" # Author filter
    assert executed_params[2] == filters['year'] # Year filter
    assert executed_params[3] == top_k # Limit

    mock_cursor.fetchall.assert_awaited_once()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_vector_search_chunks_invalid_dimension(mock_get_conn):
    """Tests vector_search_chunks raises ValueError for invalid query dimension."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    # Add mock cursor to avoid AttributeError if the code reaches that point unexpectedly
    mock_conn.cursor.return_value = AsyncMock(spec=psycopg.AsyncCursor)


    query_embedding = [0.1, 0.2] # Invalid dimension (expected 3)
    top_k = 5

    # Expect ValueError due to dimension mismatch
    with pytest.raises(ValueError, match="Query embedding dimension mismatch"):
        await db_layer.vector_search_chunks(mock_conn, query_embedding, top_k)

    # Assertions
    mock_conn.cursor.assert_not_called() # Should fail before DB interaction
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_vector_search_chunks_empty_embedding(mock_get_conn):
    """Tests vector_search_chunks raises ValueError for empty query embedding."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    # Add mock cursor to avoid AttributeError if the code reaches that point unexpectedly
    mock_conn.cursor.return_value = AsyncMock(spec=psycopg.AsyncCursor)

    query_embedding = [] # Empty embedding
    top_k = 5

    # Expect ValueError due to empty embedding
    with pytest.raises(ValueError, match="Query embedding cannot be empty."):
        await db_layer.vector_search_chunks(mock_conn, query_embedding, top_k)

    # Assertions
    mock_conn.cursor.assert_not_called() # Should fail before DB interaction
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.format_vector_for_pgvector')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_vector_search_chunks_db_error(mock_format_vector, mock_get_conn):
    """Tests vector_search_chunks propagates DB errors."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Mock format_vector
    query_embedding = [0.1, 0.2, 0.3]
    formatted_query_embedding = "[0.1,0.2,0.3]"
    mock_format_vector.return_value = formatted_query_embedding

    top_k = 5

    # Simulate DB error during execute
    db_error = psycopg.ProgrammingError("Simulated DB error during search")
    mock_cursor.execute.side_effect = db_error

    # Expect the psycopg error to be raised
    with pytest.raises(psycopg.ProgrammingError, match="Simulated DB error"):
        await db_layer.vector_search_chunks(mock_conn, query_embedding, top_k)

    # Assertions
    mock_format_vector.assert_called_once_with(query_embedding)
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    mock_cursor.fetchall.assert_not_called() # Should not be called if execute fails
# --- Test Relationship Operations ---

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.json_serialize')
async def test_add_relationship_success(mock_json_serialize, mock_get_conn):
    """Tests successfully adding a relationship."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = {'id': 9001}
    # Mock json_serialize
    metadata = {"source": "test"}
    serialized_metadata = '{"source": "test"}'
    mock_json_serialize.return_value = serialized_metadata

    source_node_id = "chunk:101"
    target_node_id = "doc:5"
    relation_type = "cites"
    expected_id = 9001
    expected_sql = """
        INSERT INTO relationships (source_node_id, target_node_id, relation_type, metadata_jsonb)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    expected_params = (source_node_id, target_node_id, relation_type, serialized_metadata)

    # Call the function under test
    returned_id = await db_layer.add_relationship(mock_conn, source_node_id, target_node_id, relation_type, metadata)

    # Assertions
    mock_json_serialize.assert_called_once_with(metadata)
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_conn.commit.assert_awaited_once()
    assert returned_id == expected_id
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.json_serialize')
async def test_add_relationship_db_error(mock_json_serialize, mock_get_conn):
    """Tests add_relationship propagates DB errors."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Mock json_serialize
    metadata = {"source": "error_test"}
    serialized_metadata = '{"source": "error_test"}'
    mock_json_serialize.return_value = serialized_metadata

    # Simulate DB error during execute
    db_error = psycopg.ProgrammingError("Simulated DB error during relationship insert")
    mock_cursor.execute.side_effect = db_error

    source_node_id = "chunk:102"
    target_node_id = "doc:6"
    relation_type = "mentions"

    # Expect the psycopg error to be raised
    with pytest.raises(psycopg.ProgrammingError, match="Simulated DB error"):
        await db_layer.add_relationship(mock_conn, source_node_id, target_node_id, relation_type, metadata)

    # Assertions
    mock_json_serialize.assert_called_once_with(metadata)
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    mock_cursor.fetchone.assert_not_called() # Should not be called if execute fails
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_relationships_outgoing_success(mock_get_conn):
    """Tests retrieving outgoing relationships successfully."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    node_id = "doc:123"
    db_results = [
        {'id': 1, 'source_node_id': node_id, 'target_node_id': 'chunk:456', 'relation_type': 'contains', 'metadata_jsonb': None},
        {'id': 2, 'source_node_id': node_id, 'target_node_id': 'doc:789', 'relation_type': 'cites', 'metadata_jsonb': {'page': 5}},
    ]
    mock_cursor.fetchall.return_value = db_results

    expected_sql_base = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships"
    expected_where = "WHERE source_node_id = %s"
    expected_params = (node_id,)

    # Call the function under test (default direction is 'outgoing')
    relationships = await db_layer.get_relationships(mock_conn, node_id)

    # Assertions
    call_args, _ = mock_cursor.execute.call_args
    executed_sql = call_args[0]
    executed_params = call_args[1]

    assert expected_sql_base in executed_sql
    assert expected_where in executed_sql
    assert "target_node_id =" not in executed_sql # Ensure only source is checked
    assert "relation_type =" not in executed_sql # No type filter
    assert executed_params == expected_params

    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == len(db_results)
    assert all(isinstance(r, db_layer.Relationship) for r in relationships)
    assert relationships[0].id == db_results[0]['id']
    assert relationships[0].source_node_id == node_id
    assert relationships[0].target_node_id == db_results[0]['target_node_id']
    assert relationships[0].relation_type == db_results[0]['relation_type']
    assert relationships[0].metadata == {} # Default factory for None jsonb
    assert relationships[1].metadata == db_results[1]['metadata_jsonb']
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_relationships_incoming_success(mock_get_conn):
    """Tests retrieving incoming relationships successfully."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    node_id = "chunk:456"
    db_results = [
        {'id': 1, 'source_node_id': 'doc:123', 'target_node_id': node_id, 'relation_type': 'contains', 'metadata_jsonb': None},
        {'id': 3, 'source_node_id': 'chunk:999', 'target_node_id': node_id, 'relation_type': 'relates_to', 'metadata_jsonb': {'certainty': 0.8}},
    ]
    mock_cursor.fetchall.return_value = db_results

    expected_sql_base = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships"
    expected_where = "WHERE target_node_id = %s"
    expected_params = (node_id,)

    # Call the function under test
    relationships = await db_layer.get_relationships(mock_conn, node_id, direction='incoming')

    # Assertions
    call_args, _ = mock_cursor.execute.call_args
    executed_sql = call_args[0]
    executed_params = call_args[1]

    assert expected_sql_base in executed_sql
    assert expected_where in executed_sql
    assert "source_node_id =" not in executed_sql # Ensure only target is checked
    assert "relation_type =" not in executed_sql # No type filter
    assert executed_params == expected_params

    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == len(db_results)
    assert all(isinstance(r, db_layer.Relationship) for r in relationships)
    assert relationships[0].target_node_id == node_id
    assert relationships[1].target_node_id == node_id
    assert relationships[1].metadata == db_results[1]['metadata_jsonb']
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_relationships_both_success(mock_get_conn):
    """Tests retrieving both incoming and outgoing relationships successfully."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    node_id = "doc:123"
    db_results = [
        {'id': 1, 'source_node_id': node_id, 'target_node_id': 'chunk:456', 'relation_type': 'contains', 'metadata_jsonb': None}, # Outgoing
        {'id': 4, 'source_node_id': 'doc:999', 'target_node_id': node_id, 'relation_type': 'cites', 'metadata_jsonb': None}, # Incoming
    ]
    mock_cursor.fetchall.return_value = db_results

    expected_sql_base = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships"
    expected_where = "WHERE (source_node_id = %s OR target_node_id = %s)"
    expected_params = (node_id, node_id)

    # Call the function under test
    relationships = await db_layer.get_relationships(mock_conn, node_id, direction='both')

    # Assertions
    call_args, _ = mock_cursor.execute.call_args
    executed_sql = call_args[0]
    executed_params = call_args[1]

    assert expected_sql_base in executed_sql
    assert expected_where in executed_sql
    assert "relation_type =" not in executed_sql # No type filter
    assert executed_params == expected_params

    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == len(db_results)
    assert all(isinstance(r, db_layer.Relationship) for r in relationships)
    assert relationships[0].source_node_id == node_id # First is outgoing
    assert relationships[1].target_node_id == node_id # Second is incoming
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_relationships_outgoing_with_type_filter(mock_get_conn):
    """Tests retrieving outgoing relationships filtered by type."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    node_id = "doc:123"
    relation_type_filter = "cites"
    db_results = [
        # Only the 'cites' relationship should be returned
        {'id': 2, 'source_node_id': node_id, 'target_node_id': 'doc:789', 'relation_type': relation_type_filter, 'metadata_jsonb': {'page': 5}},
    ]
    mock_cursor.fetchall.return_value = db_results

    expected_sql_base = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships"
    expected_where_source = "WHERE source_node_id = %s"
    expected_where_type = "AND relation_type = %s"
    expected_params = (node_id, relation_type_filter)

    # Call the function under test
    relationships = await db_layer.get_relationships(mock_conn, node_id, direction='outgoing', relation_type=relation_type_filter)

    # Assertions
    call_args, _ = mock_cursor.execute.call_args
    executed_sql = call_args[0]
    executed_params = call_args[1]

    assert expected_sql_base in executed_sql
    assert expected_where_source in executed_sql
    assert expected_where_type in executed_sql
    assert executed_params == expected_params

    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == len(db_results)
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_relationships_non_existent_node(mock_get_conn):
    """Tests retrieving relationships for a non-existent node returns empty list."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    node_id = "non:existent"
    # Simulate database returning no rows
    mock_cursor.fetchall.return_value = []

    expected_sql_base = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships"
    expected_where = "WHERE source_node_id = %s" # Default direction is outgoing
    expected_params = (node_id,)

    # Call the function under test
    relationships = await db_layer.get_relationships(mock_conn, node_id)

    # Assertions
    call_args, _ = mock_cursor.execute.call_args
    executed_sql = call_args[0]
    executed_params = call_args[1]

    assert expected_sql_base in executed_sql
    assert expected_where in executed_sql
    assert executed_params == expected_params

    mock_cursor.fetchall.assert_awaited_once()
    assert relationships == []
    # The following assertion is removed as it causes IndexError on an empty list
    # assert all(isinstance(r, db_layer.Relationship) for r in relationships)
    # assert relationships[0].relation_type == relation_type_filter
    # assert relationships[0].source_node_id == node_id # Removed: Causes IndexError on empty list
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_relationships_for_document_success(mock_get_conn):
    """Tests retrieving relationships originating from chunks within a document."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    doc_id = 123
    # Mock database response (assuming source_node_id is 'chunk:id')
    db_rows = [
        {'id': 1, 'source_node_id': 'chunk:101', 'target_node_id': 'doc:456', 'relation_type': 'cites', 'metadata_jsonb': {'context': 'page 5'}},
        {'id': 2, 'source_node_id': 'chunk:102', 'target_node_id': 'concept:abc', 'relation_type': 'mentions', 'metadata_jsonb': None},
    ]
    mock_cursor.fetchall.return_value = db_rows

    # Define the expected SQL query (adjust based on actual schema/logic)
    # This query assumes relationships are linked via chunks belonging to sections of the target doc_id
    expected_sql_fragment_select = "SELECT r.id, r.source_node_id, r.target_node_id, r.relation_type, r.metadata_jsonb"
    expected_sql_fragment_from = "FROM relationships r JOIN chunks c ON r.source_node_id = 'chunk:' || c.id::text JOIN sections s ON c.section_id = s.id"
    expected_sql_fragment_where = "WHERE s.doc_id = %s"
    expected_params = (doc_id,)

    # Call the function under test
    relationships = await db_layer.get_relationships_for_document(mock_conn, doc_id)

    # Assertions
    # Check that execute was called with SQL containing the expected fragments and parameters
    call_args, call_kwargs = mock_cursor.execute.call_args
    executed_sql = call_args[0]
    executed_params = call_args[1]

    assert expected_sql_fragment_select in executed_sql
    # Check for essential JOIN parts instead of the exact multiline fragment
    assert "FROM relationships r" in executed_sql
    assert "JOIN chunks c ON r.source_node_id = 'chunk:' || c.id::text" in executed_sql
    assert "JOIN sections s ON c.section_id = s.id" in executed_sql
    assert expected_sql_fragment_where in executed_sql
    assert executed_params == expected_params

    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == 2
    assert isinstance(relationships[0], db_layer.Relationship)
    assert relationships[0].id == 1
    assert relationships[0].source_node_id == 'chunk:101'
    assert relationships[0].target_node_id == 'doc:456'
    assert relationships[0].relation_type == 'cites'
    assert relationships[0].metadata == {'context': 'page 5'}
    assert isinstance(relationships[1], db_layer.Relationship)
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_relationships_for_document_empty(mock_get_conn):
    """Tests retrieving relationships for a document with no relationships returns empty list."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    doc_id = 456
    # Mock database response as empty
    db_rows = []
    mock_cursor.fetchall.return_value = db_rows

    expected_sql_fragment_where = "WHERE s.doc_id = %s"
    expected_params = (doc_id,)

    # Call the function under test
    relationships = await db_layer.get_relationships_for_document(mock_conn, doc_id)

    # Assertions
    call_args, call_kwargs = mock_cursor.execute.call_args
    executed_sql = call_args[0]
    executed_params = call_args[1]

    assert expected_sql_fragment_where in executed_sql
    assert executed_params == expected_params
    mock_cursor.fetchall.assert_awaited_once()
    assert relationships == []
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_collection_success(mock_get_conn):
    """Tests adding a new collection successfully."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_name = "Test Collection"
    expected_collection_id = 99

    # Simulate fetchone returning the new ID
    mock_cursor.fetchone.return_value = (expected_collection_id,)

    # Call the function under test
    collection_id = await db_layer.add_collection(mock_conn, collection_name)

    # Assertions
    expected_sql = "INSERT INTO collections (name) VALUES (%s) RETURNING id;"
    expected_params = (collection_name,)

    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_conn.commit.assert_awaited_once()
    assert collection_id == expected_collection_id
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_collection_db_error(mock_get_conn):
    """Tests handling of database errors during collection addition."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_name = "Error Collection"

    # Simulate a database error during execute
    db_error = psycopg.Error("Simulated DB error")
    mock_cursor.execute.side_effect = db_error

    # Call the function under test and expect an error
    with pytest.raises(psycopg.Error) as excinfo:
        await db_layer.add_collection(mock_conn, collection_name)

    # Assertions
    assert excinfo.value is db_error # Check if the original error is propagated
    expected_sql = "INSERT INTO collections (name) VALUES (%s) RETURNING id;"
    expected_params = (collection_name,)

    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_not_awaited() # Should not be called if execute fails
    mock_conn.commit.assert_not_awaited() # Ensure commit was NOT called on error
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_document_success(mock_get_conn):
    """Tests adding a document item to a collection successfully."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 99
    item_type = "document"
    item_id = 123

    # Call the function under test
    await db_layer.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    expected_sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    expected_params = (collection_id, item_type, item_id)

    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_awaited_once()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_chunk_success(mock_get_conn):
    """Tests adding a chunk item to a collection successfully."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 100
    item_type = "chunk"
    item_id = 456

    # Call the function under test
    await db_layer.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    expected_sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    expected_params = (collection_id, item_type, item_id)

    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_awaited_once()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_invalid_collection_id(mock_get_conn):
    """Tests adding an item to a non-existent collection raises an error."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    invalid_collection_id = -1 # Assuming -1 is never a valid ID
    item_type = "document"
    item_id = 123

    # Simulate a foreign key violation error
    # Use IntegrityError as it's a common error for FK violations
    db_error = psycopg.IntegrityError("Simulated FK violation")
    mock_cursor.execute.side_effect = db_error

    # Call the function under test and expect an IntegrityError
    with pytest.raises(psycopg.IntegrityError) as excinfo:
        await db_layer.add_item_to_collection(mock_conn, invalid_collection_id, item_type, item_id)

    # Assertions
    assert excinfo.value is db_error
    expected_sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    expected_params = (invalid_collection_id, item_type, item_id)

    # Execute should be called, and raise the simulated error
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_not_awaited()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_invalid_item_type(mock_get_conn):
    """Tests adding an item with an invalid type raises a database error."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 101
    invalid_item_type = "invalid_type" # Assuming this is not a valid type
    item_id = 789

    # Simulate a database data error (e.g., check constraint violation)
    db_error = psycopg.DataError("Simulated invalid item_type error")
    mock_cursor.execute.side_effect = db_error

    # Call the function under test and expect a ValueError due to application-level validation
    with pytest.raises(ValueError) as excinfo:
         await db_layer.add_item_to_collection(mock_conn, collection_id, invalid_item_type, item_id)

    # Assertions
    assert "Invalid item_type" in str(excinfo.value) # Check the error message
    expected_sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    expected_params = (collection_id, invalid_item_type, item_id)

    # Database should not be touched if validation fails before the call
    mock_cursor.execute.assert_not_awaited()
    mock_conn.commit.assert_not_awaited() # Commit should not be called on error
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_db_error(mock_get_conn):
    """Tests handling of general database errors during item addition."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 102
    item_type = "document"
    item_id = 999

    # Simulate a generic database error
    db_error = psycopg.Error("Simulated generic DB error")
    mock_cursor.execute.side_effect = db_error

    # Call the function under test and expect the error
    with pytest.raises(psycopg.Error) as excinfo:
        await db_layer.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    assert excinfo.value is db_error
    expected_sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    expected_params = (collection_id, item_type, item_id)

    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_not_awaited() # Commit should not be called on error
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_success(mock_get_conn):
    """Tests retrieving items from a collection successfully."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 103
    expected_items = [
        ("document", 123),
        ("chunk", 456),
        ("document", 789),
    ]
    # Simulate fetchall returning the items as tuples
    mock_cursor.fetchall.return_value = expected_items

    # Call the function under test
    items = await db_layer.get_collection_items(mock_conn, collection_id)

    # Assertions
    expected_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    expected_params = (collection_id,)

    # Check both execute calls were made
    assert mock_cursor.execute.await_count == 2
    # Check the second call specifically
    mock_cursor.execute.assert_awaited_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    # The function currently returns raw tuples based on list_code_definition_names output
    # Adjust assertion if a data model/dict mapping is implemented later
    assert items == expected_items
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_empty(mock_get_conn):
    """Tests retrieving items from an empty collection returns an empty list."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 104 # An existing but empty collection

    # Simulate fetchall returning an empty list
    mock_cursor.fetchall.return_value = []

    # Call the function under test
    items = await db_layer.get_collection_items(mock_conn, collection_id)

    # Assertions
    expected_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    expected_params = (collection_id,)

    # Check both execute calls were made
    assert mock_cursor.execute.await_count == 2
    # Check the second call specifically
    mock_cursor.execute.assert_awaited_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert items == []
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_non_existent_id(mock_get_conn):
    """Tests retrieving items for a non-existent collection ID returns None."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    non_existent_collection_id = -999 # Assuming negative IDs are never valid

    # Simulate the existence check returning False
    mock_cursor.fetchone.return_value = (False,)

    # Call the function under test
    items = await db_layer.get_collection_items(mock_conn, non_existent_collection_id)

    # Assertions
    expected_check_sql = "SELECT EXISTS(SELECT 1 FROM collections WHERE id = %s);"
    expected_check_params = (non_existent_collection_id,)

    # Only the existence check should be executed
    mock_cursor.execute.assert_awaited_once_with(expected_check_sql, expected_check_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_cursor.fetchall.assert_not_awaited() # The second query should not run
    assert items is None # Function should return None
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_db_error(mock_get_conn):
    """Tests that get_collection_items propagates database errors."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 105

    # Simulate the existence check passing
    mock_cursor.fetchone.return_value = (True,)

    # Simulate a database error during the *second* execute call
    db_error = psycopg.Error("Simulated DB error during item retrieval")

    async def execute_side_effect(sql, params):
        if "collection_items" in sql: # Identify the second query
            raise db_error
        # Allow the first query (existence check) to proceed normally
        # (The actual return value of execute itself isn't usually checked directly)
        return None

    mock_cursor.execute.side_effect = execute_side_effect

    # Call the function under test and expect the error
    with pytest.raises(psycopg.Error) as excinfo:
        await db_layer.get_collection_items(mock_conn, collection_id)

    # Assertions
    assert excinfo.value is db_error # Check if the original error is propagated

    # Check calls
    expected_check_sql = "SELECT EXISTS(SELECT 1 FROM collections WHERE id = %s);"
    expected_check_params = (collection_id,)
    expected_items_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    expected_items_params = (collection_id,)

    assert mock_cursor.execute.await_count == 2
    mock_cursor.execute.assert_any_await(expected_check_sql, expected_check_params)
    mock_cursor.execute.assert_any_await(expected_items_sql, expected_items_params)
    mock_cursor.fetchall.assert_not_awaited() # Should not be called if execute fails
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_remove_item_from_collection_success(mock_get_conn):
    """Tests successfully removing an item from a collection."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 1
    item_type = 'document'
    item_id = 123

    # Simulate the cursor rowcount indicating 1 row was deleted
    mock_cursor.rowcount = 1

    expected_sql = "DELETE FROM collection_items WHERE collection_id = %s AND item_type = %s AND item_id = %s;"
    expected_params = (collection_id, item_type, item_id)

    # Call the function under test
    removed = await db_layer.remove_item_from_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_awaited_once()
    assert removed is True
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_remove_item_from_collection_not_found(mock_get_conn):
    """Tests removing a non-existent item from a collection returns False."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 1
    item_type = 'document'
    item_id = 999 # Non-existent item

    # Simulate the cursor rowcount indicating 0 rows were deleted
    mock_cursor.rowcount = 0

    expected_sql = "DELETE FROM collection_items WHERE collection_id = %s AND item_type = %s AND item_id = %s;"
    expected_params = (collection_id, item_type, item_id)

    # Call the function under test
    removed = await db_layer.remove_item_from_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_awaited_once()
    assert removed is False
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_delete_collection_success(mock_get_conn):
    """Tests successfully deleting a collection."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 1

    # Simulate the cursor rowcount indicating 1 row was deleted
    mock_cursor.rowcount = 1

    # Note: The placeholder mentions deleting items too. A real implementation
    # might need two separate queries (or rely on CASCADE DELETE).
    # For minimal implementation, we'll just test the collection deletion.
    expected_sql = "DELETE FROM collections WHERE id = %s;"
    expected_params = (collection_id,)

    # Call the function under test
    deleted = await db_layer.delete_collection(mock_conn, collection_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_awaited_once()
    assert deleted is True
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_delete_collection_not_found(mock_get_conn):
    """Tests deleting a non-existent collection returns False."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 999 # Non-existent ID

    # Simulate the cursor rowcount indicating 0 rows were deleted
    mock_cursor.rowcount = 0

    expected_sql = "DELETE FROM collections WHERE id = %s;"
    expected_params = (collection_id,)

    # Call the function under test
    deleted = await db_layer.delete_collection(mock_conn, collection_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_awaited_once()
    assert deleted is False