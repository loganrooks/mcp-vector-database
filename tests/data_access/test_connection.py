import pytest
import psycopg
from unittest.mock import AsyncMock, MagicMock, patch
from psycopg_pool import AsyncConnectionPool

# Import functions from the new connection module
from src.philograph.data_access import connection as db_connection
from src.philograph import config # Assuming config is needed for URLs etc.

# --- Test Connection Management ---

@pytest.mark.asyncio
@patch('src.philograph.data_access.connection.AsyncConnectionPool', new_callable=MagicMock) # Patch the new location
async def test_get_db_pool_success_first_call(mock_pool_class):
    """Tests successful pool creation on the first call."""
    # Reset global pool for isolation
    db_connection.pool = None

    # Configure mocks
    mock_pool_instance = AsyncMock(spec=AsyncConnectionPool)
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)

    # Configure context managers
    mock_pool_instance.connection.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,) # Simulate successful SELECT 1

    # Configure the class mock to return the instance
    mock_pool_class.return_value = mock_pool_instance

    # Call the function
    pool = await db_connection.get_db_pool()

    # Assertions
    assert pool is mock_pool_instance
    mock_pool_class.assert_called_once() # Check pool was initialized
    mock_pool_instance.connection.assert_called_once() # Check connection test was attempted
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_awaited_once_with("SELECT 1")
    assert db_connection.pool is mock_pool_instance # Check global variable is set

    # Clean up global state
    db_connection.pool = None


@pytest.mark.asyncio
@patch('src.philograph.data_access.connection.AsyncConnectionPool', new_callable=MagicMock) # Patch the new location
async def test_get_db_pool_returns_existing_pool(mock_pool_class):
    """Tests that an existing pool is returned on subsequent calls."""
    # Reset global pool for isolation
    db_connection.pool = None

    # Mock successful first call
    mock_pool_instance = AsyncMock(spec=AsyncConnectionPool)
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_pool_instance.connection.return_value.__aenter__.return_value = mock_conn
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,) # Simulate successful SELECT 1
    mock_pool_class.return_value = mock_pool_instance

    # First call
    pool1 = await db_connection.get_db_pool()
    assert pool1 is mock_pool_instance
    mock_pool_class.assert_called_once() # Pool class initialized only once

    # Reset mock call count for the class before second call
    mock_pool_class.reset_mock()

    # Second call
    pool2 = await db_connection.get_db_pool()

    # Assertions
    assert pool2 is pool1 # Should be the same instance
    mock_pool_class.assert_not_called() # Pool class should NOT be called again

    # Clean up global state
    db_connection.pool = None


@pytest.mark.asyncio
@patch('src.philograph.data_access.connection.AsyncConnectionPool', new_callable=MagicMock) # Patch the new location
async def test_get_db_pool_failure(mock_pool_class):
    """Tests that RuntimeError is raised if pool initialization fails."""
    # Reset global pool for isolation
    db_connection.pool = None

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

    # Expect RuntimeError to be raised (as implemented in connection.py)
    # Match the start of the error message, allowing for the appended original error
    with pytest.raises(RuntimeError, match="Failed to initialize database connection pool"): # Removed colon
        await db_connection.get_db_pool()

    # Assert pool was attempted to be created but failed
    mock_pool_class.assert_called_once()
    assert db_connection.pool is None # Pool should not be set globally on failure

    # Clean up global state just in case (though it should be None)
    db_connection.pool = None


@pytest.mark.asyncio
@patch('src.philograph.data_access.connection.get_db_pool') # Patch the new location
async def test_get_db_connection_success(mock_get_pool):
    """Tests successfully getting a connection from the pool."""
    mock_pool = AsyncMock(spec=AsyncConnectionPool)
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_get_pool.return_value = mock_pool # Mock get_db_pool to return our mock pool

    # Configure the pool's connection context manager
    mock_pool.connection.return_value.__aenter__.return_value = mock_conn

    async with db_connection.get_db_connection() as conn:
        assert conn is mock_conn # Check the correct connection is yielded

    mock_get_pool.assert_awaited_once()
    mock_pool.connection.assert_called_once() # Check pool.connection() was used


