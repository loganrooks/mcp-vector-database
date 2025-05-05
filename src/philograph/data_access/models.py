from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Pydantic Models for Data Access Layer ---

class Document(BaseModel):
    id: int
    title: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    source_path: str
    metadata: Optional[Dict[str, Any]] = None

class Section(BaseModel):
    id: int
    doc_id: int
    title: Optional[str] = None
    level: int
    sequence: int

class Chunk(BaseModel):
    id: int
    section_id: int
    text_content: str
    sequence: int
    # embedding_vector: List[float] # Often excluded from models returned by DB layer

class SearchResult(BaseModel):
    chunk_id: int
    section_id: int
    doc_id: int
    text_content: str
    distance: float
    # Add other relevant fields like document title, author, etc. if joined in the query
    doc_title: Optional[str] = None
    doc_author: Optional[str] = None
    doc_year: Optional[int] = None
    doc_source_path: Optional[str] = None
    section_title: Optional[str] = None
    chunk_sequence: Optional[int] = None

class Relationship(BaseModel):
    id: int
    source_node_id: str
    target_node_id: str
    relation_type: str
    metadata: Optional[Dict[str, Any]] = None