import logging
import psycopg
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# --- Collection Queries ---

async def add_collection(conn: psycopg.AsyncConnection, name: str) -> int:
    """Adds a new collection."""
    logger.debug(f"Adding collection: {name}")
    sql = """
        INSERT INTO collections (name)
        VALUES (%s)
        RETURNING id;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (name,))
        result = await cur.fetchone()
        if result:
            logger.info(f"Collection added with ID: {result[0]} for name: {name}")
            return result[0]
        else:
            logger.error(f"Failed to retrieve ID after inserting collection: {name}")
            raise RuntimeError("Failed to add collection to database.")

async def add_item_to_collection(conn: psycopg.AsyncConnection, collection_id: int, item_type: str, item_id: int):
    """Adds an item (document, chunk) to a collection."""
    logger.debug(f"Adding item {item_type}:{item_id} to collection {collection_id}")
    sql = """
        INSERT INTO collection_items (collection_id, item_type, item_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (collection_id, item_type, item_id) DO NOTHING; -- Avoid errors if item already exists
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (collection_id, item_type, item_id))
        if cur.rowcount > 0:
             logger.info(f"Item {item_type}:{item_id} added to collection {collection_id}.")
        else:
             logger.warning(f"Item {item_type}:{item_id} might already exist in collection {collection_id}.")


async def get_collection_items(conn: psycopg.AsyncConnection, collection_id: int) -> Optional[List[Tuple[str, int]]]:
    """Retrieves items (type, id) in a collection. Returns None if collection doesn't exist."""
    logger.debug(f"Getting items for collection ID: {collection_id}")
    # First check if collection exists
    check_sql = "SELECT EXISTS (SELECT 1 FROM collections WHERE id = %s);"
    items_sql = """
        SELECT item_type, item_id
        FROM collection_items
        WHERE collection_id = %s
        ORDER BY added_at; -- Or some other meaningful order
    """
    async with conn.cursor() as cur:
        await cur.execute(check_sql, (collection_id,))
        exists_result = await cur.fetchone()
        if not exists_result or not exists_result[0]:
            logger.warning(f"Collection with ID {collection_id} not found.")
            return None # Indicate collection not found

        # Collection exists, now get items
        await cur.execute(items_sql, (collection_id,))
        rows = await cur.fetchall()
        logger.info(f"Found {len(rows)} items in collection {collection_id}.")
        # Return list of tuples (item_type, item_id)
        return [(row[0], row[1]) for row in rows]


async def remove_item_from_collection(conn: psycopg.AsyncConnection, collection_id: int, item_type: str, item_id: int) -> bool:
    """Removes an item from a collection. Returns True if removed, False if not found."""
    logger.debug(f"Removing item {item_type}:{item_id} from collection {collection_id}")
    sql = """
        DELETE FROM collection_items
        WHERE collection_id = %s AND item_type = %s AND item_id = %s;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (collection_id, item_type, item_id))
        removed = cur.rowcount > 0
        if removed:
            logger.info(f"Item {item_type}:{item_id} removed from collection {collection_id}.")
        else:
            logger.warning(f"Item {item_type}:{item_id} not found in collection {collection_id} for removal.")
        return removed

async def delete_collection(conn: psycopg.AsyncConnection, collection_id: int) -> bool:
    """Deletes a collection. Returns True if deleted, False if not found.
    Assumes ON DELETE CASCADE is set for collection_items table."""
    logger.debug(f"Deleting collection ID: {collection_id}")
    sql = """
        DELETE FROM collections
        WHERE id = %s;
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, (collection_id,))
        deleted = cur.rowcount > 0
        if deleted:
            logger.info(f"Collection ID {collection_id} deleted.")
        else:
            logger.warning(f"Collection ID {collection_id} not found for deletion.")
        return deleted