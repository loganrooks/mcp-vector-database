import json
import asyncio # Add asyncio import
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel, Field, validator

from .. import config # Use relative import within the package

logger = logging.getLogger(__name__)

# --- Pydantic Models for Data Structures (Optional but helpful) ---
class Document(BaseModel):
    id: int
    title: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    source_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Section(BaseModel):
    id: int
    doc_id: int
    title: Optional[str] = None
    level: int = 0
    sequence: int

class Chunk(BaseModel):
    id: int
    section_id: int
    text_content: str
    sequence: int
    # embedding: List[float] # Embedding is handled separately for search

class SearchResult(BaseModel):
    chunk_id: int
    text_content: str
    sequence: int
    section_id: int
    section_title: Optional[str] = None
    doc_id: int
    doc_title: Optional[str] = None
    doc_author: Optional[str] = None
    doc_year: Optional[int] = None
    source_path: str
    distance: float

class Relationship(BaseModel):
    id: int
    source_node_id: str # Assuming node IDs can be strings (e.g., 'doc:123', 'chunk:456')
    target_node_id: str
    relation_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

# --- Connection Management ---

# Initialize the pool globally but lazily
db_pool: Optional[AsyncConnectionPool] = None

async def get_db_pool() -> AsyncConnectionPool:
    """Initializes and returns the async connection pool."""
    global db_pool
    if db_pool is None:
        logger.info(f"Initializing database connection pool for {config.DB_HOST}:{config.DB_PORT} using URL: {config.ASYNC_DATABASE_URL}") # Log URL
        try:
            logger.info("Creating AsyncConnectionPool instance...")
            # Use min_size=1 to keep at least one connection open
            db_pool = AsyncConnectionPool(
                conninfo=config.ASYNC_DATABASE_URL,
                min_size=1,
                max_size=10, # Adjust pool size as needed
                # Set explicit timeouts (in seconds)
                timeout=30 # Timeout for acquiring a connection from the pool
                # connect_timeout=30 # REMOVED: Invalid argument for AsyncConnectionPool
                # open=True # DEPRECATED: Open pool immediately - REMOVED
                # row_factory=dict_row # Removed: Apply row_factory at cursor level if needed
            )
            logger.info("AsyncConnectionPool instance created. Opening pool...")
            # Explicitly open the pool asynchronously
            await db_pool.open() # This implicitly tries to connect
            logger.info("Database connection pool opened.")
            # Test connection
            logger.info("Attempting test query via pool...") # Add log before test
            async with db_pool.connection() as conn:
                 async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    result = await cur.fetchone()
                    logger.info(f"Database test connection successful. Result: {result}")
        except psycopg.Error as e:
            logger.exception("psycopg.Error during DB pool initialization/test.", exc_info=e)
            db_pool = None # Ensure pool is None if initialization fails
            raise ConnectionError("Database connection pool initialization failed (psycopg.Error)") from e
        except Exception as e: # Catch broader exceptions during init
             logger.exception("Unexpected error during DB pool initialization/test.", exc_info=e)
             db_pool = None
             raise ConnectionError("Unexpected error during DB pool initialization") from e

    return db_pool

@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """Provides an async connection from the pool."""
    pool = await get_db_pool()
    async with pool.connection() as conn:
        try:
            yield conn
        except psycopg.Error as e:
            logger.exception("Database operation failed", exc_info=e)
            # Decide whether to rollback based on error type or context
            # await conn.rollback() # Example rollback
            raise # Re-raise the exception

async def close_db_pool():
    """Closes the database connection pool."""
    global db_pool
    if db_pool:
        logger.info("Closing database connection pool...")
        await db_pool.close()
        db_pool = None
        logger.info("Database connection pool closed.")

# --- Utility Functions ---

def format_vector_for_pgvector(vector: List[float]) -> str:
    """Formats a list of floats into the string representation required by pgvector."""
    # TDD: Test formatting of list/numpy array to string '[1.0, 2.0,...]'
    if not isinstance(vector, list) or not all(isinstance(x, (int, float)) for x in vector):
        raise TypeError("Input vector must be a list of numbers.")
    # Basic validation, more robust checks might be needed
    # assert len(vector) == config.TARGET_EMBEDDING_DIMENSION, f"Vector dimension mismatch: expected {config.TARGET_EMBEDDING_DIMENSION}, got {len(vector)}"
    return '[' + ','.join(map(str, vector)) + ']'

