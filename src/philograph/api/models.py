from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal, Union
from uuid import UUID

from ..data_access import db_layer # For reusing Document model

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
    limit: int = Field(default=10, gt=0, le=100, description="Maximum number of results.") # Assuming default 10 if config not accessible here
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
    item_id: UUID # Standardized type hint

class CollectionItemAddResponse(BaseModel):
    message: str

class CollectionDeleteResponse(BaseModel):
    message: str

class CollectionItem(BaseModel):
    item_type: str
    item_id: int # Changed back to int

class CollectionGetResponse(BaseModel):
    collection_id: int # Changed back to int
    items: List[CollectionItem]

# --- Acquisition Models (New Workflow - ADR 009) ---

class DiscoveryRequest(BaseModel):
    filters: Dict[str, Any] = Field(..., description="Filters for discovering missing texts (e.g., {'threshold': 5, 'author': 'Kant', 'tags': ['ethics']}).")

class DiscoveryResponse(BaseModel):
    discovery_id: UUID = Field(..., description="ID for this discovery session.")
    candidates: List[Dict[str, Any]] = Field(..., description="List of potential book candidates found.")

class ConfirmationRequest(BaseModel):
    selected_items: List[Union[str, Dict[str, Any]]] = Field(..., description="List of candidate IDs (md5 or index_*) or full book details objects selected for acquisition.")

class ConfirmationResponse(BaseModel):
    message: str = Field(..., description="Status message indicating processing has started.")
    status_url: str = Field(..., description="URL to check the status of the acquisition process.")

class StatusResponse(BaseModel):
    status: str = Field(..., description="Current status of the discovery session (e.g., pending_confirmation, processing, complete, complete_with_errors, error).")
    created_at: float = Field(..., description="Timestamp when the session was created.")
    candidates: Optional[List[Dict[str, Any]]] = Field(None, description="List of candidates found during discovery (cleared after confirmation).")
    selected_items: Optional[List[Dict[str, Any]]] = Field(None, description="List of items selected for confirmation.")
    processed_items: Optional[List[Dict[str, Any]]] = Field(None, description="Status details for each processed item.")
    error_message: Optional[str] = Field(None, description="Error message if the session failed.")


# --- Deprecated Acquisition Models ---
class AcquireInitiateRequest(BaseModel):
    query: str = Field(..., description="Search query for the text.")
    search_type: str = Field(default="book_meta", description="Type of search (e.g., 'book_meta', 'full_text').") # Assuming default based on test
    download: bool = Field(default=True, description="Whether to automatically download if a single exact match is found.")

class AcquireInitiateResponse(BaseModel):
    message: str
    acquisition_id: str

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

# Model for Chunk Detail
class ChunkResponse(BaseModel):
    id: int
    section_id: int
    text_content: str
    sequence: int
    # Note: Embedding vector is likely too large/unnecessary for typical API response

# Model for Collection Item Deletion
class CollectionItemDeleteResponse(BaseModel):
    message: str

# Model for Collection Item Detail (used within get_collection)
class CollectionItemDetail(BaseModel):
    item_type: str
    item_id: UUID # Changed to UUID for consistency
    added_at: str # Assuming DB returns string representation