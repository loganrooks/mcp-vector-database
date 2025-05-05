import logging
import psycopg
from uuid import UUID
from typing import List, Literal

from fastapi import APIRouter, HTTPException, status, Path as FastApiPath, Depends
from psycopg_pool import AsyncConnectionPool

from ..models import (
    CollectionCreateRequest, CollectionCreateResponse,
    CollectionItemAddRequest, CollectionItemAddResponse,
    CollectionDeleteResponse, CollectionItem, CollectionGetResponse,
    CollectionItemDeleteResponse # Added missing import
)
from ...data_access import db_layer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collections", tags=["Collections"])


@router.post("", response_model=CollectionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(request: CollectionCreateRequest):
    """Creates a new collection."""
    logger.info(f"Received request to create collection: {request.name}")
    try:
        async with db_layer.get_db_connection() as conn:
            # Check if name already exists? DB constraint should handle this ideally.
            collection_id = await db_layer.add_collection(conn, request.name)
            return CollectionCreateResponse(message="Collection created", collection_id=collection_id)
    except psycopg.errors.UniqueViolation: # Catch specific DB error for duplicate name
         logger.warning(f"Attempted to create collection with duplicate name: {request.name}")
         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Collection name '{request.name}' already exists.")
    except Exception as e:
        logger.exception(f"Error creating collection '{request.name}'", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating collection.")


@router.post("/{collection_id}/items", response_model=CollectionItemAddResponse, status_code=status.HTTP_200_OK)
async def add_collection_item(
    request: CollectionItemAddRequest,
    collection_id: UUID = FastApiPath(..., description="ID of the collection to add item to.") # Standardized type hint
):
    """Adds an item (document or chunk) to a specific collection."""
    logger.info(f"Adding {request.item_type} {request.item_id} to collection {collection_id}")
    try:
        async with db_layer.get_db_connection() as conn:
            # DB foreign key constraints should handle non-existent collection_id or item_id
            await db_layer.add_item_to_collection(conn, collection_id, request.item_type, request.item_id)
            return CollectionItemAddResponse(message=f"{request.item_type.capitalize()} added to collection.")
    except psycopg.errors.ForeignKeyViolation as fk_error:
        logger.warning(f"Foreign key violation adding item to collection {collection_id}: {fk_error}")
        # Determine if it was collection_id or item_id that failed
        # This might require querying if the collection exists first, or better error parsing
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection or item not found.")
    except psycopg.errors.UniqueViolation as uv_error:
        logger.warning(f"Unique constraint violation adding item to collection {collection_id}: {uv_error}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{request.item_type.capitalize()} ID {request.item_id} already exists in collection ID {collection_id}."
        )
    except psycopg.Error as db_err: # Catch generic DB errors
        logger.exception(f"Database error adding item to collection {collection_id}", exc_info=db_err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error adding item to collection."
        )


@router.delete(
    "/{collection_id}/items/{item_type}/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an item from a collection",
)
async def delete_collection_item(
    collection_id: UUID = FastApiPath(..., description="The ID of the collection"), # Standardized type hint
    item_type: Literal["document", "chunk"] = FastApiPath(..., description="The type of the item to remove ('document' or 'chunk')"),
    item_id: UUID = FastApiPath(..., description="The ID of the item to remove"), # Standardized type hint
    pool: AsyncConnectionPool = Depends(db_layer.get_db_pool), # Keep Depends if needed by db_layer
):
    """
    Remove a specific document or chunk from a collection.
    """
    logger.info(f"Removing {item_type} {item_id} from collection {collection_id}")
    async with db_layer.get_db_connection() as conn: # Removed pool argument if not needed
        try:
            # Assuming db_layer.remove_item_from_collection exists based on test mock
            removed = await db_layer.remove_item_from_collection(
                conn=conn, # Pass connection if required by db_layer function
                collection_id=collection_id,
                item_type=item_type,
                item_id=item_id
            )
            if not removed:
                # Assume False from db_layer means item/collection not found
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Item not found in collection or collection does not exist.", # More specific message
                )
            # No content to return on success (204)
            return None # FastAPI handles 204 response correctly when None is returned

        except psycopg.Error as e:
            logger.exception(f"Database error removing {item_type} {item_id} from collection {collection_id}", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error removing item from collection.",
            )
        except HTTPException: # Re-raise HTTP exceptions first
             raise
        except Exception as e:
            logger.exception(f"Unexpected error removing {item_type} {item_id} from collection {collection_id}", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred.",
            )


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT, # Correct status code
    summary="Delete a collection",
    # Removed response_model as 204 should have no body
)
async def delete_collection( # Renamed function for clarity
    collection_id: UUID = FastApiPath(..., description="The ID of the collection to delete."), # Standardized type hint
    pool: AsyncConnectionPool = Depends(db_layer.get_db_pool), # Add pool dependency if needed
):
    """
    Deletes a collection. Assumes DB cascade handles related items or they must be removed first.
    """
    logger.info(f"Deleting collection {collection_id}")
    async with db_layer.get_db_connection() as conn: # Use correct context manager
        try:
            deleted = await db_layer.delete_collection(conn=conn, collection_id=collection_id) # Pass conn
            if not deleted:
                # Assume False from db_layer means collection not found
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
            # Return None for 204 No Content response
            return None
        except HTTPException:
             raise # Re-raise HTTP exceptions
        except psycopg.Error as e: # Specific DB error handling
            logger.exception(f"Database error deleting collection {collection_id}", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error deleting collection.",
            )
        except Exception as e: # Generic error handling
            logger.exception(f"Unexpected error deleting collection {collection_id}", exc_info=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while deleting the collection.",
            )


@router.get("/{collection_id}", response_model=CollectionGetResponse)
async def get_collection(collection_id: int = FastApiPath(..., gt=0, description="ID of the collection to retrieve.")): # Changed back to int
    """Retrieves items within a specific collection."""
    logger.info(f"Retrieving items for collection {collection_id}")
    try:
        async with db_layer.get_db_connection() as conn:
            # Check if collection exists first? Or just return empty list if no items found.
            # Let's assume returning empty list is acceptable if collection is empty or non-existent.
            items_raw = await db_layer.get_collection_items(conn, collection_id)
            # Check if the collection exists. If not (assuming db_layer returns None), return 404.
            # An empty list means the collection exists but is empty, which is a valid 200 OK response.
            if items_raw is None:
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
            # Convert list of dicts from db_layer to list of Pydantic models
            # Map tuple elements explicitly to model fields
            items = [CollectionItem(item_type=item[0], item_id=item[1]) for item in items_raw]
            return CollectionGetResponse(collection_id=collection_id, items=items)
    except HTTPException:
         raise # Re-raise HTTP exceptions (like the 404)
    except Exception as e:
        logger.exception(f"Error retrieving collection {collection_id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving collection.")