def json_serialize(data: Optional[Dict[str, Any]]) -> Optional[str]:
    """Serializes a dictionary to a JSON string."""
    # TDD: Test serialization of dict to JSON string
    # TDD: Test handling of None input
    if data is None:
        return None
    return json.dumps(data)

# --- Document Operations ---

async def add_document(conn: psycopg.AsyncConnection, title: Optional[str], author: Optional[str], year: Optional[int], source_path: str, metadata: Optional[Dict[str, Any]]) -> int:
    """Adds a new document record to the database."""
    # TDD: Test adding a new document returns a valid ID
    # TDD: Test adding a document with existing source_path (handle appropriately - update or error?)
    # TDD: Test handling of null/empty values for optional fields
    sql = """
        INSERT INTO documents (title, author, year, source_path, metadata_jsonb)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """
    params = (title, author, year, source_path, json_serialize(metadata))
    async with conn.cursor() as cur:
        await cur.execute(sql, params)
        result = await cur.fetchone()
        if result:
            await conn.commit()
            return result['id']
        else:
            # This case should ideally not happen with RETURNING id on success
            await conn.rollback()
            raise RuntimeError("Failed to retrieve ID after document insert.")

async def get_document_by_id(conn: psycopg.AsyncConnection, doc_id: int) -> Optional[Document]:
    """Retrieves a document by its ID."""
    # TDD: Test retrieving an existing document
    # TDD: Test retrieving a non-existent document returns None
    sql = "SELECT id, title, author, year, source_path, metadata_jsonb FROM documents WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (doc_id,))
        result = await cur.fetchone()
        if result:
            # Explicitly map metadata_jsonb to metadata field for Pydantic model
            doc_data = dict(result) # Copy the dict_row result
            doc_data['metadata'] = doc_data.pop('metadata_jsonb', {}) or {} # Pop 'metadata_jsonb', provide default {} if None/missing
            return Document(**doc_data)
        else:
            return None

async def check_document_exists(conn: psycopg.AsyncConnection, source_path: str) -> bool:
    """Checks if a document with the given source_path already exists."""
    # TDD: Test returns True for existing document by source_path
    # TDD: Test returns False for non-existent document by source_path
    sql = "SELECT EXISTS(SELECT 1 FROM documents WHERE source_path = %s);"
    async with conn.cursor() as cur:
        await cur.execute(sql, (source_path,))
        result = await cur.fetchone()
        return result['exists'] if result else False

# --- Section Operations ---

async def add_section(conn: psycopg.AsyncConnection, doc_id: int, title: Optional[str], level: int, sequence: int) -> int:
    """Adds a new section record linked to a document."""
    # TDD: Test adding a section returns a valid ID
    # TDD: Test adding section linked to non-existent doc_id raises error (handled by FK constraint)
    sql = """
        INSERT INTO sections (doc_id, title, level, sequence)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    params = (doc_id, title, level, sequence)
    async with conn.cursor() as cur:
        await cur.execute(sql, params)
        result = await cur.fetchone()
        if result:
            await conn.commit()
            return result['id']
        else:
            await conn.rollback()
            raise RuntimeError("Failed to retrieve ID after section insert.")

# --- Chunk Operations ---

async def add_chunk(conn: psycopg.AsyncConnection, section_id: int, text_content: str, sequence: int, embedding_vector: List[float]) -> int:
    """Adds a single chunk with its embedding."""
    # TDD: Test adding a chunk returns a valid ID
    # TDD: Test adding chunk with embedding of incorrect dimension raises error (add assert)
    # TDD: Test adding chunk linked to non-existent section_id raises error (handled by FK constraint)
    if len(embedding_vector) != config.TARGET_EMBEDDING_DIMENSION:
         raise ValueError(f"Embedding vector dimension mismatch: expected {config.TARGET_EMBEDDING_DIMENSION}, got {len(embedding_vector)}")

    sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s::vector(%s))
        RETURNING id;
    """
    formatted_embedding = format_vector_for_pgvector(embedding_vector)
    params = (section_id, text_content, sequence, formatted_embedding, config.TARGET_EMBEDDING_DIMENSION)
    async with conn.cursor() as cur:
        await cur.execute(sql, params)
        result = await cur.fetchone()
        if result:
            await conn.commit()
            return result['id']
        else:
            await conn.rollback()
            raise RuntimeError("Failed to retrieve ID after chunk insert.")

