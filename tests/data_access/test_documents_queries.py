import pytest
import psycopg
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any, Optional

# Import functions from the new queries module
from src.philograph.data_access.queries import documents as doc_queries
# Import models if needed for type hints or assertions
from src.philograph.data_access.models import Document
# Import config if needed (e.g., for embedding dimension)
from src.philograph import config
# Import utility functions if used directly in tests (though mocks are preferred)
from src.philograph.utils import db_utils

# --- Mock Fixtures (Example - Define or import actual fixtures) ---
# These would typically be in a conftest.py or defined here if simple

@pytest.fixture
def mock_get_conn(mocker):
    """Fixture to mock the get_db_connection context manager."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    # Configure cursor context manager
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    # Configure connection context manager mock
    mock_cm = mocker.patch('src.philograph.data_access.connection.get_db_connection')
    mock_cm.return_value.__aenter__.return_value = mock_conn
    # Return the connection mock for use in tests if needed, along with cursor
    return mock_conn, mock_cursor

@pytest.fixture
def mock_format_vector(mocker):
    """Fixture to mock the format_vector_for_pgvector utility."""
    return mocker.patch('src.philograph.data_access.queries.documents.format_vector_for_pgvector')

@pytest.fixture
def mock_json_serialize(mocker):
    """Fixture to mock the json_serialize utility."""
    return mocker.patch('src.philograph.utils.db_utils.json_serialize')

# --- Test Document Operations ---

@pytest.mark.asyncio
async def test_add_document_success(mock_get_conn):
    """Tests successfully adding a document."""
    mock_conn, mock_cursor = mock_get_conn

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = (123,) # fetchone returns a tuple

    title = "Test Title"
    author = "Test Author"
    year = 2024
    source_path = "/path/to/test.pdf"
    metadata = {"key": "value"}
    serialized_metadata = '{"key":"value"}' # Assuming compact serialization
    expected_id = 123
    expected_sql = """
        INSERT INTO documents (title, author, year, source_path, metadata)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """
    expected_params = (title, author, year, source_path, serialized_metadata)

    # Mock json_serialize where it's looked up in the module under test
    with patch('src.philograph.data_access.queries.documents.json_serialize', return_value=serialized_metadata) as mock_serialize:
        # Call the function under test using the mock connection
        returned_id = await doc_queries.add_document(mock_conn, title, author, year, source_path, metadata)

        # Assertions
        mock_serialize.assert_called_once_with(metadata)
        # Match exact SQL string from source
        mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
        mock_cursor.fetchone.assert_awaited_once()
        # Commit is usually handled by the connection context manager
        # mock_conn.commit.assert_awaited_once()
        assert returned_id == expected_id

@pytest.mark.asyncio
async def test_add_document_duplicate_source_path(mock_get_conn):
    """Tests adding a document with a duplicate source_path raises IntegrityError."""
    mock_conn, mock_cursor = mock_get_conn

    # Simulate psycopg.IntegrityError on execute
    mock_cursor.execute.side_effect = psycopg.IntegrityError("duplicate key value violates unique constraint")

    title = "Duplicate Title"
    author = "Duplicate Author"
    year = 2025
    source_path = "/path/to/duplicate.pdf"
    metadata = {"key": "duplicate"}
    serialized_metadata = '{"key":"duplicate"}'

    # Mock json_serialize where it's looked up
    with patch('src.philograph.data_access.queries.documents.json_serialize', return_value=serialized_metadata):
        # Expect psycopg.IntegrityError to be raised and propagated
        with pytest.raises(psycopg.IntegrityError):
            await doc_queries.add_document(mock_conn, title, author, year, source_path, metadata)

        # Assertions
        mock_cursor.execute.assert_awaited_once() # Ensure execute was called
        # Commit should not be called on error (handled by context manager)
        # mock_conn.commit.assert_not_called()

@pytest.mark.asyncio
async def test_get_document_by_id_success(mock_get_conn):
    """Tests retrieving an existing document by ID."""
    mock_conn, mock_cursor = mock_get_conn

    doc_id = 456
    db_row_tuple = (
        doc_id,
        'Found Doc',
        'Found Author',
        2023,
        '/path/found.txt',
        {'status': 'published'} # Assume DB driver handles JSONB deserialization
    )
    # Simulate fetchone returning a tuple row
    mock_cursor.fetchone.return_value = db_row_tuple

    expected_sql = "SELECT id, title, author, year, source_path, metadata FROM documents WHERE id = %s;"
    expected_params = (doc_id,)

    # Call the function under test
    document = await doc_queries.get_document_by_id(mock_conn, doc_id)

    # Assertions
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    assert document is not None
    assert isinstance(document, Document) # Check against the model from the models module
    assert document.id == doc_id
    assert document.title == db_row_tuple[1]
    assert document.author == db_row_tuple[2]
    assert document.year == db_row_tuple[3]
    assert document.source_path == db_row_tuple[4]
    assert document.metadata == db_row_tuple[5] # Check metadata mapping

@pytest.mark.asyncio
async def test_get_document_by_id_not_found(mock_get_conn):
    """Tests retrieving a non-existent document returns None."""
    mock_conn, mock_cursor = mock_get_conn

    doc_id = 999 # Non-existent ID
    # Simulate fetchone returning None when no row is found
    mock_cursor.fetchone.return_value = None

    expected_sql = "SELECT id, title, author, year, source_path, metadata FROM documents WHERE id = %s;"
    expected_params = (doc_id,)

    # Call the function under test
    document = await doc_queries.get_document_by_id(mock_conn, doc_id)

    # Assertions
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    assert document is None

@pytest.mark.asyncio
async def test_check_document_exists_true(mock_get_conn):
    """Tests check_document_exists returns True when a document exists."""
    mock_conn, mock_cursor = mock_get_conn

    source_path = "/path/exists.pdf"
    # Simulate fetchone returning (True,)
    mock_cursor.fetchone.return_value = (True,)

    expected_sql = "SELECT EXISTS (SELECT 1 FROM documents WHERE source_path = %s);"
    expected_params = (source_path,)

    # Call the function under test
    exists = await doc_queries.check_document_exists(mock_conn, source_path)

    # Assertions
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    assert exists is True

@pytest.mark.asyncio
async def test_check_document_exists_false(mock_get_conn):
    """Tests check_document_exists returns False when a document does not exist."""
    mock_conn, mock_cursor = mock_get_conn

    source_path = "/path/does_not_exist.pdf"
    # Simulate fetchone returning (False,)
    mock_cursor.fetchone.return_value = (False,)

    expected_sql = "SELECT EXISTS (SELECT 1 FROM documents WHERE source_path = %s);"
    expected_params = (source_path,)

    # Call the function under test
    exists = await doc_queries.check_document_exists(mock_conn, source_path)

    # Assertions
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    assert exists is False

# --- Test Section Operations ---

@pytest.mark.asyncio
async def test_add_section_success(mock_get_conn):
    """Tests successfully adding a section."""
    mock_conn, mock_cursor = mock_get_conn

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = (789,) # fetchone returns tuple

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
    returned_id = await doc_queries.add_section(mock_conn, doc_id, title, level, sequence)

    # Assertions
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    # Commit handled by context manager
    # mock_conn.commit.assert_awaited_once()
    assert returned_id == expected_id

@pytest.mark.asyncio
async def test_add_section_invalid_doc_id(mock_get_conn):
    """Tests adding a section with an invalid doc_id raises IntegrityError."""
    mock_conn, mock_cursor = mock_get_conn

    # Simulate psycopg.IntegrityError (foreign key violation) on execute
    mock_cursor.execute.side_effect = psycopg.IntegrityError("insert or update on table \"sections\" violates foreign key constraint")

    doc_id = 999 # Non-existent doc_id
    title = "Section Invalid Doc"
    level = 0
    sequence = 1

    # Expect psycopg.IntegrityError to be raised and propagated
    with pytest.raises(psycopg.IntegrityError):
        await doc_queries.add_section(mock_conn, doc_id, title, level, sequence)

    # Assertions
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    # Commit should not be called on error
    # mock_conn.commit.assert_not_called()

# --- Test Chunk Operations ---

@pytest.mark.asyncio
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension for test
async def test_add_chunk_success(mock_format_vector, mock_get_conn):
    """Tests successfully adding a chunk with its embedding."""
    mock_conn, mock_cursor = mock_get_conn

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = (101,) # fetchone returns tuple

    section_id = 789 # Assuming a valid section ID
    text_content = "This is a test chunk."
    sequence = 0
    embedding_vector = [0.1, 0.2, 0.3]
    formatted_embedding = "[0.1,0.2,0.3]"
    mock_format_vector.return_value = formatted_embedding # Mock the formatting

    expected_id = 101
    # Note: SQL in implementation uses %s for dimension, adjust if needed
    expected_sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    # Params should match the SQL query structure
    expected_params = (section_id, text_content, sequence, formatted_embedding)

    # Call the function under test
    returned_id = await doc_queries.add_chunk(mock_conn, section_id, text_content, sequence, embedding_vector)

    # Assertions
    mock_format_vector.assert_called_once_with(embedding_vector)
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    # mock_conn.commit.assert_awaited_once() # Commit handled by context manager
    assert returned_id == expected_id

# Note: Dimension check might be moved outside DB layer in refactored code.
# If add_chunk still performs the check, keep this test. Otherwise, remove/move it.
# @pytest.mark.asyncio
# @patch('src.philograph.config.EMBEDDING_DIMENSION', 3) # Mock dimension for test
# async def test_add_chunk_invalid_dimension(mock_get_conn):
#     """Tests adding a chunk with incorrect embedding dimension raises ValueError."""
#     mock_conn, mock_cursor = mock_get_conn
#
#     section_id = 789
#     text_content = "Chunk with wrong dimension."
#     sequence = 1
#     embedding_vector = [0.1, 0.2] # Incorrect dimension (2 instead of 3)
#
#     # Expect ValueError to be raised (assuming check remains in add_chunk)
#     with pytest.raises(ValueError, match="Embedding vector dimension mismatch"):
#         await doc_queries.add_chunk(mock_conn, section_id, text_content, sequence, embedding_vector)
#
#     # Ensure commit was not called
#     # mock_conn.commit.assert_not_called()

@pytest.mark.asyncio
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension for test
async def test_add_chunks_batch_success(mock_format_vector, mock_get_conn):
    """Tests successfully adding multiple chunks in a batch."""
    mock_conn, mock_cursor = mock_get_conn

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
        VALUES (%s, %s, %s, %s);
    """
    # Params for executemany should match the data structure
    expected_params_list = [
        (789, "Chunk 1", 0, formatted_embeddings[0]),
        (789, "Chunk 2", 1, formatted_embeddings[1]),
        (790, "Chunk 3", 0, formatted_embeddings[2]),
    ]
    # Simulate rowcount after executemany
    mock_cursor.rowcount = len(chunks_data)

    # Call the function under test
    await doc_queries.add_chunks_batch(mock_conn, chunks_data)

    # Assertions
    assert mock_format_vector.call_count == len(chunks_data)
    # Match exact SQL string from source
    mock_cursor.executemany.assert_awaited_once_with(expected_sql, expected_params_list)
    # mock_conn.commit.assert_awaited_once() # Commit handled by context manager

