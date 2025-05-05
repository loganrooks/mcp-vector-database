import logging
import uuid
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Path as FastApiPath

from ..models import (
    DiscoveryRequest, DiscoveryResponse,
    ConfirmationRequest, ConfirmationResponse,
    StatusResponse,
    AcquireInitiateRequest, AcquireInitiateResponse,
    AcquireConfirmRequest, AcquireConfirmResponse
)
from ...acquisition import service as acquisition_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/acquire", tags=["Acquisition"])


@router.post("/discover", response_model=DiscoveryResponse, status_code=status.HTTP_200_OK)
async def handle_discover_request_endpoint(request: DiscoveryRequest):
    """
    Initiates the discovery phase of text acquisition based on provided filters.
    Finds potential candidates and searches for them using the zlibrary-mcp server.
    """
    logger.info(f"Received discovery request with filters: {request.filters}")
    try:
        result = await acquisition_service.handle_discovery_request(request.filters)

        if result['status'] == 'success':
            # Convert discovery_id string from service to UUID for response model
            return DiscoveryResponse(
                discovery_id=UUID(result['discovery_id']),
                candidates=result['candidates']
            )
        elif result['status'] == 'no_candidates':
             # Convert discovery_id string from service to UUID for response model
             return DiscoveryResponse(
                discovery_id=UUID(result['discovery_id']),
                candidates=[]
            )
        elif result['status'] == 'error':
            logger.error(f"Discovery request failed: {result.get('message')}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get('message', "Discovery failed"))
        else:
            logger.error(f"Unexpected status from handle_discovery_request: {result.get('status')}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error during discovery.")

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        logger.exception("Unexpected error during acquisition discovery endpoint", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during discovery.")


@router.post("/confirm/{discovery_id}", response_model=ConfirmationResponse, status_code=status.HTTP_202_ACCEPTED)
async def handle_confirm_request_endpoint(
    request: ConfirmationRequest,
    discovery_id: UUID = FastApiPath(..., description="ID of the discovery session to confirm.")
):
    """
    Confirms the selection of items from a discovery session, triggering download,
    processing, and ingestion via the acquisition service.
    """
    logger.info(f"Received confirmation request for discovery ID: {discovery_id}")
    try:
        # Pass discovery_id as string to service layer
        result = await acquisition_service.handle_confirmation_request(str(discovery_id), request.selected_items)

        if result['status'] == 'processing_started':
            # Need the app instance to generate the URL, which isn't available here.
            # We'll construct it manually or pass the app instance if needed later.
            # For now, returning a relative path.
            status_url = f"/acquire/status/{discovery_id}" # Relative path
            return ConfirmationResponse(
                message="Acquisition confirmed. Download and processing initiated.",
                status_url=status_url
            )
        elif result['status'] == 'not_found':
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discovery session not found or expired.")
        elif result['status'] == 'invalid_state':
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Discovery session is not awaiting confirmation.")
        elif result['status'] == 'invalid_selection':
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid items selected: {result.get('details', '')}")
        elif result['status'] == 'error': # Catch generic errors from service
             logger.error(f"Confirmation request failed for {discovery_id}: {result.get('message')}")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get('message', "Confirmation failed"))
        else:
            logger.error(f"Unexpected status from handle_confirmation_request: {result.get('status')}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error during confirmation.")

    except HTTPException:
        raise # Re-raise HTTP exceptions
    except Exception as e:
        logger.exception(f"Unexpected error during acquisition confirmation endpoint for ID: {discovery_id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during confirmation.")


@router.get("/status/{discovery_id}", response_model=Optional[StatusResponse], name="get_acquisition_status_endpoint") # Renamed path param, added name
async def get_acquisition_status_endpoint(discovery_id: UUID = FastApiPath(..., description="ID of the discovery session.")): # Renamed path param
    """
    Retrieves the current status of an acquisition discovery session.
    """
    logger.debug(f"Getting status for discovery ID: {discovery_id}")
    # Pass discovery_id as string to service layer
    status_info = await acquisition_service.get_status(str(discovery_id))
    if status_info:
        # Map the dictionary to the Pydantic model
        return StatusResponse(**status_info)
    else:
        # Return 404 if session not found or expired
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discovery session not found or expired.")


# --- Deprecated Acquisition Endpoints ---

@router.post("", response_model=AcquireInitiateResponse, status_code=status.HTTP_202_ACCEPTED, deprecated=True)
async def initiate_acquisition_endpoint(request: AcquireInitiateRequest):
    """
    (DEPRECATED - Use /acquire/discover instead)
    Initiates the text acquisition process by searching for a text.
    """
    logger.warning("Deprecated endpoint /acquire called. Use /acquire/discover instead.")
    # Minimal implementation just to avoid breaking old clients immediately
    return AcquireInitiateResponse(message="This endpoint is deprecated. Use /acquire/discover.", acquisition_id=str(uuid.uuid4()))


@router.post("/confirm/{acquisition_id}", response_model=AcquireConfirmResponse, deprecated=True)
async def handle_acquire_confirm(acquisition_id: UUID, request: AcquireConfirmRequest):
    """
    (DEPRECATED - Use /acquire/confirm/{discovery_id} instead)
    Confirms the selection of a book for download and triggers the download/processing/ingestion.
    """
    logger.warning(f"Deprecated endpoint /acquire/confirm/{acquisition_id} called. Use /acquire/confirm/{{discovery_id}} instead.")
    # Minimal implementation
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="This endpoint is deprecated. Use /acquire/confirm/{discovery_id} instead.")