async def add_chunks_batch(conn: psycopg.AsyncConnection, chunks_data: List[Tuple[int, str, int, List[float]]]):
    """Adds multiple chunks in a batch."""
    # chunks_data: list of tuples (section_id, text_content, sequence, embedding_vector)
    # TDD: Test adding multiple chunks successfully
    # TDD: Test rollback on error during batch insert
    # TDD: Test performance compared to single inserts
    if not chunks_data:
        return

    sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s::vector(%s));
    """
    formatted_data = []
    for section_id, text_content, sequence, embedding_vector in chunks_data:
        if len(embedding_vector) != config.TARGET_EMBEDDING_DIMENSION:
            raise ValueError(f"Embedding vector dimension mismatch in batch: expected {config.TARGET_EMBEDDING_DIMENSION}, got {len(embedding_vector)}")
        formatted_embedding = format_vector_for_pgvector(embedding_vector)
        formatted_data.append((section_id, text_content, sequence, formatted_embedding, config.TARGET_EMBEDDING_DIMENSION))

    async with conn.cursor() as cur:
        # Use executemany for batch insertion
        await cur.executemany(sql, formatted_data)
        await conn.commit()
    logger.info(f"Successfully added {len(formatted_data)} chunks in batch.")
async def get_chunk_by_id(conn: psycopg.AsyncConnection, chunk_id: int) -> Optional[Dict[str, Any]]:
    """Placeholder: Retrieves a chunk by its ID."""
    # TDD: Implement actual query
    # TDD: Test success case
    # TDD: Test not found case
    # TDD: Test DB error case
    pass # Minimal implementation for patching


# --- Reference Operations ---

async def add_reference(conn: psycopg.AsyncConnection, source_chunk_id: int, cited_doc_details: Dict[str, Any]) -> int:
    """Adds a reference linked to a source chunk."""
    # TDD: Test adding a reference returns a valid ID
    # TDD: Test adding reference linked to non-existent chunk_id raises error (handled by FK constraint)
    sql = """
        INSERT INTO "references" (source_chunk_id, cited_doc_details_jsonb)
        VALUES (%s, %s)
        RETURNING id;
    """
    params = (source_chunk_id, json_serialize(cited_doc_details))
    async with conn.cursor() as cur:
        await cur.execute(sql, params)
        result = await cur.fetchone()
        if result:
            await conn.commit()
            return result['id']
        else:
            await conn.rollback()
            raise RuntimeError("Failed to retrieve ID after reference insert.")

# --- Search Operations ---

async def vector_search_chunks(conn: psycopg.AsyncConnection, query_embedding: List[float], top_k: int, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
    """Performs vector search on chunks with optional metadata filtering."""
    # TDD: Test basic vector search returns correct number of results (top_k)
    # TDD: Test vector search with metadata filters (e.g., author, year)
    # TDD: Test search with empty query_embedding raises error
    # TDD: Test search with embedding of incorrect dimension raises error
    # TDD: Test different distance metrics (L2, cosine) if needed
    if not query_embedding:
        raise ValueError("Query embedding cannot be empty.")
    if len(query_embedding) != config.TARGET_EMBEDDING_DIMENSION:
         raise ValueError(f"Query embedding dimension mismatch: expected {config.TARGET_EMBEDDING_DIMENSION}, got {len(query_embedding)}")

    # Use cosine distance (<->) as it's often good for semantic similarity
    # Normalize embeddings in the DB and query embedding for cosine similarity
    # Or use inner product (<#>) if embeddings are normalized (cosine sim = 1 - inner product)
    # Using L2 distance (<=>) here as a default, adjust if needed based on embedding model characteristics
    distance_operator = "<=>"

    # Format the dimension directly into the SQL string for the vector type cast
    # PostgreSQL requires the dimension to be a literal constant in the type cast.
    vector_cast = f"::vector({config.TARGET_EMBEDDING_DIMENSION})"
    base_sql = f"""
        SELECT c.id as chunk_id, c.text_content, c.sequence, s.id as section_id, s.title as section_title,
               d.id as doc_id, d.title as doc_title, d.author as doc_author, d.year as doc_year, d.source_path,
               c.embedding {distance_operator} %s{vector_cast} AS distance
        FROM chunks c
        JOIN sections s ON c.section_id = s.id
        JOIN documents d ON s.doc_id = d.id
    """
    where_clauses = []
    # Remove dimension from params, only pass the formatted embedding vector
    params: List[Any] = [format_vector_for_pgvector(query_embedding)]

    if filters:
        # TDD: Test filter construction for various valid filter types
        # TDD: Test filter construction handles invalid/malformed filters gracefully
        param_index = len(params) + 1 # Start parameter index after embedding and dimension
        if 'author' in filters:
            where_clauses.append(f"d.author ILIKE %s") # Case-insensitive search
            params.append(f"%{filters['author']}%")
            param_index += 1
        if 'year' in filters:
            # Allow range or exact year? Assuming exact for now.
            try:
                year_val = int(filters['year'])
                where_clauses.append(f"d.year = %s")
                params.append(year_val)
                param_index += 1
            except ValueError:
                logger.warning(f"Invalid year filter value: {filters['year']}. Ignoring.")
        if 'doc_id' in filters:
            try:
                doc_id_val = int(filters['doc_id'])
                where_clauses.append(f"d.id = %s")
                params.append(doc_id_val)
                param_index += 1
            except ValueError:
                 logger.warning(f"Invalid doc_id filter value: {filters['doc_id']}. Ignoring.")
        # Add more filters as needed (e.g., tags in metadata_jsonb using @> operator)

    sql = base_sql
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    sql += f" ORDER BY distance ASC LIMIT %s;"
    params.append(top_k)

    logger.debug(f"Executing search SQL: {sql} with params: {params[:-1]}") # Log params except top_k

    async with conn.cursor() as cur:
        await cur.execute(sql, tuple(params))
        results = await cur.fetchall()

    # TDD: Test mapping of results to structured objects
    return [SearchResult(**row) for row in results]

# --- Relationship Operations (Basic) ---

async def add_relationship(conn: psycopg.AsyncConnection, source_node_id: str, target_node_id: str, relation_type: str, metadata: Optional[Dict[str, Any]] = None) -> int:
    """Adds a relationship between two nodes."""
    # TDD: Test adding a 'cites' relationship
    # TDD: Test adding relationship with non-existent nodes raises error (needs node validation or relies on FKs if nodes are table rows)
    # Assuming node_ids are strings like 'doc:123', 'chunk:456' - adjust schema if they are FKs
    sql = """
        INSERT INTO relationships (source_node_id, target_node_id, relation_type, metadata_jsonb)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    params = (source_node_id, target_node_id, relation_type, json_serialize(metadata))
    async with conn.cursor() as cur:
        await cur.execute(sql, params)
        result = await cur.fetchone()
        if result:
            await conn.commit()
            return result['id']
        else:
            await conn.rollback()
            raise RuntimeError("Failed to retrieve ID after relationship insert.")

