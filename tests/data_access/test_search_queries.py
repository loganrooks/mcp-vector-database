import pytest
import psycopg
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any, Optional

# Import function from the new queries module
from src.philograph.data_access.queries import search as search_queries
# Import models if needed for type hints or assertions
from src.philograph.data_access.models import SearchResult
# Import config if needed (e.g., for embedding dimension)
from src.philograph import config
# Import utility functions if used directly in tests (though mocks are preferred)
from src.philograph.utils import db_utils

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

@pytest.fixture
def mock_format_vector(mocker):
    """Fixture to mock the format_vector_for_pgvector utility where it's used."""
    # Patch the function where it's looked up (in the search queries module)
    return mocker.patch('src.philograph.data_access.queries.search.format_vector_for_pgvector')

# --- Test Vector Search Operations ---

@pytest.mark.asyncio
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Corrected config var
async def test_vector_search_chunks_success(mock_format_vector, mock_get_conn):
    """Tests basic vector search returns correctly mapped SearchResult objects."""
    mock_conn, mock_cursor = mock_get_conn

    query_embedding = [1.1, 2.2, 3.3]
    formatted_query_embedding = "[1.1,2.2,3.3]"
    mock_format_vector.return_value = formatted_query_embedding
    top_k = 2

    # Simulate database results (list of tuples matching SELECT order)
    db_results_tuples = [
        (101, 789, 123, 'Chunk A', 0.123, 'Doc X', 'Auth X', 2020, '/path/x.pdf', 'Sec 1', 0),
        (105, 790, 124, 'Chunk B', 0.456, 'Doc Y', 'Auth Y', 2021, '/path/y.txt', 'Sec 2', 1)
    ]
    mock_cursor.fetchall.return_value = db_results_tuples

    # Construct expected SQL (adjust based on actual implementation in search_queries.py)
    expected_base_sql = """
        SELECT
            c.id as chunk_id,
            c.section_id,
            s.doc_id,
            c.text_content,
            c.embedding <=> %s AS distance,
            d.title as doc_title,
            d.author as doc_author,
            d.year as doc_year,
            d.source_path as doc_source_path,
            s.title as section_title,
            c.sequence as chunk_sequence
        FROM chunks c
        JOIN sections s ON c.section_id = s.id
        JOIN documents d ON s.doc_id = d.id
    """
    # Adjusted to match the $N placeholder style used in the implementation
    expected_sql = f"{expected_base_sql.strip()} ORDER BY distance LIMIT $2"
    expected_params = [formatted_query_embedding, top_k] # Use list for $N params

    # Call the function under test
    search_results = await search_queries.vector_search_chunks(mock_conn, query_embedding, top_k)

    # Assertions
    mock_format_vector.assert_called_once_with(query_embedding)
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(search_results) == top_k
    assert all(isinstance(res, SearchResult) for res in search_results)
    # Check mapping for the first result
    assert search_results[0].chunk_id == db_results_tuples[0][0]
    assert search_results[0].text_content == db_results_tuples[0][3]
    assert search_results[0].doc_title == db_results_tuples[0][5]
    assert search_results[0].distance == db_results_tuples[0][4]

@pytest.mark.asyncio
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Corrected config var
async def test_vector_search_chunks_with_filters(mock_format_vector, mock_get_conn):
    """Tests vector search with metadata filters."""
    mock_conn, mock_cursor = mock_get_conn

    query_embedding = [0.1, 0.2, 0.3]
    formatted_query_embedding = "[0.1,0.2,0.3]"
    mock_format_vector.return_value = formatted_query_embedding
    top_k = 5
    filters = {"author": "Test Author", "year": 2023, "doc_id": 123}

    # Simulate database results (empty for simplicity, focus is on query construction)
    mock_cursor.fetchall.return_value = []

    # Construct expected SQL (adjust based on actual implementation in search_queries.py)
    expected_base_sql = """
        SELECT
            c.id as chunk_id,
            c.section_id,
            s.doc_id,
            c.text_content,
            c.embedding <=> %s AS distance,
            d.title as doc_title,
            d.author as doc_author,
            d.year as doc_year,
            d.source_path as doc_source_path,
            s.title as section_title,
            c.sequence as chunk_sequence
        FROM chunks c
        JOIN sections s ON c.section_id = s.id
        JOIN documents d ON s.doc_id = d.id
    """
    # Adjusted to match the $N placeholder style used in the implementation
    expected_where = " WHERE d.author ILIKE $2 AND d.year = $3 AND d.id = $4"
    expected_order_limit = " ORDER BY distance LIMIT $5"
    expected_full_sql = expected_base_sql.strip() + expected_where + expected_order_limit

    # Parameters for $N placeholders: embedding, author, year, doc_id, top_k
    expected_params = [
        formatted_query_embedding,
        f"%{filters['author']}%",
        filters['year'],
        filters['doc_id'],
        top_k
    ]

    # Call the function under test
    await search_queries.vector_search_chunks(mock_conn, query_embedding, top_k, filters)

    # Assertions
    mock_format_vector.assert_called_once_with(query_embedding)
    # Check the constructed SQL and parameters
    mock_cursor.execute.assert_awaited_once_with(expected_full_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()

# Note: Dimension check might be moved outside DB layer. Remove/move if needed.
# @pytest.mark.asyncio
# @patch('src.philograph.config.EMBEDDING_DIMENSION', 3) # Mock dimension
# async def test_vector_search_chunks_invalid_dimension(mock_get_conn):
#     """Tests vector search with incorrect query embedding dimension raises ValueError."""
#     mock_conn, mock_cursor = mock_get_conn
#
#     query_embedding = [0.1, 0.2] # Incorrect dimension (2 instead of 3)
#     top_k = 5
#
#     # Expect ValueError to be raised (assuming check remains)
#     with pytest.raises(ValueError, match="Query embedding dimension mismatch"):
#         await search_queries.vector_search_chunks(mock_conn, query_embedding, top_k)

@pytest.mark.asyncio
async def test_vector_search_chunks_empty_embedding(mock_get_conn):
    """Tests vector search with an empty query embedding raises ValueError."""
    mock_conn, mock_cursor = mock_get_conn

    query_embedding = [] # Empty embedding
    top_k = 5

    # Expect ValueError to be raised (assuming check remains)
    with pytest.raises(ValueError, match="Query embedding cannot be empty."):
        await search_queries.vector_search_chunks(mock_conn, query_embedding, top_k)

@pytest.mark.asyncio
@patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', 3) # Corrected config var
async def test_vector_search_chunks_db_error(mock_format_vector, mock_get_conn):
    """Tests that vector search propagates database errors."""
    mock_conn, mock_cursor = mock_get_conn

    query_embedding = [1.1, 2.2, 3.3]
    formatted_query_embedding = "[1.1,2.2,3.3]"
    mock_format_vector.return_value = formatted_query_embedding
    top_k = 2

    # Simulate psycopg.Error on execute
    db_error = psycopg.Error("Simulated DB error during search")
    mock_cursor.execute.side_effect = db_error

    # Expect RuntimeError (as implemented in search_queries.py) wrapping the DB error
    with pytest.raises(RuntimeError, match="Database error during vector search"):
        await search_queries.vector_search_chunks(mock_conn, query_embedding, top_k)

    # Assertions
    mock_format_vector.assert_called_once_with(query_embedding)
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    mock_cursor.fetchall.assert_not_awaited() # Fetch should not be called on error