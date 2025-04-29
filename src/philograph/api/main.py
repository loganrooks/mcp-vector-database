import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from uuid import UUID

import psycopg
import fastapi # ADDED for explicit status codes
from fastapi import FastAPI, HTTPException, Body, Path as FastApiPath, Query, status
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


# --- FastAPI Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize resources
    logger.info("FastAPI application startup...")
    await db_layer.get_db_pool() # Initialize DB pool
    http_client.get_async_client() # Initialize HTTP client
    # Initialize schema if needed (optional, might be done via separate script/migration tool)
    try:
        async with db_layer.get_db_connection() as conn:
            await db_layer.initialize_schema(conn)
    except Exception as e:
        logger.error(f"Failed to initialize database schema during startup: {e}")
        # Decide if startup should fail or continue - For now, let it continue but log error
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
            filters=filters_dict
        )
        return SearchResponse(results=results)
    except ValueError as ve: # e.g., empty query, dimension mismatch
        logger.error(f"Value error during search: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as rte: # Catch errors raised by search_service (embedding, db etc.)
        logger.error(f"Runtime error during search: {rte}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(rte))
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
    except ValueError as ve: # Catch invalid item_type from db_layer if validation added there
         logger.warning(f"Invalid item type provided: {ve}")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error adding item to collection {collection_id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error adding item to collection.")

class CollectionItemDetail(BaseModel):
    item_type: str
    item_id: int
    added_at: str # Assuming DB returns string representation

@app.get("/collections/{collection_id}", response_model=List[CollectionItemDetail], status_code=status.HTTP_200_OK)
async def get_collection(
    collection_id: int = FastApiPath(..., gt=0, description="ID of the collection to retrieve.")
):
    """Retrieves the items within a specific collection."""
    # TDD: Test retrieving items from an existing collection
    # TDD: Test retrieving items from an empty collection
    # TDD: Test retrieving items from a non-existent collection ID (should it be 404 or empty list?) - Assuming empty list for now based on db_layer behavior
    logger.info(f"Getting items for collection {collection_id}")
    try:
        async with db_layer.get_db_connection() as conn:
            items = await db_layer.get_collection_items(conn, collection_id)
            # The db_layer function is expected to return a list of dicts matching CollectionItemDetail
            if not items:
                # Raise 404 if the collection is empty (implying it doesn't exist or has no items)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
            return items
    except HTTPException as http_exc:
        # Re-raise HTTPException to let FastAPI handle it correctly
        raise http_exc
    except Exception as e:
        logger.exception(f"Error getting items for collection {collection_id}", exc_info=e)
        # Consider specific exceptions if db_layer raises them
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving collection items.")

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
            # Convert list of dicts from db_layer to list of Pydantic models
            items = [CollectionItem(**item) for item in items_raw]
            return CollectionGetResponse(collection_id=collection_id, items=items)
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
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message", "Acquisition ID not found"))
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acquisition ID not found.")


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