import pytest
import psycopg
import json
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from pathlib import Path # Added Path

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# Mock config before importing db_layer
# Set a dummy dimension for testing vector formatting/validation
MOCK_TARGET_DIMENSION = 4
with patch('src.philograph.config.TARGET_EMBEDDING_DIMENSION', MOCK_TARGET_DIMENSION), \
     patch('src.philograph.config.ASYNC_DATABASE_URL', "postgresql+psycopg_async://mock_user:mock_pass@mock_host:5432/mock_db"):
    from src.philograph.data_access import db_layer
    from src.philograph.data_access.db_layer import Document, Section, Chunk, SearchResult, Relationship # Import models for type hints

# --- Test Fixtures ---

@pytest.fixture
def mock_conn():
    """Provides a mock async connection object."""
    conn = AsyncMock(spec=psycopg.AsyncConnection)
    conn.cursor = AsyncMock() # Make cursor() return an AsyncMock
    # Configure the cursor context manager
    mock_cur = AsyncMock(spec=psycopg.AsyncCursor)
    mock_cur.__aenter__.return_value = mock_cur # Return self for async with
    conn.cursor.return_value = mock_cur
    return conn

@pytest.fixture(autouse=True)
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
async def test_get_db_pool_success(mock_pool_constructor):
    """Test successful pool initialization."""
    # Mock the pool and its connection test
    mock_pool_instance = AsyncMock(spec=db_layer.AsyncConnectionPool)
    mock_conn = AsyncMock()
    mock_cur = AsyncMock()
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cur # Configure context manager
    mock_pool_instance.connection.return_value.__aenter__.return_value = mock_conn # Configure context manager
    mock_pool_constructor.return_value = mock_pool_instance

    pool = await db_layer.get_db_pool()
    assert pool is mock_pool_instance
    mock_pool_constructor.assert_called_once()
    mock_pool_instance.connection.assert_called_once() # Check connection test was attempted
    mock_cur.execute.assert_called_once_with("SELECT 1")

@patch('src.philograph.data_access.db_layer.AsyncConnectionPool', side_effect=psycopg.OperationalError("Connection failed"))
async def test_get_db_pool_failure(mock_pool_constructor):
    """Test pool initialization failure."""
    with pytest.raises(ConnectionError, match="Database connection pool initialization failed"):
        await db_layer.get_db_pool()
    mock_pool_constructor.assert_called_once()

async def test_get_db_connection(mock_conn):
    """Test getting a connection from the pool."""
    # Mock the pool first
    mock_pool = AsyncMock(spec=db_layer.AsyncConnectionPool)
    mock_pool.connection.return_value.__aenter__.return_value = mock_conn
    db_layer.db_pool = mock_pool # Inject mock pool

    async with db_layer.get_db_connection() as conn:
        assert conn is mock_conn
    mock_pool.connection.assert_called_once()

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

async def test_add_document_success(mock_conn):
    """Test adding a document successfully."""
    mock_cursor = mock_conn.cursor.return_value
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

async def test_add_document_db_error(mock_conn):
    """Test handling database error during document add."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.side_effect = psycopg.DatabaseError("DB insert failed")

    with pytest.raises(RuntimeError, match="DB document insert failed"):
        await db_layer.add_document(
            mock_conn, "Test Title", "Test Author", 2024, "test/path.pdf", {"tag": "test"}
        )
    mock_conn.commit.assert_not_called() # Should not commit on error

async def test_get_document_by_id_found(mock_conn):
    """Test retrieving an existing document."""
    mock_cursor = mock_conn.cursor.return_value
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

async def test_get_document_by_id_not_found(mock_conn):
    """Test retrieving a non-existent document."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchone.return_value = None

    document = await db_layer.get_document_by_id(mock_conn, 999)

    assert document is None
    mock_cursor.execute.assert_called_once_with(
        "SELECT id, title, author, year, source_path, metadata_jsonb FROM documents WHERE id = %s;", (999,)
    )

async def test_check_document_exists_true(mock_conn):
    """Test checking for an existing document."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchone.return_value = {'exists': True}

    exists = await db_layer.check_document_exists(mock_conn, "existing/path.pdf")

    assert exists is True
    mock_cursor.execute.assert_called_once_with(
        "SELECT EXISTS(SELECT 1 FROM documents WHERE source_path = %s);", ("existing/path.pdf",)
    )

async def test_check_document_exists_false(mock_conn):
    """Test checking for a non-existent document."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchone.return_value = {'exists': False}

    exists = await db_layer.check_document_exists(mock_conn, "missing/path.pdf")

    assert exists is False
    mock_cursor.execute.assert_called_once_with(
        "SELECT EXISTS(SELECT 1 FROM documents WHERE source_path = %s);", ("missing/path.pdf",)
    )

# (Tests for Section, Chunk, Reference, Search, Relationship, Collection ops to follow)