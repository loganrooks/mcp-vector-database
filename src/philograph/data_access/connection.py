import logging
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import psycopg
from psycopg_pool import AsyncConnectionPool

from .. import config

logger = logging.getLogger(__name__)

# Global variable to hold the connection pool
pool: AsyncConnectionPool | None = None

async def get_db_pool() -> AsyncConnectionPool:
    """Initializes and returns the async database connection pool."""
    global pool
    if pool is None:
        logger.info(f"Initializing database connection pool for {config.DB_HOST}:{config.DB_PORT} using URL: {config.ASYNC_DATABASE_URL}") # Log URL
        try:
            logger.info("Creating AsyncConnectionPool instance...")
            # Use min_size=1 to keep at least one connection open
            pool = AsyncConnectionPool(
                conninfo=config.ASYNC_DATABASE_URL,
                min_size=config.DB_POOL_MIN_SIZE,
                max_size=config.DB_POOL_MAX_SIZE,
                open=True, # Open the pool immediately
                # Add timeouts if needed, e.g., timeout=10
            )
            # Test connection during initialization
            logger.info("Testing database connection...")
            async with pool.connection() as conn:
                 async with conn.cursor() as cur:
                     await cur.execute("SELECT 1")
                     result = await cur.fetchone()
                     if result and result[0] == 1:
                         logger.info("Database connection test successful.")
                     else:
                         logger.error("Database connection test failed.")
                         # Optionally raise an error here if connection is critical at startup
            logger.info(f"Database pool initialized successfully. Size: {pool.min_size}-{pool.max_size}")
        except psycopg.OperationalError as e:
            logger.error(f"Failed to connect to database: {e}", exc_info=True)
            # Depending on requirements, you might want to raise the error
            # or handle it gracefully (e.g., allow app to start but log error)
            pool = None # Reset pool on operational error
            raise RuntimeError(f"Failed to initialize database connection pool: {e}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during pool initialization: {e}", exc_info=True)
            pool = None # Reset pool on other exceptions
            raise RuntimeError(f"Unexpected error initializing database pool: {e}") from e
        # Removed diagnostic sleep.
    return pool # Ensure this is indented correctly within the function

@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """Provides an async connection from the pool."""
    global pool
    if pool is None:
        raise RuntimeError("Database pool is not initialized. Call get_db_pool() first.")
    async with pool.connection() as conn:
        try:
            yield conn
        except psycopg.Error as e:
            logger.error(f"Database connection error: {e}", exc_info=True)
            # Optionally rollback transaction if applicable
            # await conn.rollback()
            raise # Re-raise the error for endpoint handlers

async def close_db_pool():
    """Closes the database connection pool."""
    global pool
    if pool:
        logger.info("Closing database connection pool...")
        await pool.close()
        pool = None
        logger.info("Database connection pool closed.")

async def initialize_schema(conn: psycopg.AsyncConnection):
    """Creates necessary tables and extensions if they don't exist."""
    async with conn.cursor() as cur:
        logger.info("Initializing database schema...")

        # Enable pgvector extension
        logger.info("Enabling pgvector extension...")
        await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Create documents table
        logger.info("Creating documents table...")
        await cur.execute("""
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

        # Create sections table
        logger.info("Creating sections table...")
        await cur.execute("""
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

        # Create chunks table
        logger.info("Creating chunks table...")
        await cur.execute(f"""
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
        # Create index on embedding for faster similarity search (using HNSW)
        # Adjust parameters (m, ef_construction) based on dataset size and performance needs
        logger.info("Creating HNSW index on chunk embeddings...")
        await cur.execute(f"""
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx
            ON chunks
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = {config.PGVECTOR_HNSW_M}, ef_construction = {config.PGVECTOR_HNSW_EF_CONSTRUCTION});
        """)
        # Consider adding other indexes, e.g., on section_id if frequently queried

        # Create relationships table
        logger.info("Creating relationships table...")
        await cur.execute("""
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
        # Add indexes for faster querying
        await cur.execute("CREATE INDEX IF NOT EXISTS relationships_source_idx ON relationships (source_node_id);")
        await cur.execute("CREATE INDEX IF NOT EXISTS relationships_target_idx ON relationships (target_node_id);")
        await cur.execute("CREATE INDEX IF NOT EXISTS relationships_type_idx ON relationships (relation_type);")


        # Create collections table
        logger.info("Creating collections table...")
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        # Create collection_items table (junction table)
        logger.info("Creating collection_items table...")
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS collection_items (
                collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
                item_type VARCHAR(50) NOT NULL CHECK (item_type IN ('document', 'chunk')), -- 'section' could be added
                item_id INTEGER NOT NULL, -- Assuming integer IDs for documents/chunks
                added_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (collection_id, item_type, item_id) -- Composite primary key
                -- No direct FK to documents/chunks to allow flexibility, handled by application logic
            );
        """)
        # Add index for faster retrieval of items in a collection
        await cur.execute("CREATE INDEX IF NOT EXISTS collection_items_collection_idx ON collection_items (collection_id);")

        logger.info("Database schema initialization complete.")