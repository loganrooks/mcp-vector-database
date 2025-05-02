import philograph.acquisition.service as text_acquisition
import logging
import linecache
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Literal
from uuid import UUID
import uuid

from psycopg_pool import AsyncConnectionPool
import psycopg
import fastapi # ADDED for explicit status codes
from fastapi import FastAPI, HTTPException, Body, Path as FastApiPath, Query, status, Depends
from pydantic import BaseModel, Field

from .. import config
from ..data_access import db_layer
from ..ingestion import pipeline as ingestion_pipeline
from ..search import service as search_service
from ..acquisition import service as acquisition_service
from ..utils import http_client # For lifespan management

logger = logging.getLogger(__name__)

# --- Pydantic Models for API ---

class IngestRequest(BaseModel):
    path: str = Field(..., description="Path to the file or directory relative to the configured source directory.")

class IngestResponse(BaseModel):
    message: str
    document_id: Optional[int] = None
    status: str # e.g., "Success", "Skipped", "Error", "Directory Processed"
    details: Optional[List[Dict[str, Any]]] = None # For directory processing

class SearchFilter(BaseModel):
    author: Optional[str] = None
    year: Optional[int] = None
    doc_id: Optional[int] = None
    # Add more filter fields as needed

class SearchRequest(BaseModel):
    query: str = Field(..., description="The natural language search query.")
    filters: Optional[SearchFilter] = None
    limit: int = Field(default=config.SEARCH_TOP_K, gt=0, le=100, description="Maximum number of results.")
    offset: int = Field(default=0, ge=0, description="Number of results to skip for pagination.")

class SearchResultItemSourceDocument(BaseModel):
    doc_id: int
    title: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    source_path: str

class SearchResultItemLocation(BaseModel):
    section_id: int
    section_title: Optional[str] = None
    chunk_sequence_in_section: int

class SearchResultItem(BaseModel):
    chunk_id: int
    text: str
    distance: float
    source_document: SearchResultItemSourceDocument
    location: SearchResultItemLocation

class SearchResponse(BaseModel):
    results: List[SearchResultItem]

class DocumentResponse(db_layer.Document): # Reuse Pydantic model from db_layer
    pass

class CollectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)

class CollectionCreateResponse(BaseModel):
    message: str
    collection_id: int

class CollectionItemAddRequest(BaseModel):
    item_type: str = Field(..., pattern="^(document|chunk)$") # Validate allowed types
    item_id: int

class CollectionItemAddResponse(BaseModel):
    message: str

class CollectionDeleteResponse(BaseModel):
    message: str
class CollectionItem(BaseModel):
    item_type: str
    item_id: int

class CollectionGetResponse(BaseModel):
    collection_id: int
    items: List[CollectionItem]

# Models for the new /acquire initiation flow based on test_acquire_success
class AcquireInitiateRequest(BaseModel):
    query: str = Field(..., description="Search query for the text.")
    search_type: str = Field(default="book_meta", description="Type of search (e.g., 'book_meta', 'full_text').") # Assuming default based on test
    download: bool = Field(default=True, description="Whether to automatically download if a single exact match is found.")

class AcquireInitiateResponse(BaseModel):
    message: str
    acquisition_id: str

# Models for /acquire/confirm and /acquire/status remain

class AcquireConfirmRequest(BaseModel):
    # acquisition_id is now a path parameter
    selected_book_details: Dict[str, Any] # Full bookDetails object

class AcquireConfirmResponse(BaseModel):
    status: str # e.g., "complete", "error"
    message: str
    document_id: Optional[int] = None # PhiloGraph doc ID if ingestion successful
    status_url: Optional[str] = None # Optional: URL to check status later

class AcquisitionStatusResponse(BaseModel):
    status: str
    details: Optional[Dict[str, Any]] = None # Allow any type in details dict
    selected_book: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processed_path: Optional[str] = None
    philo_doc_id: Optional[int] = None


# Models for Document References
class ReferenceDetail(BaseModel):
    id: int # Added ID field based on mock data
    source_node_id: str # Changed from source_chunk_id
    target_node_id: str # Changed from target_chunk_id
    relation_type: str # Changed from type
    metadata: Optional[Dict[str, Any]] = None

