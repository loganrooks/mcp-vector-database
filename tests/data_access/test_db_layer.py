import pytest
import psycopg
import json
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from pathlib import Path # Added Path

# Mock config before importing db_layer
# Set a dummy dimension for testing vector formatting/validation
MOCK_TARGET_DIMENSION = 4
with patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', MOCK_TARGET_DIMENSION), \
     patch('src.philograph.config.ASYNC_DATABASE_URL', "postgresql+psycopg_async://mock_user:mock_pass@mock_host:5432/mock_db"):
    from src.philograph.data_access import db_layer
    from src.philograph.data_access.db_layer import Document, Section, Chunk, SearchResult, Relationship # Import models for type hints
    # Import the actual pool class for spec checks
    from psycopg_pool import AsyncConnectionPool as ActualPoolClass

from psycopg_pool import AsyncConnectionPool as ActualPoolClass


# Helper mock class for async context managers based on blog post
# https://pfertyk.me/2017/06/testing-asynchronous-context-managers-in-python/
class AsyncContextManagerMock(MagicMock):
    async def __aenter__(self):
        # Allows configuring what __aenter__ returns or raises
        if hasattr(self, 'aenter_effect'):
             # Raise an exception if side_effect is set
            if isinstance(self.aenter_effect, Exception):
                raise self.aenter_effect
            # Otherwise, return the configured value
            return self.aenter_effect
        # Default return value if not configured
        return self

    async def __aexit__(self, *args):
        pass # Basic implementation, can be enhanced if needed


# --- Test Fixtures ---

@pytest.fixture
def mock_conn():
    """Provides a mock async connection object with a working async cursor context manager."""
    conn = AsyncMock(spec=psycopg.AsyncConnection)

    # Mock the cursor itself
    mock_cur = AsyncMock(spec=psycopg.AsyncCursor)

    # Mock the async context manager returned by cursor()
    mock_cursor_cm = AsyncMock()
    mock_cursor_cm.__aenter__.return_value = mock_cur # __aenter__ returns the cursor mock

    # Make conn.cursor() return the context manager mock
    conn.cursor.return_value = mock_cursor_cm

    return conn

@pytest.fixture(autouse=True)
@pytest.mark.asyncio
async def manage_pool():
    """Fixture to manage the db_pool lifecycle for tests."""
    # Ensure pool is reset before each test
    db_layer.db_pool = None
    yield
    # Clean up pool after tests if it was created
    await db_layer.close_db_pool()
    db_layer.db_pool = None

# --- Test Cases ---

# == Connection Management ==

@patch('src.philograph.data_access.db_layer.AsyncConnectionPool')
@pytest.mark.asyncio
async def test_get_db_pool_success(mock_pool_constructor):
    """Test successful pool initialization."""
    # Mock the pool and its connection test
    mock_pool_instance = AsyncMock(spec=ActualPoolClass)
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cur = AsyncMock(spec=psycopg.AsyncCursor)

    # Configure the mock connection's cursor context manager
    mock_cursor_cm = AsyncMock()
    mock_cursor_cm.__aenter__.return_value = mock_cur
    mock_conn.cursor.return_value = mock_cursor_cm

    # Configure the mock pool's connection context manager
    mock_pool_conn_cm = AsyncMock() # Mock for the pool's connection CM
    mock_pool_conn_cm.__aenter__.return_value = mock_conn
    mock_pool_instance.connection.return_value = mock_pool_conn_cm # connection() returns the CM

    mock_pool_constructor.return_value = mock_pool_instance

    pool = await db_layer.get_db_pool()
    assert pool is mock_pool_instance
    mock_pool_constructor.assert_called_once()
    mock_pool_instance.connection.assert_called_once() # Check connection() method was called
    mock_pool_conn_cm.__aenter__.assert_awaited_once() # Check CM was entered
    mock_cur.execute.assert_called_once_with("SELECT 1")