@pytest.mark.asyncio
async def test_add_chunks_batch_empty_list(mock_get_conn):
    """Tests that adding an empty list of chunks does nothing."""
    mock_conn, mock_cursor = mock_get_conn

    chunks_data = []

    # Call the function under test
    await doc_queries.add_chunks_batch(mock_conn, chunks_data)

    # Assertions
    mock_cursor.executemany.assert_not_awaited()
    # mock_conn.commit.assert_not_called() # Commit not called if nothing executed

# Note: Dimension check might be moved outside DB layer. Remove/move if needed.
# @pytest.mark.asyncio
# @patch('src.philograph.config.EMBEDDING_DIMENSION', 3) # Mock dimension for test
# async def test_add_chunks_batch_invalid_dimension(mock_get_conn):
#     """Tests adding chunks with incorrect embedding dimension in batch raises ValueError."""
#     mock_conn, mock_cursor = mock_get_conn
#
#     chunks_data = [
#         (789, "Chunk 1", 0, [0.1, 0.2, 0.3]),
#         (789, "Chunk 2", 1, [0.4, 0.5]), # Incorrect dimension
#     ]
#
#     # Expect ValueError to be raised (assuming check remains in add_chunks_batch)
#     with pytest.raises(ValueError, match="Embedding vector dimension mismatch in batch"):
#         await doc_queries.add_chunks_batch(mock_conn, chunks_data)
#
#     # Ensure commit was not called
#     # mock_conn.commit.assert_not_called()

