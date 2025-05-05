import logging
import psycopg
from typing import List, Optional, Dict, Any, Tuple

from ..models import Document
from ...utils.db_utils import json_serialize, format_vector_for_pgvector

logger = logging.getLogger(__name__)

# --- Document Queries ---

async def add_document(conn: psycopg.AsyncConnection, title: Optional[str], author: Optional[str], year: Optional[int], source_path: str, metadata: Optional[Dict[str, Any]]) -> int:
    """Adds a new document record to the database."""
    logger.debug(f"Adding document: {source_path}")
    sql = """
        INSERT INTO documents (title, author, year, source_path, metadata)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (title, author, year, source_path, json_serialize(metadata)))
        result = await cur.fetchone()
        if result:
            logger.info(f"Document added with ID: {result[0]} for source: {source_path}")
            return result[0]
        else:
            # This case should ideally not happen if INSERT is successful
            logger.error(f"Failed to retrieve ID after inserting document: {source_path}")
            raise RuntimeError("Failed to add document to database.")

async def get_document_by_id(conn: psycopg.AsyncConnection, doc_id: int) -> Optional[Document]:
    """Retrieves a document by its ID."""
    logger.debug(f"Getting document by ID: {doc_id}")
    sql = "SELECT id, title, author, year, source_path, metadata FROM documents WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (doc_id,))
        result = await cur.fetchone()
        if result:
            # Map tuple to Pydantic model
            return Document(id=result[0], title=result[1], author=result[2], year=result[3], source_path=result[4], metadata=result[5])
        else:
            logger.warning(f"Document with ID {doc_id} not found.")
            return None

async def check_document_exists(conn: psycopg.AsyncConnection, source_path: str) -> bool:
    """Checks if a document with the given source_path already exists."""
    logger.debug(f"Checking if document exists: {source_path}")
    sql = "SELECT EXISTS (SELECT 1 FROM documents WHERE source_path = %s);"
    async with conn.cursor() as cur:
        await cur.execute(sql, (source_path,))
        result = await cur.fetchone()
        exists = result[0] if result else False
        logger.debug(f"Document exists check for {source_path}: {exists}")
        return exists

# --- Section Queries ---

async def add_section(conn: psycopg.AsyncConnection, doc_id: int, title: Optional[str], level: int, sequence: int) -> int:
    """Adds a new section record linked to a document."""
    logger.debug(f"Adding section for doc_id {doc_id}, sequence {sequence}")
    sql = """
        INSERT INTO sections (doc_id, title, level, sequence)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (doc_id, title, level, sequence))
        result = await cur.fetchone()
        if result:
            logger.info(f"Section added with ID: {result[0]} for doc_id {doc_id}")
            return result[0]
        else:
            logger.error(f"Failed to retrieve ID after inserting section for doc_id {doc_id}")
            raise RuntimeError("Failed to add section to database.")

# --- Chunk Queries ---

async def add_chunk(conn: psycopg.AsyncConnection, section_id: int, text_content: str, sequence: int, embedding_vector: List[float]) -> int:
    """Adds a single chunk with its embedding."""
    logger.debug(f"Adding chunk for section_id {section_id}, sequence {sequence}")
    sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    formatted_vector = format_vector_for_pgvector(embedding_vector)
    async with conn.cursor() as cur:
        await cur.execute(sql, (section_id, text_content, sequence, formatted_vector))
        result = await cur.fetchone()
        if result:
            logger.info(f"Chunk added with ID: {result[0]} for section_id {section_id}")
            return result[0]
        else:
            logger.error(f"Failed to retrieve ID after inserting chunk for section_id {section_id}")
            raise RuntimeError("Failed to add chunk to database.")

async def add_chunks_batch(conn: psycopg.AsyncConnection, chunks_data: List[Tuple[int, str, int, List[float]]]):
    """Adds multiple chunks in a batch."""
    if not chunks_data:
        logger.warning("add_chunks_batch called with empty list.")
        return

    logger.info(f"Adding batch of {len(chunks_data)} chunks.")
    sql = """
        INSERT INTO chunks (section_id, text_content, sequence, embedding)
        VALUES (%s, %s, %s, %s);
    """
    # Format data for execute_values or executemany
    formatted_data = [
        (section_id, text_content, sequence, format_vector_for_pgvector(embedding))
        for section_id, text_content, sequence, embedding in chunks_data
    ]
    async with conn.cursor() as cur:
        # Use executemany for batch insertion
        await cur.executemany(sql, formatted_data)
        logger.info(f"Successfully added batch of {cur.rowcount} chunks.") # Log how many rows were affected

async def get_chunk_by_id(conn: psycopg.AsyncConnection, chunk_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves chunk details by ID. Returns a dictionary."""
    logger.debug(f"Getting chunk by ID: {chunk_id}")
    sql = "SELECT id, section_id, text_content, sequence FROM chunks WHERE id = %s;"
    async with conn.cursor() as cur:
        await cur.execute(sql, (chunk_id,))
        result = await cur.fetchone()
        if result:
            # Return as dict
            return {
                "id": result[0],
                "section_id": result[1],
                "text_content": result[2],
                "sequence": result[3],
            }
        else:
            logger.warning(f"Chunk with ID {chunk_id} not found.")
            return None