# Patch AsyncConnectionPool where it's used in the db_layer module
@patch('src.philograph.data_access.db_layer.AsyncConnectionPool')
@pytest.mark.asyncio
async def test_get_db_pool_failure(mock_pool_constructor):
    """Test pool initialization failure during the connection test (SELECT 1)."""
    # Mock the pool instance returned by the constructor
    mock_pool_instance = AsyncMock(spec=ActualPoolClass)
    mock_pool_constructor.return_value = mock_pool_instance

    # Mock the connection context manager returned by pool.connection()
    mock_pool_conn_cm = AsyncMock()
    mock_pool_instance.connection.return_value = mock_pool_conn_cm

    # Mock the connection object returned by the connection CM's __aenter__
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_pool_conn_cm.__aenter__.return_value = mock_conn

    # Mock the cursor context manager returned by conn.cursor()
    mock_cursor_cm = AsyncMock()
    mock_conn.cursor.return_value = mock_cursor_cm

    # Mock the cursor object returned by the cursor CM's __aenter__
    mock_cur = AsyncMock(spec=psycopg.AsyncCursor)
    mock_cursor_cm.__aenter__.return_value = mock_cur

    # Configure the mock cursor's execute method to raise the error
    mock_cur.execute.side_effect = psycopg.OperationalError("SELECT 1 failed")

    # The except block in get_db_pool should catch the OperationalError and raise ConnectionError
    with pytest.raises(ConnectionError, match="Database connection pool initialization failed"):
        await db_layer.get_db_pool()

    # Verify the call chain
    mock_pool_constructor.assert_called_once()
    mock_pool_instance.connection.assert_called_once()
    mock_pool_conn_cm.__aenter__.assert_awaited_once()
    mock_conn.cursor.assert_called_once()
    mock_cursor_cm.__aenter__.assert_awaited_once()
    mock_cur.execute.assert_called_once_with("SELECT 1")

@pytest.mark.asyncio
async def test_get_db_connection(mock_conn):
    """Test getting a connection from the pool."""
    # Mock the pool first
    mock_pool = AsyncMock(spec=ActualPoolClass) # Use correct spec
    mock_pool_conn_cm = AsyncMock() # Mock for the pool's connection CM
    mock_pool_conn_cm.__aenter__.return_value = mock_conn
    mock_pool.connection.return_value = mock_pool_conn_cm # connection() returns the CM
    db_layer.db_pool = mock_pool # Inject mock pool

    async with db_layer.get_db_connection() as conn:
        assert conn is mock_conn
    mock_pool.connection.assert_called_once()
    mock_pool_conn_cm.__aenter__.assert_awaited_once() # Check CM was entered

# == Utility Functions ==

def test_format_vector_for_pgvector():
    """Test vector formatting."""
    vector = [1.0, 2.5, -3.0, 0.0]
    assert db_layer.format_vector_for_pgvector(vector) == '[1.0,2.5,-3.0,0.0]'

def test_format_vector_for_pgvector_invalid_type():
    """Test vector formatting with invalid input type."""
    with pytest.raises(TypeError):
        db_layer.format_vector_for_pgvector("not a list") # type: ignore
    with pytest.raises(TypeError):
        db_layer.format_vector_for_pgvector([1.0, "a", 3.0]) # type: ignore

def test_json_serialize():
    """Test JSON serialization."""
    data = {"key": "value", "list": [1, 2]}
    assert db_layer.json_serialize(data) == '{"key": "value", "list": [1, 2]}'
    assert db_layer.json_serialize(None) is None

# == Document Operations ==

