"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DocumentMetadata(BaseModel):
    """Metadata for ingested documents."""
    source: str
    department: str = Field(default="General")
    doc_type: str = Field(default="Unknown")
    section: Optional[str] = None
    page_number: Optional[int] = None
    access_level: str = Field(default="Employee")


class DocumentChunk(BaseModel):
    """A single text chunk with metadata."""
    content: str
    metadata: DocumentMetadata
    chunk_id: str


class IngestRequest(BaseModel):
    """Request to ingest a document."""
    filename: str
    department: str = Field(default="General")
    doc_type: str = Field(default="Document")
    access_level: str = Field(default="Employee")


class IngestResponse(BaseModel):
    """Response after document ingestion."""
    success: bool
    message: str
    chunks_created: int
    document_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QueryRequest(BaseModel):
    """Request to query documents."""
    query: str = Field(..., min_length=3, max_length=500)
    role: str = Field(default="general")
    department: Optional[str] = None
    retriever_type: str = Field(default="mmr")
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedDocument(BaseModel):
    """A document retrieved by the retriever."""
    content: str
    metadata: DocumentMetadata
    relevance_score: float


class QueryResponse(BaseModel):
    """Response to a query."""
    answer: str
    sources: List[RetrievedDocument]
    query: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = "gemini-1.5-flash"
    tokens_used: Optional[int] = None


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: Optional[List[RetrievedDocument]] = None


class ChatHistory(BaseModel):
    """Chat conversation history."""
    session_id: str
    messages: List[ChatMessage]
    department: Optional[str] = None
    role: str = Field(default="general")