async def get_relationships(conn: psycopg.AsyncConnection, node_id: str, direction: str = 'outgoing', relation_type: Optional[str] = None) -> List[Relationship]:
    """Retrieves relationships connected to a node."""
    # direction: 'outgoing', 'incoming', 'both'
    # TDD: Test getting outgoing 'cites' relationships
    # TDD: Test getting incoming 'cites' relationships
    # TDD: Test getting relationships of a specific type
    # TDD: Test getting relationships for a non-existent node_id returns empty list
    base_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata_jsonb FROM relationships"
    where_clauses = []
    params = []

    if direction == 'outgoing':
        where_clauses.append("source_node_id = %s")
        params.append(node_id)
    elif direction == 'incoming':
        where_clauses.append("target_node_id = %s")
        params.append(node_id)
    elif direction == 'both':
        where_clauses.append("(source_node_id = %s OR target_node_id = %s)")
        params.extend([node_id, node_id])
    else:
        raise ValueError("Invalid direction specified. Use 'outgoing', 'incoming', or 'both'.")

    if relation_type is not None:
        where_clauses.append("relation_type = %s")
        params.append(relation_type)

    sql = base_sql
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    async with conn.cursor() as cur:
        await cur.execute(sql, tuple(params))
        results = await cur.fetchall()

    # Map metadata_jsonb to metadata field for Pydantic model
    processed_results = []
    for row in results:
        rel_data = dict(row) # Copy the dict_row result
        rel_data['metadata'] = rel_data.pop('metadata_jsonb', {}) or {} # Pop 'metadata_jsonb', provide default {} if None/missing
        processed_results.append(Relationship(**rel_data))
    return processed_results

