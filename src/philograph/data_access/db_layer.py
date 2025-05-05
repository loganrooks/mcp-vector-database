"""
Data Access Layer Facade

This module acts as a central point of access to the database functionalities,
re-exporting components from specialized submodules for connection management,
models, and queries.
"""

# Import and re-export models
from .models import (
    Document,
    Section,
    Chunk,
    SearchResult,
    Relationship
)

# Import and re-export connection management functions
from .connection import (
    get_db_pool,
    get_db_connection,
    close_db_pool,
    initialize_schema
)

# Import and re-export query functions
from .queries.documents import (
    add_document,
    get_document_by_id,
    check_document_exists,
    add_section,
    add_chunk,
    add_chunks_batch,
    get_chunk_by_id
)
from .queries.search import (
    vector_search_chunks
)
from .queries.relationships import (
    add_relationship,
    get_relationships,
    get_relationships_for_document,
    add_reference # Keep if still used directly, otherwise consider removing
)
from .queries.collections import (
    add_collection,
    add_item_to_collection,
    get_collection_items,
    remove_item_from_collection,
    delete_collection
)

# Define __all__ for explicit re-export control
__all__ = [
    # Models
    "Document",
    "Section",
    "Chunk",
    "SearchResult",
    "Relationship",
    # Connection Management
    "get_db_pool",
    "get_db_connection",
    "close_db_pool",
    "initialize_schema",
    # Document/Chunk Queries
    "add_document",
    "get_document_by_id",
    "check_document_exists",
    "add_section",
    "add_chunk",
    "add_chunks_batch",
    "get_chunk_by_id",
    # Search Queries
    "vector_search_chunks",
    # Relationship Queries
    "add_relationship",
    "get_relationships",
    "get_relationships_for_document",
    "add_reference",
    # Collection Queries
    "add_collection",
    "add_item_to_collection",
    "get_collection_items",
    "remove_item_from_collection",
    "delete_collection",
]