import logging
import psycopg
from typing import List, Optional, Dict, Any

from ..models import Relationship
from ...utils.db_utils import json_serialize

logger = logging.getLogger(__name__)

# --- Relationship Queries ---

async def add_relationship(conn: psycopg.AsyncConnection, source_node_id: str, target_node_id: str, relation_type: str, metadata: Optional[Dict[str, Any]] = None) -> int:
    """Adds a relationship between two nodes."""
    logger.debug(f"Adding relationship: {source_node_id} -> {target_node_id} ({relation_type})")
    sql = """
        INSERT INTO relationships (source_node_id, target_node_id, relation_type, metadata)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (source_node_id, target_node_id, relation_type, json_serialize(metadata)))
        result = await cur.fetchone()
        if result:
            logger.info(f"Relationship added with ID: {result[0]}")
            return result[0]
        else:
            logger.error("Failed to retrieve ID after inserting relationship.")
            raise RuntimeError("Failed to add relationship to database.")

async def get_relationships(conn: psycopg.AsyncConnection, node_id: str, direction: str = 'outgoing', relation_type: Optional[str] = None) -> List[Relationship]:
    """Retrieves relationships connected to a node."""
    logger.debug(f"Getting relationships for node {node_id}, direction: {direction}, type: {relation_type}")
    results = []
    params: List[Any] = [node_id]
    sql_base = "SELECT id, source_node_id, target_node_id, relation_type, metadata FROM relationships WHERE "
    sql_clauses = []

    if direction == 'outgoing' or direction == 'both':
        sql_clauses.append("source_node_id = %s")
    if direction == 'incoming' or direction == 'both':
        # Need careful parameter handling if 'both'
        if direction == 'both':
            sql_clauses.append("target_node_id = %s")
            params.append(node_id) # Add node_id again for the second placeholder
        else: # direction == 'incoming'
            sql_clauses.append("target_node_id = %s")

    if not sql_clauses:
        raise ValueError("Invalid direction specified. Must be 'incoming', 'outgoing', or 'both'.")

    sql_direction_clause = f"({' OR '.join(sql_clauses)})" # Re-add outer parentheses

    sql_type_clause = ""
    if relation_type:
        sql_type_clause = f" AND relation_type = %s"
        params.append(relation_type)

    sql = f"{sql_base}{sql_direction_clause}{sql_type_clause} ORDER BY created_at DESC;" # Example ordering - Removed space after sql_base

    logger.debug(f"Executing relationship query: {sql} with params: {params}")
    async with conn.cursor() as cur:
        try:
            await cur.execute(sql, tuple(params)) # Pass params as a tuple
            rows = await cur.fetchall()
            logger.info(f"Found {len(rows)} relationships for node {node_id}.")
            for row in rows:
                # Deserialize metadata if needed
                metadata = row[4] # json.loads(row[4]) if row[4] else None
                results.append(Relationship(
                    id=row[0],
                    source_node_id=row[1],
                    target_node_id=row[2],
                    relation_type=row[3],
                    metadata=metadata
                ))
        except psycopg.Error as e:
            logger.error(f"Database error getting relationships for node {node_id}: {e}", exc_info=True)
            raise RuntimeError(f"Database error getting relationships: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting relationships for node {node_id}: {e}", exc_info=True)
            raise RuntimeError(f"Unexpected error getting relationships: {e}") from e
    return results

async def get_relationships_for_document(conn: psycopg.AsyncConnection, doc_id: int) -> List[Dict[str, Any]]:
    """Retrieves all relationships where the source node is a chunk within the given document."""
    logger.debug(f"Getting relationships originating from document ID: {doc_id}")
    sql = """
        SELECT r.id, r.source_node_id, r.target_node_id, r.relation_type, r.metadata
        FROM relationships r
        JOIN chunks c ON r.source_node_id = 'chunk:' || c.id::text
        JOIN sections s ON c.section_id = s.id
        WHERE s.doc_id = %s
        ORDER BY r.created_at DESC;
    """
    results = []
    async with conn.cursor() as cur:
        await cur.execute(sql, (doc_id,))
        rows = await cur.fetchall()
        logger.info(f"Found {len(rows)} relationships originating from document {doc_id}.")
        for row in rows:
            results.append({
                "id": row[0],
                "source_node_id": row[1],
                "target_node_id": row[2],
                "relation_type": row[3],
                "metadata": row[4] # Already JSONB from DB
            })
    return results

# --- Reference Query (Specific type of relationship) ---

async def add_reference(conn: psycopg.AsyncConnection, source_chunk_id: int, cited_doc_details: Dict[str, Any]) -> int:
    """Adds a reference linked to a source chunk."""
    # This might be better handled by the generic add_relationship function
    # Assuming 'reference' is a specific relation_type and target_node_id needs construction
    logger.debug(f"Adding reference from chunk {source_chunk_id} to {cited_doc_details}")
    source_node = f"chunk:{source_chunk_id}"
    # Construct a target node ID - this needs a defined format. Example:
    target_node = f"citation:{cited_doc_details.get('doi', cited_doc_details.get('title', 'unknown'))}" # Example format
    relation_type = "cites"
    metadata = cited_doc_details # Store the details in metadata

    sql = """
        INSERT INTO relationships (source_node_id, target_node_id, relation_type, metadata)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (source_node_id, target_node_id, relation_type) DO NOTHING -- Avoid duplicates
        RETURNING id;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (source_node, target_node, relation_type, json_serialize(metadata)))
        result = await cur.fetchone()
        if result:
            logger.info(f"Reference added/found with ID: {result[0]}")
            return result[0]
        else:
            # Could mean conflict occurred and it already existed, or insert failed
            logger.warning(f"Reference from {source_node} to {target_node} might already exist or failed to insert.")
            # Optionally query for existing ID if needed
            return -1 # Indicate potential existing or failed insert