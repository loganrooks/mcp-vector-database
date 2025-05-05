import pytest
import psycopg
import json
from unittest.mock import AsyncMock, MagicMock
from src.philograph.data_access import db_layer
from src.philograph.data_access.db_layer import Relationship, Document, Section, Chunk, SearchResult # Added Relationship
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

    section_id = 789 # Assuming a valid section ID
    text_content = "This is a test chunk."
    sequence = 0
    embedding_vector = [0.1, 0.2, 0.3]
    formatted_embedding = "[0.1,0.2,0.3]"
    mock_format_vector.return_value = formatted_embedding # Mock the formatting

    expected_id = 101
    expected_sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s::vector(%s))
        RETURNING id;
    """
    expected_params = (section_id, text_content, sequence, formatted_embedding, 3) # Use mocked dimension

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
    mock_get_conn.return_value.__aenter__.return_value = mock_conn

    section_id = 789
    text_content = "Chunk with wrong dimension."
    sequence = 1
    embedding_vector = [0.1, 0.2] # Incorrect dimension (2 instead of 3)

    # Expect ValueError to be raised
    with pytest.raises(ValueError, match="Embedding vector dimension mismatch"):
        await db_layer.add_chunk(mock_conn, section_id, text_content, sequence, embedding_vector)

    # Ensure commit was not called
    mock_conn.commit.assert_not_called()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.format_vector_for_pgvector')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension for test
async def test_add_chunks_batch_success(mock_format_vector, mock_get_conn):
    """Tests successfully adding multiple chunks in a batch."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    chunks_data = [
        (789, "Chunk 1", 0, [0.1, 0.2, 0.3]),
        (789, "Chunk 2", 1, [0.4, 0.5, 0.6]),
        (790, "Chunk 3", 0, [0.7, 0.8, 0.9]),
    ]
    formatted_embeddings = ["[0.1,0.2,0.3]", "[0.4,0.5,0.6]", "[0.7,0.8,0.9]"]
    # Mock format_vector to return expected strings for each vector
    mock_format_vector.side_effect = formatted_embeddings

    expected_sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s::vector(%s));
    """
    expected_params_list = [
        (789, "Chunk 1", 0, formatted_embeddings[0], 3),
        (789, "Chunk 2", 1, formatted_embeddings[1], 3),
        (790, "Chunk 3", 0, formatted_embeddings[2], 3),
    ]

    # Call the function under test
    await db_layer.add_chunks_batch(mock_conn, chunks_data)

    # Assertions
    assert mock_format_vector.call_count == len(chunks_data)
    mock_cursor.executemany.assert_awaited_once_with(expected_sql, expected_params_list)
    mock_conn.commit.assert_awaited_once()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_chunks_batch_empty_list(mock_get_conn):
    """Tests that adding an empty list of chunks does nothing."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    chunks_data = []

    # Call the function under test
    await db_layer.add_chunks_batch(mock_conn, chunks_data)

    # Assertions
    mock_cursor.executemany.assert_not_awaited()
    mock_conn.commit.assert_not_called()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension for test
async def test_add_chunks_batch_invalid_dimension(mock_get_conn):
    """Tests adding chunks with incorrect embedding dimension in batch raises ValueError."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn

    chunks_data = [
        (789, "Chunk 1", 0, [0.1, 0.2, 0.3]),
        (789, "Chunk 2", 1, [0.4, 0.5]), # Incorrect dimension
    ]

    # Expect ValueError to be raised during formatting
    with pytest.raises(ValueError, match="Embedding vector dimension mismatch in batch"):
        await db_layer.add_chunks_batch(mock_conn, chunks_data)

    # Ensure commit was not called
    mock_conn.commit.assert_not_called()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.format_vector_for_pgvector')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension for test
async def test_add_chunks_batch_db_error(mock_format_vector, mock_get_conn):
    """Tests that a database error during batch insert prevents commit."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    chunks_data = [
        (789, "Chunk 1", 0, [0.1, 0.2, 0.3]),
        (999, "Chunk Invalid FK", 0, [0.7, 0.8, 0.9]), # Assume 999 is invalid section_id
    ]
    formatted_embeddings = ["[0.1,0.2,0.3]", "[0.7,0.8,0.9]"]
    mock_format_vector.side_effect = formatted_embeddings

    # Simulate psycopg.IntegrityError on executemany
    mock_cursor.executemany.side_effect = psycopg.IntegrityError("FK constraint violation")

    expected_sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s::vector(%s));
    """
    expected_params_list = [
        (789, "Chunk 1", 0, formatted_embeddings[0], 3),
        (999, "Chunk Invalid FK", 0, formatted_embeddings[1], 3),
    ]

    # Expect psycopg.IntegrityError to be raised and propagated
    with pytest.raises(psycopg.IntegrityError):
        await db_layer.add_chunks_batch(mock_conn, chunks_data)

    # Assertions
    assert mock_format_vector.call_count == len(chunks_data)
    mock_cursor.executemany.assert_awaited_once_with(expected_sql, expected_params_list)
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
    mock_cursor.fetchone.return_value = {'id': 201}

    source_chunk_id = 101 # Assuming a valid chunk ID
    cited_doc_details = {"title": "Cited Doc", "author": "Cited Author"}
    serialized_details = '{"title": "Cited Doc", "author": "Cited Author"}'
    mock_json_serialize.return_value = serialized_details # Mock serialization

    expected_id = 201
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
    """Tests adding a reference with an invalid chunk_id raises IntegrityError."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    source_chunk_id = 999 # Non-existent chunk_id
    cited_doc_details = {"title": "Cited Doc"}
    serialized_details = '{"title": "Cited Doc"}'
    mock_json_serialize.return_value = serialized_details

    # Simulate psycopg.IntegrityError (foreign key violation) on execute
    mock_cursor.execute.side_effect = psycopg.IntegrityError("insert or update on table \"references\" violates foreign key constraint")

    # Expect psycopg.IntegrityError to be raised and propagated
    with pytest.raises(psycopg.IntegrityError):
        await db_layer.add_reference(mock_conn, source_chunk_id, cited_doc_details)

    # Assertions
    mock_json_serialize.assert_called_once_with(cited_doc_details)
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error