class DocumentReferencesResponse(BaseModel):
    references: List[ReferenceDetail]
# --- FastAPI Lifespan ---

# --- FastAPI Lifespan (Original, without tracemalloc) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize resources
    logger.info("FastAPI application startup...")
    await db_layer.get_db_pool() # Initialize DB pool
    http_client.get_async_client() # Initialize HTTP client
    # Initialize schema if needed
    try:
        async with db_layer.get_db_connection() as conn:
            await db_layer.initialize_schema(conn)
    except Exception as e:
        logger.error(f"Failed to initialize database schema during startup: {e}")
    yield
    # Shutdown: Cleanup resources
    logger.info("FastAPI application shutdown...")
    await db_layer.close_db_pool()
    await http_client.close_async_client()

# --- FastAPI App Initialization ---

app = FastAPI(
    title="PhiloGraph Backend API",
    description="API for interacting with the PhiloGraph knowledge base.",
    version="0.1.0 (Tier 0)",
    lifespan=lifespan
)

# --- API Endpoints ---

@app.get("/", status_code=status.HTTP_200_OK)
async def read_root():
    """Basic health check endpoint."""
    return {"message": "PhiloGraph API is running"}
@app.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def handle_ingest_request(request: IngestRequest):
    """
    Triggers the ingestion pipeline for a given file or directory path
    (relative to the configured source directory).
    Returns immediately with status ACCEPTED, actual processing happens async.
    (Note: Tier 0 implementation might block until complete for simplicity).
    """
    # TDD: Test successful ingestion request for a single file path
    # TDD: Test successful ingestion request for a directory path
    # TDD: Test request with missing 'path' parameter returns 400 (handled by FastAPI/Pydantic)
    # TDD: Test request with invalid path returns appropriate error
    # TDD: Test response when ingestion pipeline returns success/skipped/error
    logger.info(f"Received ingest request for path: {request.path}")
    try:
        # For Tier 0, run synchronously and wait for the result
        # In Tier 1+, this would likely enqueue a background task
        result = await ingestion_pipeline.process_document(request.path)
        logger.info(f"Pipeline result for {request.path}: {result}") # ADDED LOGGING

        # Use .get() for safety in case 'status' key is missing
        result_status = result.get("status") # Renamed variable
        if result_status == "Success":
             # Return 200 OK (previously 201)
             return IngestResponse(status=result_status, message=result.get("message", "Ingestion successful"), document_id=result.get("document_id"))
        elif result_status == "Skipped":
             # Return 200 OK if skipped
             return IngestResponse(status=result_status, message=result.get("message", "Document already exists"))
        elif result_status == "Directory Processed":
             # Return 200 OK for directory summary
             return IngestResponse(status=result_status, message=result.get("message"), details=result.get("details"))
        elif result_status == "Error": # Explicitly check for Error status using renamed variable
            error_message = result.get("message", "Ingestion failed")
            logger.warning(f"Pipeline returned error status for {request.path}. Message: {error_message}") # ADDED LOGGING
            # More robust check for "not found" case-insensitively
            if "not found" in error_message.lower():
                logger.warning(f"Ingestion source not found for {request.path}: {error_message}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion source file not found") # Standardized detail
            else:
                logger.error(f"Ingestion pipeline returned error for {request.path}: {error_message}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
        else: # Catch unexpected status from pipeline
             logger.error(f"Unexpected status from ingestion pipeline for {request.path}. Full result: {result}") # ADDED LOGGING
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected status from ingestion pipeline.")

    except ValueError as ve: # e.g., invalid path from pipeline
        logger.error(f"Caught ValueError during ingestion for {request.path}: {ve}", exc_info=True) # ADDED LOGGING + exc_info
        # More robust check for "not found" case-insensitively
        if "not found" in str(ve).lower():
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion source file not found") # Standardized detail
        else:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as rte: # Catch errors raised by pipeline (embedding, db etc.)
        logger.error(f"Caught RuntimeError during ingestion for {request.path}: {rte}", exc_info=True) # ADDED LOGGING + exc_info
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(rte))
    except Exception as e:
        # Log the specific exception type as well
        logger.exception(f"Caught unexpected {type(e).__name__} during ingestion for {request.path}", exc_info=e) # MODIFIED LOGGING
        # Check if it's an HTTPException we already raised (like the 404) and re-raise it
        if isinstance(e, HTTPException):
            raise e
        # Otherwise, raise the generic 500, fixing the status code reference
        raise HTTPException(status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during ingestion.")

# (Remaining endpoints will be added in the next step)
@app.post("/search", response_model=SearchResponse)
async def handle_search_request(request: SearchRequest):
    """
    Performs semantic search with optional metadata filtering.
    """
    # TDD: Test successful search with query only
    # TDD: Test successful search with query and filters (author, year)
    # TDD: Test request with missing 'query' parameter returns 422 (handled by FastAPI/Pydantic)
    # TDD: Test request with invalid filter format returns 422
    # TDD: Test handling of errors from search_service (e.g., embedding failure)
    logger.info(f"Received search request: query='{request.query[:50]}...', filters={request.filters}, limit={request.limit}")
    try:
        filters_dict = request.filters.model_dump(exclude_none=True) if request.filters else None
        results = await search_service.perform_search(
            query_text=request.query,
            top_k=request.limit,
            filters=filters_dict,
            offset=request.offset # Pass offset to service layer
        )
        return SearchResponse(results=results)
    except ValueError as ve: # e.g., empty query, dimension mismatch
        logger.error(f"Value error during search: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as rte: # Catch errors raised by search_service (embedding, db etc.)
        logger.error(f"Runtime error during search: {rte}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(rte))
    except psycopg.Error as db_err: # Catch specific DB errors
        logger.error(f"Database error during search: {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Search failed due to unexpected database error")
    except Exception as e:
        logger.exception(f"Unexpected error during search for query: {request.query[:50]}...", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during search.")


@app.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: int = FastApiPath(..., gt=0, description="ID of the document to retrieve.")):
    """
    Retrieves details for a specific document.
    """
    # TDD: Test retrieving an existing document by ID
    # TDD: Test retrieving a non-existent document returns 404
    # TDD: Test handling of invalid ID format returns 422 (handled by FastAPI/Pydantic)
    logger.info(f"Received request for document ID: {doc_id}")
    try:
        async with db_layer.get_db_connection() as conn:
            document = await db_layer.get_document_by_id(conn, doc_id)
            if document:
                return document
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    except HTTPException:
         raise # Re-raise HTTPException (like 404)
    except Exception as e:
        logger.exception(f"Error retrieving document {doc_id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving document.")


@app.get("/documents/{doc_id}/references", response_model=DocumentReferencesResponse)
async def get_document_references(doc_id: int = FastApiPath(..., gt=0, description="ID of the document to retrieve references for.")):
    """
    Retrieves references originating from chunks within a specific document.
    """
    # TDD: Test retrieving references for an existing document
    # TDD: Test retrieving references for a document with no references returns empty list
    # TDD: Test retrieving references for a non-existent document returns 404
    logger.info(f"Received request for references for document ID: {doc_id}")
    try:
        async with db_layer.get_db_connection() as conn:
            # Check if document exists first
            document = await db_layer.get_document_by_id(conn, doc_id)
            if document is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

            references_raw = await db_layer.get_relationships_for_document(conn, doc_id)
            # Convert list of dicts from db_layer to list of Pydantic models
            references = [ReferenceDetail(**ref) for ref in references_raw]
            return DocumentReferencesResponse(references=references)
    except HTTPException:
         raise # Re-raise HTTP exceptions (like the 404)
    except Exception as e:
        logger.exception(f"Error retrieving references for document {doc_id}", exc_info=e)
class ChunkResponse(BaseModel):
    id: int
    section_id: int
    text_content: str
    sequence: int
    # Note: Embedding vector is likely too large/unnecessary for typical API response

@app.get("/chunks/{chunk_id}", response_model=ChunkResponse)
async def get_chunk(chunk_id: int = FastApiPath(..., gt=0, description="ID of the chunk to retrieve.")):
    """
    Retrieves details for a specific chunk.
    """
    # TDD: Test success case
    # TDD: Test not found case
    # TDD: Test DB error case
    logger.info(f"Received request for chunk ID: {chunk_id}")
    try:
        async with db_layer.get_db_connection() as conn:
            chunk_data = await db_layer.get_chunk_by_id(conn, chunk_id)
            if chunk_data is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found.")
            # Assuming db_layer returns a dict compatible with ChunkResponse
            return ChunkResponse(**chunk_data)
    except HTTPException:
         raise # Re-raise HTTP exceptions (like the 404)
    except Exception as e:
        logger.exception(f"Error retrieving chunk {chunk_id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving chunk.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving document references.")


@app.post("/collections", response_model=CollectionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(request: CollectionCreateRequest):
    """Creates a new collection."""
    # TDD: Test creating a new collection with a valid name
    # TDD: Test request with missing 'name' returns 422
    # TDD: Test creating collection with duplicate name returns error (depends on DB constraint)
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


@app.post("/collections/{collection_id}/items", response_model=CollectionItemAddResponse, status_code=status.HTTP_200_OK)
async def add_collection_item(
    request: CollectionItemAddRequest,
    collection_id: int = FastApiPath(..., gt=0, description="ID of the collection to add item to.")
):
    """Adds an item (document or chunk) to a specific collection."""
    # TDD: Test adding a valid document item to a collection
    # TDD: Test adding a valid chunk item to a collection
    # TDD: Test request with missing fields returns 422
    # TDD: Test request with invalid 'item_type' returns 422
    # TDD: Test adding item to non-existent collection returns 404 (via FK constraint)
    # TDD: Test adding non-existent item_id returns error (via FK constraint)
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
# Define a simple response model for the delete operation
class CollectionItemDeleteResponse(BaseModel):
    message: str

@app.delete(
    "/collections/{collection_id}/items/{item_type}/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an item from a collection",
    tags=["Collections"],
)
async def delete_collection_item(
    collection_id: uuid.UUID = FastApiPath(..., description="The ID of the collection"),
    item_type: Literal["document", "chunk"] = FastApiPath(..., description="The type of the item to remove ('document' or 'chunk')"),
    item_id: uuid.UUID = FastApiPath(..., description="The ID of the item to remove"),
    pool: AsyncConnectionPool = Depends(db_layer.get_db_pool),
):
    """
    Remove a specific document or chunk from a collection.
    """
    # TDD: Test success case (204)
    # TDD: Test item not found in collection (404)
    # TDD: Test collection not found (404) - handled by db_layer?
    # TDD: Test invalid item_type (422 - handled by FastAPI/Literal)
    # TDD: Test invalid UUID format (422 - handled by FastAPI)
    # TDD: Test DB error during removal (500)
    logger.info(f"Removing {item_type} {item_id} from collection {collection_id}")
    async with db_layer.get_db_connection() as conn: # Removed pool argument
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

@app.delete(
    "/collections/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT, # Correct status code
    summary="Delete a collection",
    tags=["Collections"],
    # Removed response_model as 204 should have no body
)
async def delete_collection( # Renamed function for clarity
    collection_id: uuid.UUID = FastApiPath(..., description="The ID of the collection to delete."), # Use UUID
    pool: AsyncConnectionPool = Depends(db_layer.get_db_pool), # Add pool dependency
):
    """
    Deletes a collection. Assumes DB cascade handles related items or they must be removed first.
    """
    # TDD: Test deleting an existing collection returns 204
    # TDD: Test deleting a non-existent collection returns 404
    # TDD: Test DB error during deletion returns 500
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


class CollectionItemDetail(BaseModel):
    item_type: str
    item_id: int
    added_at: str # Assuming DB returns string representation

# Removed duplicate endpoint definition. The definition below is the correct one.

@app.get("/collections/{collection_id}", response_model=CollectionGetResponse)
async def get_collection(collection_id: int = FastApiPath(..., gt=0, description="ID of the collection to retrieve.")):
    """Retrieves items within a specific collection."""
    # TDD: Test retrieving items for an existing collection
    # TDD: Test retrieving items for a non-existent collection returns 404 (or empty list?)
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
            items = [CollectionItem(**item) for item in items_raw]
            return CollectionGetResponse(collection_id=collection_id, items=items)
    except HTTPException:
         raise # Re-raise HTTP exceptions (like the 404)
    except Exception as e:
        logger.exception(f"Error retrieving collection {collection_id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving collection.")


@app.post("/acquire", response_model=AcquireInitiateResponse, status_code=status.HTTP_202_ACCEPTED)
async def initiate_acquisition_endpoint(request: AcquireInitiateRequest):
    """
    Initiates the text acquisition process by searching for a text.
    (Minimal implementation for TDD Green phase)
    """
    logger.info(f"Received acquisition initiation request: query='{request.query}', type='{request.search_type}', download={request.download}")
    try:
        # Call the acquisition service function (mocked in the test)
        acq_id = await acquisition_service.initiate_acquisition(
            query=request.query,
            search_type=request.search_type,
            download=request.download
        )
        return AcquireInitiateResponse(message="Acquisition initiated.", acquisition_id=acq_id)
    except Exception as e:
        # Basic error handling for now
        logger.exception(f"Error initiating acquisition for query: {request.query}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to initiate acquisition: {e}")


@app.post("/acquire/confirm/{acquisition_id}", response_model=AcquireConfirmResponse) # Added path parameter
async def handle_acquire_confirm(acquisition_id: UUID, request: AcquireConfirmRequest): # Added path parameter to signature
    """
    Confirms the selection of a book for download and triggers the download/processing/ingestion.
    """
    # TDD: Test confirming download with valid acquisition_id and bookDetails -> complete/processing
    # TDD: Test confirming with invalid acquisition_id returns 404
    # TDD: Test response indicating download/processing started/completed
    # TDD: Test handling errors from text_acquisition service during confirmation/download trigger
    logger.info(f"Received acquisition confirmation for ID: {acquisition_id}") # Use path parameter
    try:
        result = await acquisition_service.confirm_and_trigger_download(
            acquisition_id, request.selected_book_details # Use path parameter
        )

        if result["status"] == "complete":
             return AcquireConfirmResponse(**result)
        elif result["status"] == "error":
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Confirmation or processing failed"))
        elif result["status"] == "not_found": # Note: Service might return this status OR raise ValueError
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acquisition ID not found or invalid state") # Match test expectation
        else: # Should not happen if service logic is correct
             logger.error(f"Unexpected status from confirm_and_trigger_download: {result.get('status')}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected status during confirmation.")
    except ValueError as e: # Catch ValueError for not found case
        logger.warning(f"Acquisition task not found for ID {acquisition_id}: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        logger.exception(f"Unexpected error during acquisition confirmation for ID: {acquisition_id}", exc_info=e) # Use path parameter
        # Align detail message with test expectation
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to confirm acquisition: {e}")


@app.get("/acquire/status/{acquisition_id}", response_model=Optional[AcquisitionStatusResponse])
async def get_acquisition_status(acquisition_id: UUID = FastApiPath(..., description="ID of the acquisition process.")): # Changed type hint to UUID
    """
    Retrieves the current status of an acquisition process (uses in-memory store for Tier 0).
    """
    # TDD: Test retrieving status for ongoing acquisition
    # TDD: Test retrieving status for completed acquisition
    # TDD: Test retrieving status for failed acquisition
    # TDD: Test retrieving status for invalid acquisition_id returns 404
    logger.debug(f"Getting status for acquisition ID: {acquisition_id}")
    status_info = await acquisition_service.get_acquisition_status(acquisition_id)
    if status_info:
        # Map the dictionary to the Pydantic model
        return AcquisitionStatusResponse(**status_info)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acquisition task not found.")


# --- Main Execution (for local testing) ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server for local development...")
    # Ensure config is loaded before uvicorn starts if it relies on env vars set here
    # (config.py already loads dotenv, so should be fine)
    uvicorn.run(
        "src.philograph.api.main:app", # Path to the app instance
        host=config.BACKEND_HOST,
        port=config.BACKEND_PORT,
        reload=True, # Enable auto-reload for development
        log_level=config.LOG_LEVEL.lower()
    )