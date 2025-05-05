import logging
import psycopg
from typing import List, Optional, Dict, Any

from ..models import SearchResult
from ...utils.db_utils import format_vector_for_pgvector

logger = logging.getLogger(__name__)

async def vector_search_chunks(conn: psycopg.AsyncConnection, query_embedding: List[float], top_k: int, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
    """Performs vector similarity search on chunks with optional metadata filtering."""
    if not query_embedding:
        # Raise ValueError as expected by tests
        # logger.warning("vector_search_chunks called with empty query embedding.")
        # return []
        raise ValueError("Query embedding cannot be empty.")

    logger.debug(f"Performing vector search with top_k={top_k}, filters={filters}")
    formatted_vector = format_vector_for_pgvector(query_embedding)

    # Base query
    base_sql = """
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
    params: List[Any] = [formatted_vector]
    where_clauses: List[str] = []

    # Apply filters
    if filters:
        logger.debug(f"Applying filters: {filters}")
        # Use %s placeholders consistently
        if 'author' in filters:
            where_clauses.append(f"d.author ILIKE %s")
            params.append(f"%{filters['author']}%")
        if 'year' in filters:
            where_clauses.append(f"d.year = %s")
            params.append(filters['year'])
        if 'doc_id' in filters:
            where_clauses.append(f"d.id = %s")
            params.append(filters['doc_id'])
        # Add more filters as needed

    # Construct final query
    if where_clauses:
        sql = f"{base_sql} WHERE {' AND '.join(where_clauses)} ORDER BY distance LIMIT %s"
        params.append(top_k)
    else:
        sql = f"{base_sql} ORDER BY distance LIMIT %s"
        params.append(top_k)

    logger.debug(f"Executing search query: {sql} with params count: {len(params)}")

    results = []
    async with conn.cursor() as cur:
        try:
            await cur.execute(sql, params)
            rows = await cur.fetchall()
            logger.info(f"Vector search returned {len(rows)} results.")
            for row in rows:
                results.append(SearchResult(
                    chunk_id=row[0],
                    section_id=row[1],
                    doc_id=row[2],
                    text_content=row[3],
                    distance=row[4],
                    doc_title=row[5],
                    doc_author=row[6],
                    doc_year=row[7],
                    doc_source_path=row[8],
                    section_title=row[9],
                    chunk_sequence=row[10]
                ))
        except psycopg.Error as e:
            logger.error(f"Database error during vector search: {e}", exc_info=True)
            # Re-raise or handle as appropriate for the calling context
            raise RuntimeError(f"Database error during vector search: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during vector search: {e}", exc_info=True)
            raise RuntimeError(f"Unexpected error during vector search: {e}") from e

    return results