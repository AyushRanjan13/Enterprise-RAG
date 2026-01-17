"""
Advanced text splitting with metadata preservation.
Implements RecursiveCharacterTextSplitter with section-aware chunking.
"""

from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)


class MetadataAwareSplitter:
    """
    Text splitter that preserves and enriches document metadata.
    Supports section-aware chunking.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize splitter.
        
        Args:
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            separators: Custom separators for splitting
        """
        if separators is None:
            separators = [
                "\n\n",      # Paragraph breaks
                "\n",        # Line breaks
                ". ",        # Sentences
                " ",         # Words
                ""           # Characters
            ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators
        )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_documents(
        self,
        documents: List[Document],
        section_key: Optional[str] = None
    ) -> List[Document]:
        """
        Split documents while preserving metadata.
        
        Args:
            documents: List of Document objects
            section_key: Optional metadata key for section names
        
        Returns:
            List of chunked documents with enriched metadata
        """
        chunked_docs = []
        
        for doc in documents:
            # Split the document
            splits = self.splitter.split_documents([doc])
            
            # Enrich metadata for each chunk
            for chunk_idx, chunk in enumerate(splits):
                # Preserve original metadata
                chunk.metadata["chunk_index"] = chunk_idx
                chunk.metadata["total_chunks"] = len(splits)
                chunk.metadata["chunk_size"] = len(chunk.page_content)
                
                # Add source reference
                if "source" not in chunk.metadata:
                    chunk.metadata["source"] = "unknown"
                
                # Add section if provided
                if section_key and section_key in doc.metadata:
                    chunk.metadata["section"] = doc.metadata[section_key]
                
                chunked_docs.append(chunk)
            
            logger.debug(f"Split '{doc.metadata.get('source', 'unknown')}' into {len(splits)} chunks")
        
        logger.info(f"Created {len(chunked_docs)} chunks from {len(documents)} documents")
        return chunked_docs
    
    def split_text(self, text: str, metadata: Optional[dict] = None) -> List[Document]:
        """
        Split raw text into documents.
        
        Args:
            text: Text to split
            metadata: Optional metadata to attach
        
        Returns:
            List of Document objects
        """
        doc = Document(
            page_content=text,
            metadata=metadata or {}
        )
        return self.split_documents([doc])