@pytest.mark.asyncio
async def test_add_document_success(mock_conn):
    """Test adding a document successfully."""
    mock_cursor = mock_conn.cursor.return_value.__aenter__.return_value # Get cursor from context manager mock
    mock_cursor.fetchone.return_value = {'id': 123} # Simulate RETURNING id

    doc_id = await db_layer.add_document(
        mock_conn, "Test Title", "Test Author", 2024, "test/path.pdf", {"tag": "test"}
    )

    assert doc_id == 123
    expected_sql = """
        INSERT INTO documents (title, author, year, source_path, metadata_jsonb)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """
    expected_params = ("Test Title", "Test Author", 2024, "test/path.pdf", '{"tag": "test"}')
    mock_cursor.execute.assert_called_once_with(expected_sql, expected_params)
    mock_conn.commit.assert_called_once()

@pytest.mark.asyncio
async def test_add_document_db_error(mock_conn):
    """Test handling database error during document add."""
    mock_cursor = mock_conn.cursor.return_value.__aenter__.return_value # Get cursor from context manager mock
    mock_cursor.execute.side_effect = psycopg.DatabaseError("DB insert failed")

    # Expect the original psycopg.DatabaseError as it's re-raised by get_db_connection
    with pytest.raises(psycopg.DatabaseError, match="DB insert failed"):
        await db_layer.add_document(
            mock_conn, "Test Title", "Test Author", 2024, "test/path.pdf", {"tag": "test"}
        )
    mock_conn.commit.assert_not_called() # Should not commit on error

@pytest.mark.asyncio
async def test_get_document_by_id_found(mock_conn):
    """Test retrieving an existing document."""
    mock_cursor = mock_conn.cursor.return_value.__aenter__.return_value # Get cursor from context manager mock
    mock_row = {
        'id': 1, 'title': 'Found Doc', 'author': 'Author', 'year': 2023,
        'source_path': 'found/doc.pdf', 'metadata_jsonb': {'key': 'value'}
    }
    mock_cursor.fetchone.return_value = mock_row

    document = await db_layer.get_document_by_id(mock_conn, 1)

    assert document is not None
    assert isinstance(document, Document)
    assert document.id == 1
    assert document.title == 'Found Doc'
    assert document.metadata == {'key': 'value'}
    mock_cursor.execute.assert_called_once_with(
        "SELECT id, title, author, year, source_path, metadata_jsonb FROM documents WHERE id = %s;", (1,)
    )

@pytest.mark.asyncio
async def test_get_document_by_id_not_found(mock_conn):
    """Test retrieving a non-existent document."""
    mock_cursor = mock_conn.cursor.return_value.__aenter__.return_value # Get cursor from context manager mock
    mock_cursor.fetchone.return_value = None

    document = await db_layer.get_document_by_id(mock_conn, 999)

    assert document is None
    mock_cursor.execute.assert_called_once_with(
        "SELECT id, title, author, year, source_path, metadata_jsonb FROM documents WHERE id = %s;", (999,)
    )

@pytest.mark.asyncio
async def test_check_document_exists_true(mock_conn):
    """Test checking for an existing document."""
    mock_cursor = mock_conn.cursor.return_value.__aenter__.return_value # Get cursor from context manager mock
    mock_cursor.fetchone.return_value = {'exists': True}

    exists = await db_layer.check_document_exists(mock_conn, "existing/path.pdf")

    assert exists is True
    mock_cursor.execute.assert_called_once_with(
        "SELECT EXISTS(SELECT 1 FROM documents WHERE source_path = %s);", ("existing/path.pdf",)
    )

@pytest.mark.asyncio
async def test_check_document_exists_false(mock_conn):
    """Test checking for a non-existent document."""
    mock_cursor = mock_conn.cursor.return_value.__aenter__.return_value # Get cursor from context manager mock
    mock_cursor.fetchone.return_value = {'exists': False}

    exists = await db_layer.check_document_exists(mock_conn, "missing/path.pdf")

    assert exists is False
    mock_cursor.execute.assert_called_once_with(
        "SELECT EXISTS(SELECT 1 FROM documents WHERE source_path = %s);", ("missing/path.pdf",)
    )

# (Tests for Section, Chunk, Reference, Search, Relationship, Collection ops to follow)