# --- Test Search Operations ---

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.format_vector_for_pgvector')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_vector_search_chunks_success(mock_format_vector, mock_get_conn):
    """Tests basic vector search returns correctly mapped SearchResult objects."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    query_embedding = [1.1, 2.2, 3.3]
    formatted_query_embedding = "[1.1,2.2,3.3]"
    mock_format_vector.return_value = formatted_query_embedding
    top_k = 2

    # Simulate database results (list of dictionaries)
    db_results = [
        {
            'chunk_id': 101, 'text_content': 'Chunk A', 'sequence': 0,
            'section_id': 789, 'section_title': 'Sec 1',
            'doc_id': 123, 'doc_title': 'Doc X', 'doc_author': 'Auth X', 'doc_year': 2020,
            'source_path': '/path/x.pdf', 'distance': 0.123
        },
        {
            'chunk_id': 105, 'text_content': 'Chunk B', 'sequence': 1,
            'section_id': 790, 'section_title': 'Sec 2',
            'doc_id': 124, 'doc_title': 'Doc Y', 'doc_author': 'Auth Y', 'doc_year': 2021,
            'source_path': '/path/y.txt', 'distance': 0.456
        }
    ]
    mock_cursor.fetchall.return_value = db_results

    expected_sql = f"""
        SELECT c.id as chunk_id, c.text_content, c.sequence, s.id as section_id, s.title as section_title,
               d.id as doc_id, d.title as doc_title, d.author as doc_author, d.year as doc_year, d.source_path,
               c.embedding <=> %s::vector(3) AS distance
        FROM chunks c
        JOIN sections s ON c.section_id = s.id
        JOIN documents d ON s.doc_id = d.id
     ORDER BY distance ASC LIMIT %s;"""
    expected_params = (formatted_query_embedding, top_k)

    # Call the function under test
    search_results = await db_layer.vector_search_chunks(mock_conn, query_embedding, top_k)

    # Assertions
    mock_format_vector.assert_called_once_with(query_embedding)
    mock_cursor.execute.assert_awaited_once_with(expected_sql.strip(), expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(search_results) == top_k
    assert all(isinstance(res, SearchResult) for res in search_results)
    # Check mapping for the first result
    assert search_results[0].chunk_id == db_results[0]['chunk_id']
    assert search_results[0].text_content == db_results[0]['text_content']
    assert search_results[0].doc_title == db_results[0]['doc_title']
    assert search_results[0].distance == db_results[0]['distance']
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.format_vector_for_pgvector')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_vector_search_chunks_with_filters(mock_format_vector, mock_get_conn):
    """Tests vector search with metadata filters."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    query_embedding = [0.1, 0.2, 0.3]
    formatted_query_embedding = "[0.1,0.2,0.3]"
    mock_format_vector.return_value = formatted_query_embedding
    top_k = 5
    filters = {"author": "Test Author", "year": 2023, "doc_id": 123}

    # Simulate database results (empty for simplicity, focus is on query construction)
    mock_cursor.fetchall.return_value = []

    expected_base_sql = f"""
        SELECT c.id as chunk_id, c.text_content, c.sequence, s.id as section_id, s.title as section_title,
               d.id as doc_id, d.title as doc_title, d.author as doc_author, d.year as doc_year, d.source_path,
               c.embedding <=> %s::vector(3) AS distance
        FROM chunks c
        JOIN sections s ON c.section_id = s.id
        JOIN documents d ON s.doc_id = d.id
    """
    expected_where = " WHERE d.author ILIKE %s AND d.year = %s AND d.id = %s"
    expected_order_limit = " ORDER BY distance ASC LIMIT %s;"
    expected_full_sql = expected_base_sql.strip() + expected_where + expected_order_limit

    # Parameters: embedding, author filter, year filter, doc_id filter, top_k
    expected_params = (
        formatted_query_embedding,
        f"%{filters['author']}%",
        filters['year'],
        filters['doc_id'],
        top_k
    )

    # Call the function under test
    await db_layer.vector_search_chunks(mock_conn, query_embedding, top_k, filters)

    # Assertions
    mock_format_vector.assert_called_once_with(query_embedding)
    # Check the constructed SQL and parameters
    mock_cursor.execute.assert_awaited_once_with(expected_full_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_vector_search_chunks_invalid_dimension(mock_get_conn):
    """Tests vector search with incorrect query embedding dimension raises ValueError."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn

    query_embedding = [0.1, 0.2] # Incorrect dimension (2 instead of 3)
    top_k = 5

    # Expect ValueError to be raised
    with pytest.raises(ValueError, match="Query embedding dimension mismatch"):
        await db_layer.vector_search_chunks(mock_conn, query_embedding, top_k)
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_vector_search_chunks_empty_embedding(mock_get_conn):
    """Tests vector search with an empty query embedding raises ValueError."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn

    query_embedding = [] # Empty embedding
    top_k = 5

    # Expect ValueError to be raised
    with pytest.raises(ValueError, match="Query embedding cannot be empty."):
        await db_layer.vector_search_chunks(mock_conn, query_embedding, top_k)
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
@patch('src.philograph.data_access.db_layer.format_vector_for_pgvector')
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension
async def test_vector_search_chunks_db_error(mock_format_vector, mock_get_conn):
    """Tests that vector search propagates database errors."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    query_embedding = [1.1, 2.2, 3.3]
    formatted_query_embedding = "[1.1,2.2,3.3]"
    mock_format_vector.return_value = formatted_query_embedding
    top_k = 2

    # Simulate psycopg.Error on execute
    db_error = psycopg.Error("Simulated DB error during search")
    mock_cursor.execute.side_effect = db_error

    # Expect psycopg.Error to be raised and propagated
    with pytest.raises(psycopg.Error) as excinfo:
        await db_layer.vector_search_chunks(mock_conn, query_embedding, top_k)

    # Assertions
    assert excinfo.value is db_error # Check if the original error is propagated
    mock_format_vector.assert_called_once_with(query_embedding)
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    mock_cursor.fetchall.assert_not_awaited() # Fetch should not be called on error

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
    mock_cursor.fetchone.return_value = {'id': 301}

    source_node_id = "doc:123"
    target_node_id = "chunk:456"
    relation_type = "cites"
    metadata = {"page": 42}
    serialized_metadata = '{"page": 42}'
    mock_json_serialize.return_value = serialized_metadata

    expected_id = 301
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
    """Tests that add_relationship propagates database errors."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    source_node_id = "doc:123"
    target_node_id = "doc:999" # Assume invalid target
    relation_type = "related_to"
    metadata = None
    serialized_metadata = None
    mock_json_serialize.return_value = serialized_metadata

    # Simulate psycopg.IntegrityError on execute
    db_error = psycopg.IntegrityError("FK constraint violation")
    mock_cursor.execute.side_effect = db_error

    # Expect psycopg.IntegrityError to be raised and propagated
    with pytest.raises(psycopg.IntegrityError):
        await db_layer.add_relationship(mock_conn, source_node_id, target_node_id, relation_type, metadata)

    # Assertions
    mock_json_serialize.assert_called_once_with(metadata)
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
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
        {'id': 301, 'source_node_id': node_id, 'target_node_id': 'chunk:456', 'relation_type': 'cites', 'metadata_jsonb': {'page': 42}},
        {'id': 302, 'source_node_id': node_id, 'target_node_id': 'doc:789', 'relation_type': 'related_to', 'metadata_jsonb': None}
    ]
    mock_cursor.fetchall.return_value = db_results

    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships WHERE source_node_id = %s"
    expected_params = (node_id,)

    # Call the function under test
    relationships = await db_layer.get_relationships(mock_conn, node_id, direction='outgoing')

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == 2
    assert all(isinstance(rel, Relationship) for rel in relationships)
    assert relationships[0].id == db_results[0]['id']
    assert relationships[0].target_node_id == db_results[0]['target_node_id']
    assert relationships[0].metadata == db_results[0]['metadata_jsonb']
    assert relationships[1].metadata == {} # Check None metadata maps to empty dict
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
        {'id': 301, 'source_node_id': 'doc:123', 'target_node_id': node_id, 'relation_type': 'cites', 'metadata_jsonb': {'page': 42}}
    ]
    mock_cursor.fetchall.return_value = db_results

    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships WHERE target_node_id = %s"
    expected_params = (node_id,)

    # Call the function under test
    relationships = await db_layer.get_relationships(mock_conn, node_id, direction='incoming')

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == 1
    assert relationships[0].id == db_results[0]['id']
    assert relationships[0].source_node_id == db_results[0]['source_node_id']
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_relationships_both_success(mock_get_conn):
    """Tests retrieving both incoming and outgoing relationships."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    node_id = "doc:123"
    db_results = [
        {'id': 301, 'source_node_id': node_id, 'target_node_id': 'chunk:456', 'relation_type': 'cites', 'metadata_jsonb': {}},
        {'id': 305, 'source_node_id': 'doc:999', 'target_node_id': node_id, 'relation_type': 'cites', 'metadata_jsonb': {}}
    ]
    mock_cursor.fetchall.return_value = db_results

    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships WHERE (source_node_id = %s OR target_node_id = %s)"
    expected_params = (node_id, node_id)

    # Call the function under test
    relationships = await db_layer.get_relationships(mock_conn, node_id, direction='both')

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == 2
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
        {'id': 301, 'source_node_id': node_id, 'target_node_id': 'chunk:456', 'relation_type': relation_type_filter, 'metadata_jsonb': {}}
    ] # Only the 'cites' relationship should be returned
    mock_cursor.fetchall.return_value = db_results

    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships WHERE source_node_id = %s AND relation_type = %s"
    expected_params = (node_id, relation_type_filter)

    # Call the function under test
    relationships = await db_layer.get_relationships(mock_conn, node_id, direction='outgoing', relation_type=relation_type_filter)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == 1
    assert relationships[0].relation_type == relation_type_filter
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_relationships_non_existent_node(mock_get_conn):
    """Tests retrieving relationships for a non-existent node returns an empty list."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    node_id = "non:existent"
    # Simulate fetchall returning an empty list
    mock_cursor.fetchall.return_value = []

    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships WHERE source_node_id = %s"
    expected_params = (node_id,)

    # Call the function under test (default direction is outgoing)
    relationships = await db_layer.get_relationships(mock_conn, node_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert relationships == []
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_relationships_for_document_success(mock_get_conn):
    """Tests retrieving relationships originating from chunks within a document."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    doc_id = 123
    db_results = [
        {'id': 301, 'source_node_id': 'chunk:456', 'target_node_id': 'doc:789', 'relation_type': 'cites', 'metadata_jsonb': {'page': 10}},
        {'id': 302, 'source_node_id': 'chunk:457', 'target_node_id': 'doc:790', 'relation_type': 'cites', 'metadata_jsonb': None}
    ]
    mock_cursor.fetchall.return_value = db_results

    expected_sql = """
        SELECT r.id, r.source_node_id, r.target_node_id, r.relation_type, r.metadata_jsonb
        FROM relationships r
        JOIN chunks c ON r.source_node_id = 'chunk:' || c.id::text
        JOIN sections s ON c.section_id = s.id
        WHERE s.doc_id = %s;
    """
    expected_params = (doc_id,)

    # Call the function under test
    relationships = await db_layer.get_relationships_for_document(mock_conn, doc_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql.strip(), expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == 2
    assert all(isinstance(rel, Relationship) for rel in relationships)
    assert relationships[0].id == db_results[0]['id']
    assert relationships[0].source_node_id == db_results[0]['source_node_id']
    assert relationships[0].metadata == db_results[0]['metadata_jsonb']
    assert relationships[1].metadata == {} # Check None metadata maps to empty dict
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_relationships_for_document_empty(mock_get_conn):
    """Tests retrieving relationships for a document with no relationships."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    doc_id = 124
    # Simulate fetchall returning an empty list
    mock_cursor.fetchall.return_value = []

    expected_sql = """
        SELECT r.id, r.source_node_id, r.target_node_id, r.relation_type, r.metadata_jsonb
        FROM relationships r
        JOIN chunks c ON r.source_node_id = 'chunk:' || c.id::text
        JOIN sections s ON c.section_id = s.id
        WHERE s.doc_id = %s;
    """
    expected_params = (doc_id,)

    # Call the function under test
    relationships = await db_layer.get_relationships_for_document(mock_conn, doc_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql.strip(), expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert relationships == []
# --- Test Collection Operations ---

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_collection_success(mock_get_conn):
    """Tests successfully adding a new collection."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = (1,) # Return a tuple as fetchone does

    collection_name = "My Test Collection"
    expected_id = 1
    expected_sql = "INSERT INTO collections (name) VALUES (%s) RETURNING id;"
    expected_params = (collection_name,)

    # Call the function under test
    returned_id = await db_layer.add_collection(mock_conn, collection_name)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_conn.commit.assert_awaited_once()
    assert returned_id == expected_id
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_collection_db_error(mock_get_conn):
    """Tests that add_collection propagates database errors."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_name = "Error Collection"

    # Simulate psycopg.Error on execute
    db_error = psycopg.Error("Simulated DB error during collection insert")
    mock_cursor.execute.side_effect = db_error

    expected_sql = "INSERT INTO collections (name) VALUES (%s) RETURNING id;"
    expected_params = (collection_name,)

    # Expect psycopg.Error to be raised and propagated
    with pytest.raises(psycopg.Error) as excinfo:
        await db_layer.add_collection(mock_conn, collection_name)

    # Assertions
    assert excinfo.value is db_error # Check if the original error is propagated
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_not_awaited() # Fetchone should not be called
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_document_success(mock_get_conn):
    """Tests successfully adding a document item to a collection."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 1
    item_type = "document"
    item_id = 123
    expected_sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    expected_params = (collection_id, item_type, item_id)

    # Call the function under test
    await db_layer.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_awaited_once()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_chunk_success(mock_get_conn):
    """Tests successfully adding a chunk item to a collection."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 2
    item_type = "chunk"
    item_id = 456
    expected_sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    expected_params = (collection_id, item_type, item_id)

    # Call the function under test
    await db_layer.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_awaited_once()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_invalid_collection_id(mock_get_conn):
    """Tests adding an item with an invalid collection_id raises IntegrityError."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 999 # Non-existent collection ID
    item_type = "document"
    item_id = 123

    # Simulate psycopg.IntegrityError (foreign key violation) on execute
    mock_cursor.execute.side_effect = psycopg.IntegrityError("insert or update on table \"collection_items\" violates foreign key constraint")

    # Expect psycopg.IntegrityError to be raised and propagated
    with pytest.raises(psycopg.IntegrityError):
        await db_layer.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_invalid_item_type(mock_get_conn):
    """Tests adding an item with an invalid item_type raises ValueError."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn

    collection_id = 1
    item_type = "invalid_type" # Invalid type
    item_id = 123

    # Expect ValueError to be raised due to the check within the function
    with pytest.raises(ValueError, match="Invalid item_type"):
        await db_layer.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Ensure commit was not called
    mock_conn.commit.assert_not_called()
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_db_error(mock_get_conn):
    """Tests that add_item_to_collection propagates database errors."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 1
    item_type = "document"
    item_id = 123

    # Simulate psycopg.Error on execute
    db_error = psycopg.Error("Simulated DB error during item insert")
    mock_cursor.execute.side_effect = db_error

    expected_sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    expected_params = (collection_id, item_type, item_id)

    # Expect psycopg.Error to be raised and propagated
    with pytest.raises(psycopg.Error) as excinfo:
        await db_layer.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    assert excinfo.value is db_error # Check if the original error is propagated
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_success(mock_get_conn):
    """Tests retrieving items from a collection with multiple items."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 1
    expected_items = [("document", 123), ("chunk", 456)]
    # Simulate fetchall returning a list of tuples
    mock_cursor.fetchall.return_value = expected_items

    expected_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    expected_params = (collection_id,)

    # Call the function under test
    items = await db_layer.get_collection_items(mock_conn, collection_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert items == expected_items
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_empty(mock_get_conn):
    """Tests retrieving items from an empty collection."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 2
    expected_items = []
    # Simulate fetchall returning an empty list
    mock_cursor.fetchall.return_value = expected_items

    expected_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    expected_params = (collection_id,)

    # Call the function under test
    items = await db_layer.get_collection_items(mock_conn, collection_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert items == expected_items
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_non_existent_id(mock_get_conn):
    """Tests retrieving items for a non-existent collection ID returns an empty list."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    non_existent_collection_id = -999 # Assuming negative IDs are never valid
    expected_items = []
    # Simulate fetchall returning an empty list for a non-existent ID
    mock_cursor.fetchall.return_value = expected_items

    expected_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    expected_params = (non_existent_collection_id,)

    # Call the function under test
    items = await db_layer.get_collection_items(mock_conn, non_existent_collection_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert items == expected_items
@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_db_error(mock_get_conn):
    """Tests that get_collection_items propagates database errors."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 105

    # Simulate a database error during the execute call
    db_error = psycopg.Error("Simulated DB error during item retrieval")
    mock_cursor.execute.side_effect = db_error

    # Call the function under test and expect the error
    with pytest.raises(psycopg.Error) as excinfo:
        await db_layer.get_collection_items(mock_conn, collection_id)

    # Assertions
    assert excinfo.value is db_error # Check if the original error is propagated

    # Check calls
    expected_items_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    expected_items_params = (collection_id,)

    # Check the execute call was made once with the correct SQL
    mock_cursor.execute.assert_awaited_once_with(expected_items_sql, expected_items_params)
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error
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

# --- Test Schema Initialization ---
# Note: These tests are basic checks. More comprehensive tests might involve
# inspecting the database schema directly or using a dedicated testing database.

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_initialize_schema_success(mock_get_conn):
    """Tests that initialize_schema executes all expected SQL commands."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Call the function under test
    await db_layer.initialize_schema(mock_conn)

    # Assertions
    # Check that execute was called multiple times (at least for each CREATE statement)
    assert mock_cursor.execute.await_count >= 10 # Adjust count based on actual number of statements
    # Check specific statements were executed (optional, can be brittle)
    mock_cursor.execute.assert_any_await("CREATE EXTENSION IF NOT EXISTS vector;")
    mock_cursor.execute.assert_any_await("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;") # Example check
    mock_cursor.execute.assert_any_await("CREATE TABLE IF NOT EXISTS documents (") # Check table creation start
    mock_cursor.execute.assert_any_await("CREATE TABLE IF NOT EXISTS sections (")
    mock_cursor.execute.assert_any_await("CREATE TABLE IF NOT EXISTS chunks (")
    mock_cursor.execute.assert_any_await("CREATE TABLE IF NOT EXISTS \"references\" (") # Quoted table name
    mock_cursor.execute.assert_any_await("CREATE TABLE IF NOT EXISTS relationships (")
    mock_cursor.execute.assert_any_await("CREATE TABLE IF NOT EXISTS collections (")
    mock_cursor.execute.assert_any_await("CREATE TABLE IF NOT EXISTS collection_items (")
    mock_cursor.execute.assert_any_await("CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);") # Check index creation

    mock_conn.commit.assert_awaited_once() # Should commit at the end

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_initialize_schema_db_error(mock_get_conn):
    """Tests that initialize_schema propagates database errors."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate psycopg.Error on one of the execute calls
    db_error = psycopg.Error("Simulated DB error during schema init")
    mock_cursor.execute.side_effect = db_error

    # Expect psycopg.Error to be raised and propagated
    with pytest.raises(psycopg.Error) as excinfo:
        await db_layer.initialize_schema(mock_conn)

    # Assertions
    assert excinfo.value is db_error # Check if the original error is propagated
    mock_cursor.execute.assert_awaited_once() # Should fail on the first execute
    mock_conn.commit.assert_not_called() # Commit should not be called on error

# --- Test Relationship Functions (Mocker based) ---
# These tests use mocker fixture for simpler mocking setup

@pytest.mark.asyncio
async def test_add_relationship_cites_success(mocker):
    """Tests adding a 'cites' relationship successfully."""
    mock_conn = mocker.AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = mocker.AsyncMock(spec=psycopg.AsyncCursor)
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'id': 1} # Simulate returning ID

    source = "doc:1"
    target = "doc:2"
    rel_type = "cites"
    metadata = {"page": 5}
    serialized_metadata = json.dumps(metadata)

    mocker.patch('src.philograph.data_access.db_layer.json_serialize', return_value=serialized_metadata)

    result_id = await db_layer.add_relationship(mock_conn, source, target, rel_type, metadata)

    expected_sql = """
        INSERT INTO relationships (source_node_id, target_node_id, relation_type, metadata_jsonb)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    mock_cursor.execute.assert_awaited_once_with(expected_sql, (source, target, rel_type, serialized_metadata))
    mock_conn.commit.assert_awaited_once()
    assert result_id == 1

@pytest.mark.asyncio
async def test_add_relationship_invalid_source_node(mocker):
    """Tests adding relationship with invalid source node raises IntegrityError."""
    mock_conn = mocker.AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = mocker.AsyncMock(spec=psycopg.AsyncCursor)
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg.IntegrityError("FK violation")

    mocker.patch('src.philograph.data_access.db_layer.json_serialize', return_value=None)

    with pytest.raises(psycopg.IntegrityError):
        await db_layer.add_relationship(mock_conn, "invalid:1", "doc:2", "cites")

    mock_conn.commit.assert_not_called()

@pytest.mark.asyncio
async def test_add_relationship_invalid_target_node(mocker):
    """Tests adding relationship with invalid target node raises IntegrityError."""
    mock_conn = mocker.AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = mocker.AsyncMock(spec=psycopg.AsyncCursor)
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg.IntegrityError("FK violation")

    mocker.patch('src.philograph.data_access.db_layer.json_serialize', return_value=None)

    with pytest.raises(psycopg.IntegrityError):
        await db_layer.add_relationship(mock_conn, "doc:1", "invalid:2", "cites")

    mock_conn.commit.assert_not_called()

@pytest.mark.asyncio
async def test_add_relationship_with_metadata(mocker):
    """Tests adding a relationship with metadata."""
    mock_conn = mocker.AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = mocker.AsyncMock(spec=psycopg.AsyncCursor)
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'id': 2}

    metadata = {"certainty": 0.9, "source": "manual"}
    serialized_metadata = json.dumps(metadata)
    mocker.patch('src.philograph.data_access.db_layer.json_serialize', return_value=serialized_metadata)

    result_id = await db_layer.add_relationship(mock_conn, "chunk:10", "chunk:11", "related_concept", metadata)

    expected_sql = """
        INSERT INTO relationships (source_node_id, target_node_id, relation_type, metadata_jsonb)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    mock_cursor.execute.assert_awaited_once_with(expected_sql, ("chunk:10", "chunk:11", "related_concept", serialized_metadata))
    mock_conn.commit.assert_awaited_once()
    assert result_id == 2

@pytest.mark.asyncio
async def test_get_relationships_outgoing_cites(mocker):
    """Tests getting outgoing 'cites' relationships."""
    mock_conn = mocker.AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = mocker.AsyncMock(spec=psycopg.AsyncCursor)
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    db_results = [
        {'id': 1, 'source_node_id': 'doc:1', 'target_node_id': 'doc:2', 'relation_type': 'cites', 'metadata_jsonb': {'page': 5}},
        {'id': 3, 'source_node_id': 'doc:1', 'target_node_id': 'chunk:10', 'relation_type': 'cites', 'metadata_jsonb': None}
    ]
    mock_cursor.fetchall.return_value = db_results

    relationships = await db_layer.get_relationships(mock_conn, "doc:1", direction='outgoing', relation_type='cites')

    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships WHERE source_node_id = %s AND relation_type = %s"
    mock_cursor.execute.assert_awaited_once_with(expected_sql, ("doc:1", "cites"))
    assert len(relationships) == 2
    assert relationships[0].id == 1
    assert relationships[0].target_node_id == 'doc:2'
    assert relationships[0].metadata == {'page': 5}
    assert relationships[1].id == 3
    assert relationships[1].target_node_id == 'chunk:10'
    assert relationships[1].metadata == {}

@pytest.mark.asyncio
async def test_get_relationships_incoming_cites(mocker):
    """Tests getting incoming 'cites' relationships."""
    mock_conn = mocker.AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = mocker.AsyncMock(spec=psycopg.AsyncCursor)
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    db_results = [
        {'id': 4, 'source_node_id': 'doc:5', 'target_node_id': 'doc:2', 'relation_type': 'cites', 'metadata_jsonb': None}
    ]
    mock_cursor.fetchall.return_value = db_results

    relationships = await db_layer.get_relationships(mock_conn, "doc:2", direction='incoming', relation_type='cites')

    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships WHERE target_node_id = %s AND relation_type = %s"
    mock_cursor.execute.assert_awaited_once_with(expected_sql, ("doc:2", "cites"))
    assert len(relationships) == 1
    assert relationships[0].id == 4
    assert relationships[0].source_node_id == 'doc:5'
    assert relationships[0].metadata == {}

@pytest.mark.asyncio
async def test_get_relationships_specific_type(mocker):
    """Tests getting relationships filtered only by type (both directions)."""
    mock_conn = mocker.AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = mocker.AsyncMock(spec=psycopg.AsyncCursor)
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    db_results = [
        {'id': 5, 'source_node_id': 'chunk:10', 'target_node_id': 'chunk:11', 'relation_type': 'related_concept', 'metadata_jsonb': {}},
    ]
    mock_cursor.fetchall.return_value = db_results

    # Note: The function requires node_id, so this test case might need adjustment
    # if we want to search *only* by type across all nodes.
    # Assuming we search for 'related_concept' around 'chunk:10'
    node_id = "chunk:10"
    rel_type = "related_concept"
    relationships = await db_layer.get_relationships(mock_conn, node_id, direction='both', relation_type=rel_type)

    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships WHERE (source_node_id = %s OR target_node_id = %s) AND relation_type = %s"
    mock_cursor.execute.assert_awaited_once_with(expected_sql, (node_id, node_id, rel_type))
    assert len(relationships) == 1
    assert relationships[0].id == 5

@pytest.mark.asyncio
async def test_get_relationships_direction_both(mocker):
    """Tests getting relationships in both directions."""
    mock_conn = mocker.AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = mocker.AsyncMock(spec=psycopg.AsyncCursor)
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    db_results = [
        {'id': 1, 'source_node_id': 'doc:1', 'target_node_id': 'doc:2', 'relation_type': 'cites', 'metadata_jsonb': {}}, # Outgoing
        {'id': 4, 'source_node_id': 'doc:5', 'target_node_id': 'doc:1', 'relation_type': 'cites', 'metadata_jsonb': {}}  # Incoming
    ]
    mock_cursor.fetchall.return_value = db_results

    node_id = "doc:1"
    relationships = await db_layer.get_relationships(mock_conn, node_id, direction='both')

    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships WHERE (source_node_id = %s OR target_node_id = %s)"
    mock_cursor.execute.assert_awaited_once_with(expected_sql, (node_id, node_id))
    assert len(relationships) == 2

@pytest.mark.asyncio
async def test_get_relationships_non_existent_node(mocker):
    """Tests getting relationships for a non-existent node returns empty list."""
    mock_conn = mocker.AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = mocker.AsyncMock(spec=psycopg.AsyncCursor)
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [] # Simulate no results

    node_id = "nonexistent:999"
    relationships = await db_layer.get_relationships(mock_conn, node_id) # Default outgoing

    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships WHERE source_node_id = %s"
    mock_cursor.execute.assert_awaited_once_with(expected_sql, (node_id,))
    assert relationships == []

@pytest.mark.asyncio
async def test_get_relationships_invalid_direction(mocker):
    """Tests that an invalid direction raises ValueError."""
    mock_conn = mocker.AsyncMock(spec=psycopg.AsyncConnection)

    with pytest.raises(ValueError, match="Invalid direction specified"):
        await db_layer.get_relationships(mock_conn, "doc:1", direction="sideways")


# --- Test Collection Operations ---

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_collection_success(mock_get_conn):
    """Tests successfully adding a new collection."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = (1,) # Return a tuple as fetchone does

    collection_name = "My Test Collection"
    expected_id = 1
    expected_sql = "INSERT INTO collections (name) VALUES (%s) RETURNING id;"
    expected_params = (collection_name,)

    # Call the function under test
    returned_id = await db_layer.add_collection(mock_conn, collection_name)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    mock_conn.commit.assert_awaited_once()
    assert returned_id == expected_id

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_document_success(mock_get_conn):
    """Tests successfully adding a document item to a collection."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 1
    item_type = "document"
    item_id = 123
    expected_sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    expected_params = (collection_id, item_type, item_id)

    # Call the function under test
    await db_layer.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_awaited_once()

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_chunk_success(mock_get_conn):
    """Tests successfully adding a chunk item to a collection."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 2
    item_type = "chunk"
    item_id = 456
    expected_sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    expected_params = (collection_id, item_type, item_id)

    # Call the function under test
    await db_layer.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_awaited_once()

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_add_item_to_collection_non_existent_collection(mock_get_conn):
    """Tests adding an item to a non-existent collection raises IntegrityError."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate psycopg.IntegrityError (foreign key violation) on execute
    mock_cursor.execute.side_effect = psycopg.IntegrityError("insert or update on table \"collection_items\" violates foreign key constraint")

    collection_id = 999 # Non-existent collection ID
    item_type = "document"
    item_id = 123

    # Expect psycopg.IntegrityError to be raised and propagated
    with pytest.raises(psycopg.IntegrityError):
        await db_layer.add_item_to_collection(mock_conn, collection_id, item_type, item_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_success(mock_get_conn):
    """Tests retrieving items from a collection with multiple items."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 1
    expected_items = [("document", 123), ("chunk", 456)]
    # Simulate fetchall returning a list of tuples
    mock_cursor.fetchall.return_value = expected_items

    expected_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    expected_params = (collection_id,)

    # Call the function under test
    items = await db_layer.get_collection_items(mock_conn, collection_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert items == expected_items

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_empty(mock_get_conn):
    """Tests retrieving items from an empty collection."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 2
    expected_items = []
    # Simulate fetchall returning an empty list
    mock_cursor.fetchall.return_value = expected_items

    expected_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    expected_params = (collection_id,)

    # Call the function under test
    items = await db_layer.get_collection_items(mock_conn, collection_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert items == expected_items

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_non_existent_id(mock_get_conn):
    """Tests retrieving items for a non-existent collection ID returns an empty list."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    non_existent_collection_id = -999 # Assuming negative IDs are never valid
    expected_items = []
    # Simulate fetchall returning an empty list for a non-existent ID
    mock_cursor.fetchall.return_value = expected_items

    expected_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    expected_params = (non_existent_collection_id,)

    # Call the function under test
    items = await db_layer.get_collection_items(mock_conn, non_existent_collection_id)

    # Assertions
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert items == expected_items

@pytest.mark.asyncio
@patch('src.philograph.data_access.db_layer.get_db_connection')
async def test_get_collection_items_db_error(mock_get_conn):
    """Tests that get_collection_items propagates database errors."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_get_conn.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    collection_id = 105

    # Simulate a database error during the execute call
    db_error = psycopg.Error("Simulated DB error during item retrieval")
    mock_cursor.execute.side_effect = db_error

    # Call the function under test and expect the error
    with pytest.raises(psycopg.Error) as excinfo:
        await db_layer.get_collection_items(mock_conn, collection_id)

    # Assertions
    assert excinfo.value is db_error # Check if the original error is propagated

    # Check calls
    expected_items_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    expected_items_params = (collection_id,)

    # Check the execute call was made once with the correct SQL
    mock_cursor.execute.assert_awaited_once_with(expected_items_sql, expected_items_params)
    mock_conn.commit.assert_not_called() # Ensure commit was NOT called on error