async def get_relationships_for_document(conn: psycopg.AsyncConnection, doc_id: int) -> List[Dict[str, Any]]:
    """Retrieves relationships originating from chunks within a specific document."""
    # TDD: Test retrieving relationships for a document
    # TDD: Test retrieving relationships for a document with no relationships returns empty list
    # TDD: Test handling of different relationship types if needed
    sql = """
        SELECT r.id, r.source_node_id, r.target_node_id, r.relation_type, r.metadata_jsonb
        FROM relationships r
        JOIN chunks c ON r.source_node_id = 'chunk:' || c.id::text
        JOIN sections s ON c.section_id = s.id
        WHERE s.doc_id = %s;
    """
    params = (doc_id,)
    async with conn.cursor() as cur:
        await cur.execute(sql, params)
        results = await cur.fetchall()

    # Map metadata_jsonb to metadata field for Pydantic model
    processed_results = []
    for row in results:
        rel_data = dict(row) # Copy the dict_row result
        rel_data['metadata'] = rel_data.pop('metadata_jsonb', {}) or {} # Pop 'metadata_jsonb', provide default {} if None/missing
        processed_results.append(Relationship(**rel_data)) # Use the Relationship model defined earlier
    return processed_results
# --- Collection Operations ---

async def add_collection(conn: psycopg.AsyncConnection, name: str) -> int:
    """Adds a new collection."""
    # TDD: Test adding a new collection
    sql = "INSERT INTO collections (name) VALUES (%s) RETURNING id;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (name,))
        result = await cur.fetchone()
        if result:
            await conn.commit()
            return result[0]
        else:
            await conn.rollback()
            raise RuntimeError("Failed to retrieve ID after collection insert.")

async def add_item_to_collection(conn: psycopg.AsyncConnection, collection_id: int, item_type: str, item_id: int):
    """Adds an item (document, chunk) to a collection."""
    # item_type: 'document', 'chunk', etc.
    # TDD: Test adding a document to a collection
    # TDD: Test adding a chunk to a collection
    # TDD: Test adding item to non-existent collection raises error (handled by FK constraint)
    # TDD: Test adding item with invalid item_type raises error
    allowed_types = ['document', 'chunk'] # Define allowed types
    if item_type not in allowed_types:
        raise ValueError(f"Invalid item_type '{item_type}'. Allowed types: {allowed_types}")

    sql = "INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (%s, %s, %s);"
    params = (collection_id, item_type, item_id)
    async with conn.cursor() as cur:
        await cur.execute(sql, params)
        await conn.commit()

async def get_collection_items(conn: psycopg.AsyncConnection, collection_id: int) -> Optional[List[Dict[str, Any]]]:
    """Retrieves items belonging to a collection. Returns None if collection_id does not exist."""
    # TDD: Test retrieving items from a collection
    # TDD: Test retrieving items from non-existent collection returns None
    # TDD: Test retrieving items from an empty collection returns []

    # First, check if the collection exists
    check_sql = "SELECT EXISTS(SELECT 1 FROM collections WHERE id = %s);"
    async with conn.cursor() as cur:
        await cur.execute(check_sql, (collection_id,))
        exists_result = await cur.fetchone()
        collection_exists = exists_result[0] if exists_result else False

    if not collection_exists:
        logger.warning(f"Collection with ID {collection_id} not found.")
        return None # Return None if collection does not exist

    # If collection exists, retrieve items
    items_sql = "SELECT item_type, item_id FROM collection_items WHERE collection_id = %s;"
    params = (collection_id,)
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(items_sql, params)
        results = await cur.fetchall()
        return results # Returns list of dicts (can be empty if collection has no items)