@pytest.mark.asyncio
@patch('src.philograph.data_access.connection.get_db_pool') # Patch the new location
async def test_get_db_connection_pool_error(mock_get_pool):
    """Tests that an error during pool retrieval propagates."""
    # Simulate get_db_pool raising an error
    mock_get_pool.side_effect = RuntimeError("Database pool is not initialized.")

    with pytest.raises(RuntimeError, match="Database pool is not initialized."):
        async with db_connection.get_db_connection() as conn:
            pass # Should not reach here

    mock_get_pool.assert_awaited_once()


@pytest.mark.asyncio
@patch('src.philograph.data_access.connection.get_db_pool') # Patch the new location
async def test_get_db_connection_psycopg_error(mock_get_pool):
    """Tests that psycopg errors within the context are re-raised."""
    mock_pool = AsyncMock(spec=AsyncConnectionPool)
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_get_pool.return_value = mock_pool

    # Configure the pool's connection context manager
    mock_pool.connection.return_value.__aenter__.return_value = mock_conn

    simulated_error = psycopg.ProgrammingError("Syntax error")

    with pytest.raises(psycopg.ProgrammingError, match="Syntax error"):
        async with db_connection.get_db_connection() as conn:
            # Simulate an error occurring while using the connection
            raise simulated_error

    mock_get_pool.assert_awaited_once()
    mock_pool.connection.assert_called_once()


@pytest.mark.asyncio
async def test_close_db_pool_closes_existing_pool():
    """Tests that close_db_pool closes an existing pool and resets the global."""
    # Setup a mock pool in the global variable
    mock_pool_instance = AsyncMock(spec=AsyncConnectionPool)
    db_connection.pool = mock_pool_instance

    await db_connection.close_db_pool()

    # Assertions
    mock_pool_instance.close.assert_awaited_once()
    assert db_connection.pool is None


@pytest.mark.asyncio
async def test_close_db_pool_no_pool():
    """Tests that close_db_pool does nothing if the pool is already None."""
    # Ensure global pool is None
    db_connection.pool = None

    # Call close_db_pool - it should not raise an error or try to close anything
    await db_connection.close_db_pool()

    # Assert the pool remains None
    assert db_connection.pool is None

# Schema initialization tests will be added here later
# --- Test Schema Initialization ---

