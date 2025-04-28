import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import psycopg
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

class AcquireRequest(BaseModel):
    text_details: Optional[Dict[str, str]] = None # e.g., {"title": "...", "author": "..."}
    find_missing_threshold: Optional[int] = Query(default=None, description="Threshold for finding missing texts (alternative to text_details).")

class AcquireResponseNeedsConfirmation(BaseModel):
    status: str = "needs_confirmation"
    message: str
    options: List[Dict[str, Any]] # List of bookDetails from zlibrary-mcp
    acquisition_id: str

class AcquireResponseError(BaseModel):
    status: str = "error"
    message: str

class AcquireConfirmRequest(BaseModel):
    acquisition_id: str
    selected_book_details: Dict[str, Any] # Full bookDetails object

class AcquireConfirmResponse(BaseModel):
    status: str # e.g., "complete", "error"
    message: str
    document_id: Optional[int] = None # PhiloGraph doc ID if ingestion successful
    status_url: Optional[str] = None # Optional: URL to check status later

class AcquisitionStatusResponse(BaseModel):
    status: str
    details: Optional[Dict[str, str]] = None
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
    # try:
    #     async with db_layer.get_db_connection() as conn:
    #         await db_layer.initialize_schema(conn)
    # except Exception as e:
    #     logger.error(f"Failed to initialize database schema during startup: {e}")
    #     # Decide if startup should fail or continue
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

        if result["status"] == "Success":
             # Return 201 Created if a single doc was successfully added
             # Changed status code to 200 OK as 201 might imply resource creation *at this endpoint*
             return IngestResponse(status=result["status"], message=result.get("message", "Ingestion successful"), document_id=result.get("document_id"))
        elif result["status"] == "Skipped":
             # Return 200 OK if skipped
             return IngestResponse(status=result["status"], message=result.get("message", "Document already exists"))
        elif result["status"] == "Directory Processed":
             # Return 200 OK for directory summary
             return IngestResponse(status=result["status"], message=result.get("message"), details=result.get("details"))
        else: # Error case
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Ingestion failed"))

    except ValueError as ve: # e.g., invalid path from pipeline
        logger.error(f"Value error during ingestion for {request.path}: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as rte: # Catch errors raised by pipeline (embedding, db etc.)
        logger.error(f"Runtime error during ingestion for {request.path}: {rte}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(rte))
    except Exception as e:
        logger.exception(f"Unexpected error during ingestion for {request.path}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during ingestion.")

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
        filters_dict = request.filters.dict(exclude_none=True) if request.filters else None
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
    except ValueError as ve: # Catch invalid item_type from db_layer if validation added there
         logger.warning(f"Invalid item type provided: {ve}")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error adding item to collection {collection_id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error adding item to collection.")


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


@app.post("/acquire",
          response_model=AcquireResponseNeedsConfirmation | AcquireResponseError, # Union for multiple responses
          responses={ # Define possible responses for OpenAPI docs
              status.HTTP_200_OK: {"model": AcquireResponseNeedsConfirmation},
              status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": AcquireResponseError},
              status.HTTP_400_BAD_REQUEST: {"model": AcquireResponseError}
          })
async def handle_acquire_request(request: AcquireRequest):
    """
    Starts the text acquisition process.
    Either provide `text_details` to search for a specific text,
    or provide `find_missing_threshold` to search for frequently cited missing texts.
    """
    # TDD: Test triggering acquisition with valid text details -> needs_confirmation
    # TDD: Test triggering acquisition with threshold -> needs_confirmation or error
    # TDD: Test request missing required details returns 400/422
    # TDD: Test handling errors from the text_acquisition service
    logger.info(f"Received acquisition request: {request.dict(exclude_none=True)}")

    if request.text_details:
        try:
            result = await acquisition_service.start_acquisition_search(request.text_details)
            if result["status"] == "needs_confirmation":
                return AcquireResponseNeedsConfirmation(**result)
            else: # status == "error"
                # Return 500 for now, could refine based on error type
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Acquisition search failed"))
        except Exception as e:
             logger.exception("Unexpected error during specific text acquisition search", exc_info=e)
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {e}")

    elif request.find_missing_threshold is not None:
        # Placeholder: Logic to find missing texts based on threshold and then call start_acquisition_search
        # This requires the find_missing_texts_from_citations function to be implemented
        logger.warning("Finding missing texts by threshold not fully implemented yet.")
        # Example:
        # missing_texts = await acquisition_service.find_missing_texts_from_citations(request.find_missing_threshold)
        # if not missing_texts:
        #     return AcquireResponseError(status="error", message="No missing texts found above threshold.")
        # # How to handle multiple missing texts? Trigger one search? Return list?
        # # For now, just return error indicating not implemented
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Finding missing texts by threshold not implemented.")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either 'text_details' or 'find_missing_threshold' must be provided.")


@app.post("/acquire/confirm", response_model=AcquireConfirmResponse)
async def handle_acquire_confirm(request: AcquireConfirmRequest):
    """
    Confirms the selection of a book for download and triggers the download/processing/ingestion.
    """
    # TDD: Test confirming download with valid acquisition_id and bookDetails -> complete/processing
    # TDD: Test confirming with invalid acquisition_id returns 404
    # TDD: Test response indicating download/processing started/completed
    # TDD: Test handling errors from text_acquisition service during confirmation/download trigger
    logger.info(f"Received acquisition confirmation for ID: {request.acquisition_id}")
    try:
        result = await acquisition_service.confirm_and_trigger_download(
            request.acquisition_id, request.selected_book_details
        )

        if result["status"] == "complete":
             return AcquireConfirmResponse(**result)
        elif result["status"] == "error":
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("message", "Confirmation or processing failed"))
        elif result["status"] == "not_found":
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("message", "Acquisition ID not found"))
        else: # Should not happen if service logic is correct
             logger.error(f"Unexpected status from confirm_and_trigger_download: {result.get('status')}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected status during confirmation.")

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        logger.exception(f"Unexpected error during acquisition confirmation for ID: {request.acquisition_id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {e}")


@app.get("/acquire/status/{acquisition_id}", response_model=Optional[AcquisitionStatusResponse])
async def get_acquisition_status(acquisition_id: str = FastApiPath(..., description="ID of the acquisition process.")):
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