async def remove_item_from_collection(conn: psycopg.AsyncConnection, collection_id: int, item_type: str, item_id: int) -> bool:
    """Removes an item from a collection. Returns True if removed, False if not found."""
    # TDD: Test removing an existing item returns True
    # TDD: Test removing a non-existent item returns False
    # TDD: Test removing item from non-existent collection returns False (or relies on FK)
    sql = "DELETE FROM collection_items WHERE collection_id = %s AND item_type = %s AND item_id = %s;"
    params = (collection_id, item_type, item_id)
    async with conn.cursor() as cur:
        await cur.execute(sql, params)
        await conn.commit()
        # Check if any row was actually deleted
        return cur.rowcount > 0

async def delete_collection(conn: psycopg.AsyncConnection, collection_id: int) -> bool:
    """Deletes a collection. Returns True if deleted, False if not found.
    Note: This currently only deletes the collection record itself.
    Associated items in collection_items might need separate handling or CASCADE DELETE in the schema.
    """
    # TDD: Test deleting an existing collection returns True
    # TDD: Test deleting a non-existent collection returns False
    sql = "DELETE FROM collections WHERE id = %s;"
    params = (collection_id,)
    async with conn.cursor() as cur:
        await cur.execute(sql, params)
        await conn.commit()
        # Check if any row was actually deleted
        return cur.rowcount > 0

# --- Schema Initialization (Example - Run separately or via migration tool) ---
async def initialize_schema(conn: psycopg.AsyncConnection):
    """Creates necessary tables and extensions if they don't exist."""
    async with conn.cursor() as cur:
        logger.info("Initializing database schema...")
        await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await cur.execute(f"""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title TEXT,
                author TEXT,
                year INTEGER,
                source_path TEXT UNIQUE NOT NULL,
                metadata_jsonb JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS sections (
                id SERIAL PRIMARY KEY,
                doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                title TEXT,
                level INTEGER DEFAULT 0,
                sequence INTEGER NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (doc_id, sequence) -- Ensure sequence is unique within a document
            );
        """)
        await cur.execute(f"""
            CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
                text_content TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                embedding vector({config.TARGET_EMBEDDING_DIMENSION}),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (section_id, sequence) -- Ensure sequence is unique within a section
            );
        """)
        # Create index after table creation
        # Adjust index parameters (lists, probes) based on performance testing
        await cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks
            USING hnsw (embedding vector_l2_ops);
        """) # Or vector_cosine_ops / vector_ip_ops
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS "references" (
                id SERIAL PRIMARY KEY,
                source_chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
                cited_doc_details_jsonb JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id SERIAL PRIMARY KEY,
                source_node_id TEXT NOT NULL, -- e.g., 'doc:1', 'chunk:5'
                target_node_id TEXT NOT NULL,
                relation_type VARCHAR(50) NOT NULL,
                metadata_jsonb JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
                -- Add UNIQUE constraint if needed: UNIQUE(source_node_id, target_node_id, relation_type)
            );
        """)
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS collection_items (
                collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
                item_type VARCHAR(50) NOT NULL, -- e.g., 'document', 'chunk'
                item_id INTEGER NOT NULL, -- Refers to ID in documents or chunks table based on item_type
                added_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (collection_id, item_type, item_id)
            );
        """)
        # Trigger for updated_at timestamp
        await cur.execute("""
            CREATE OR REPLACE FUNCTION trigger_set_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
              NEW.updated_at = NOW();
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        await cur.execute("""
            DROP TRIGGER IF EXISTS set_timestamp ON documents;
            CREATE TRIGGER set_timestamp
            BEFORE UPDATE ON documents
            FOR EACH ROW
            EXECUTE PROCEDURE trigger_set_timestamp();
        """)
        await conn.commit()
        logger.info("Database schema initialized successfully.")

# Example usage for schema init (run this separately, e.g., in a setup script)
# async def main():
#     pool = await get_db_pool()
#     async with pool.connection() as conn:
#         await initialize_schema(conn)
#     await close_db_pool()

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())