@pytest.mark.asyncio
@patch('src.philograph.data_access.connection.get_db_connection') # Patch new location
async def test_initialize_schema_success(mock_get_conn):
    """Tests that initialize_schema executes all expected SQL commands."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    # Simulate context manager for get_db_connection if it's used directly
    # If initialize_schema takes conn directly, this mock setup is simpler:
    # mock_get_conn.return_value = mock_conn # If get_db_connection returns conn directly
    # If it's a context manager:
    mock_get_conn.return_value.__aenter__.return_value = mock_conn # Assuming get_db_connection is context manager

    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Call the function under test (using the new module path)
    await db_connection.initialize_schema(mock_conn)

    # Assertions
    # Check that execute was called multiple times (at least for each CREATE statement)
    # The exact number depends on the final schema definition
    assert mock_cursor.execute.await_count >= 10 # Adjust if needed

    # Check specific statements were executed using exact multi-line strings from source
    mock_cursor.execute.assert_any_await("CREATE EXTENSION IF NOT EXISTS vector;")
    # Exact match for documents table
    mock_cursor.execute.assert_any_await("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title TEXT,
                author TEXT,
                year INTEGER,
                source_path TEXT UNIQUE NOT NULL,
                metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
    # Exact match for sections table
    mock_cursor.execute.assert_any_await("""
            CREATE TABLE IF NOT EXISTS sections (
                id SERIAL PRIMARY KEY,
                doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                title TEXT,
                level INTEGER,
                sequence INTEGER NOT NULL, -- Order within the document
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (doc_id, sequence) -- Ensure sequence is unique within a document
            );
        """)
    # Exact match for chunks table (using f-string as in source)
    mock_cursor.execute.assert_any_await(f"""
            CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
                text_content TEXT NOT NULL,
                sequence INTEGER NOT NULL, -- Order within the section
                embedding vector({config.TARGET_EMBEDDING_DIMENSION}), -- Use dimension from config
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (section_id, sequence) -- Ensure sequence is unique within a section
            );
        """)
    # Exact match for relationships table
    mock_cursor.execute.assert_any_await("""
            CREATE TABLE IF NOT EXISTS relationships (
                id SERIAL PRIMARY KEY,
                source_node_id TEXT NOT NULL, -- e.g., 'chunk:123', 'doc:45'
                target_node_id TEXT NOT NULL, -- e.g., 'chunk:456', 'concept:logic'
                relation_type VARCHAR(255) NOT NULL, -- e.g., 'cites', 'explains', 'contradicts'
                metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (source_node_id, target_node_id, relation_type) -- Prevent duplicate relationships
            );
        """)
    # Exact match for collections table
    mock_cursor.execute.assert_any_await("""
            CREATE TABLE IF NOT EXISTS collections (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
    # Exact match for collection_items table
    mock_cursor.execute.assert_any_await("""
            CREATE TABLE IF NOT EXISTS collection_items (
                collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
                item_type VARCHAR(50) NOT NULL CHECK (item_type IN ('document', 'chunk')), -- 'section' could be added
                item_id INTEGER NOT NULL, -- Assuming integer IDs for documents/chunks
                added_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (collection_id, item_type, item_id) -- Composite primary key
                -- No direct FK to documents/chunks to allow flexibility, handled by application logic
            );
        """)
    # Exact match for HNSW index (using f-string as in source)
    mock_cursor.execute.assert_any_await(f"""
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx
            ON chunks
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = {config.PGVECTOR_HNSW_M}, ef_construction = {config.PGVECTOR_HNSW_EF_CONSTRUCTION});
        """)
    # Check other indexes with exact strings
    mock_cursor.execute.assert_any_await("CREATE INDEX IF NOT EXISTS relationships_source_idx ON relationships (source_node_id);")
    mock_cursor.execute.assert_any_await("CREATE INDEX IF NOT EXISTS relationships_target_idx ON relationships (target_node_id);")
    mock_cursor.execute.assert_any_await("CREATE INDEX IF NOT EXISTS relationships_type_idx ON relationships (relation_type);")
    mock_cursor.execute.assert_any_await("CREATE INDEX IF NOT EXISTS collection_items_collection_idx ON collection_items (collection_id);")

    # Commit is usually handled by the connection context manager, not explicitly called in initialize_schema
    # mock_conn.commit.assert_awaited_once() # Remove this assertion


@pytest.mark.asyncio
@patch('src.philograph.data_access.connection.get_db_connection') # Patch new location
async def test_initialize_schema_db_error(mock_get_conn):
    """Tests that initialize_schema propagates database errors."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    # mock_get_conn.return_value = mock_conn # If get_db_connection returns conn directly
    mock_get_conn.return_value.__aenter__.return_value = mock_conn # If context manager

    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

    # Simulate psycopg.Error on one of the execute calls
    db_error = psycopg.Error("Simulated DB error during schema init")
    mock_cursor.execute.side_effect = db_error

    # Expect psycopg.Error to be raised and propagated
    with pytest.raises(psycopg.Error) as excinfo:
        await db_connection.initialize_schema(mock_conn) # Use new module path

    # Assertions
    assert excinfo.value is db_error # Check if the original error is propagated
    mock_cursor.execute.assert_awaited_once() # Should fail on the first execute
    # Commit is usually handled by the connection context manager
    # mock_conn.commit.assert_not_called() # Remove this assertion