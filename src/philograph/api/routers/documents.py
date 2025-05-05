import logging
import psycopg
from fastapi import APIRouter, HTTPException, status, Path as FastApiPath

from ..models import DocumentResponse, DocumentReferencesResponse, ChunkResponse, ReferenceDetail
from ...data_access import db_layer

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/documents/{doc_id}", response_model=DocumentResponse, tags=["Documents & Chunks"])
async def get_document(doc_id: int = FastApiPath(..., gt=0, description="ID of the document to retrieve.")):
    """
    Retrieves details for a specific document.
    """
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


@router.get("/documents/{doc_id}/references", response_model=DocumentReferencesResponse, tags=["Documents & Chunks"])
async def get_document_references(doc_id: int = FastApiPath(..., gt=0, description="ID of the document to retrieve references for.")):
    """
    Retrieves references originating from chunks within a specific document.
    """
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
    except Exception as e: # Catch other potential errors
        logger.exception(f"Error retrieving references for document {doc_id}", exc_info=e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error retrieving document references.")


@router.get("/chunks/{chunk_id}", response_model=ChunkResponse, tags=["Documents & Chunks"])
async def get_chunk(chunk_id: int = FastApiPath(..., gt=0, description="ID of the chunk to retrieve.")):
    """
    Retrieves details for a specific chunk.
    """
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