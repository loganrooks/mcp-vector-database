import logging
from typing import Any, Dict, List, Optional

import fastapi
from fastapi import APIRouter, HTTPException, status

from ..models import IngestRequest, IngestResponse
from ...ingestion import pipeline as ingestion_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Ingestion"])
async def handle_ingest_request(request: IngestRequest):
    """
    Triggers the ingestion pipeline for a given file or directory path
    (relative to the configured source directory).
    Returns immediately with status ACCEPTED, actual processing happens async.
    (Note: Tier 0 implementation might block until complete for simplicity).
    """
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