@pytest.mark.asyncio
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Mock dimension for test
async def test_add_chunks_batch_db_error(mock_format_vector, mock_get_conn):
    """Tests that a database error during batch insert prevents commit."""
    mock_conn, mock_cursor = mock_get_conn

    chunks_data = [
        (789, "Chunk 1", 0, [0.1, 0.2, 0.3]),
        (999, "Chunk Invalid FK", 0, [0.7, 0.8, 0.9]), # Assume 999 is invalid section_id
    ]
    formatted_embeddings = ["[0.1,0.2,0.3]", "[0.7,0.8,0.9]"]
    mock_format_vector.side_effect = formatted_embeddings

    # Simulate psycopg.IntegrityError on executemany
    db_error = psycopg.IntegrityError("FK constraint violation")
    mock_cursor.executemany.side_effect = db_error

    expected_sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s);
    """
    expected_params_list = [
        (789, "Chunk 1", 0, formatted_embeddings[0]),
        (999, "Chunk Invalid FK", 0, formatted_embeddings[1]),
    ]

    # Expect psycopg.IntegrityError to be raised and propagated
    with pytest.raises(psycopg.IntegrityError):
        await doc_queries.add_chunks_batch(mock_conn, chunks_data)

    # Assertions
    assert mock_format_vector.call_count == len(chunks_data)
    # Match exact SQL string from source
    mock_cursor.executemany.assert_awaited_once_with(expected_sql, expected_params_list)
    # mock_conn.commit.assert_not_called() # Commit not called on error

@pytest.mark.asyncio
async def test_get_chunk_by_id_success(mock_get_conn):
    """Tests retrieving an existing chunk by ID."""
    mock_conn, mock_cursor = mock_get_conn
    chunk_id = 101
    db_row_tuple = (chunk_id, 789, "This is a test chunk.", 0)
    mock_cursor.fetchone.return_value = db_row_tuple

    expected_sql = "SELECT id, section_id, text_content, sequence FROM chunks WHERE id = %s;"
    expected_params = (chunk_id,)

    chunk_data = await doc_queries.get_chunk_by_id(mock_conn, chunk_id)

    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    assert chunk_data == {
        "id": db_row_tuple[0],
        "section_id": db_row_tuple[1],
        "text_content": db_row_tuple[2],
        "sequence": db_row_tuple[3],
    }

@pytest.mark.asyncio
async def test_get_chunk_by_id_not_found(mock_get_conn):
    """Tests retrieving a non-existent chunk returns None."""
    mock_conn, mock_cursor = mock_get_conn
    chunk_id = 999
    mock_cursor.fetchone.return_value = None

    expected_sql = "SELECT id, section_id, text_content, sequence FROM chunks WHERE id = %s;"
    expected_params = (chunk_id,)

    chunk_data = await doc_queries.get_chunk_by_id(mock_conn, chunk_id)

    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    assert chunk_data is None