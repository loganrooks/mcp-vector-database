import logging
import psycopg
from fastapi import APIRouter, HTTPException, status

from ..models import SearchRequest, SearchResponse
from ...search import service as search_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/search", response_model=SearchResponse, tags=["Search"])
async def handle_search_request(request: SearchRequest):
    """
    Performs semantic search with optional metadata filtering.
    """
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