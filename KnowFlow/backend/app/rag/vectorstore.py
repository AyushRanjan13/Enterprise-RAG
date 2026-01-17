"""
Vector store abstraction layer for Chroma.
Supports document storage, retrieval, and metadata filtering.
"""

import logging
from typing import List, Optional, Dict
from pathlib import Path
from langchain_core.documents import Document
from langchain_chroma import Chroma
from app.config import settings
from app.rag.embeddings import get_embeddings_provider

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages Chroma vector store with document persistence."""
    
    def __init__(self, persist_dir: str = None):
        """
        Initialize vector store.
        
        Args:
            persist_dir: Directory for Chroma persistence
        """
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        
        # Create persistence directory
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        
        # Get embeddings provider
        embeddings = get_embeddings_provider().embeddings
        
        # Initialize Chroma
        self.vectorstore = Chroma(
            collection_name="knowflow_documents",
            embedding_function=embeddings,
            persist_directory=self.persist_dir
        )
        
        logger.info(f"VectorStore initialized with persist_dir: {self.persist_dir}")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to vector store.
        
        Args:
            documents: List of Document objects with content and metadata
        
        Returns:
            List of document IDs added
        """
        try:
            # Add documents and get IDs
            ids = self.vectorstore.add_documents(documents)
            logger.info(f"Added {len(ids)} documents to vector store")
            return ids
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise
    
    def get_vectorstore(self):
        """Get the underlying Chroma vectorstore object."""
        return self.vectorstore
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[Document]:
        """
        Search by similarity.
        
        Args:
            query: Query text
            k: Number of results
            filter: Optional metadata filter
        
        Returns:
            List of similar documents
        """
        try:
            if filter:
                results = self.vectorstore.similarity_search(
                    query,
                    k=k,
                    filter=filter
                )
            else:
                results = self.vectorstore.similarity_search(query, k=k)
            
            logger.debug(f"Found {len(results)} similar documents for query")
            return results
        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            raise
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None
    ) -> List[tuple]:
        """
        Search by similarity with relevance scores.
        
        Args:
            query: Query text
            k: Number of results
            filter: Optional metadata filter
        
        Returns:
            List of (Document, score) tuples
        """
        try:
            if filter:
                results = self.vectorstore.similarity_search_with_score(
                    query,
                    k=k,
                    filter=filter
                )
            else:
                results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            return results
        except Exception as e:
            logger.error(f"Similarity search with score failed: {str(e)}")
            raise
    
    def mmr_search(
        self,
        query: str,
        k: int = 5,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        filter: Optional[Dict] = None
    ) -> List[Document]:
        """
        Maximum Marginal Relevance search (reduces redundancy).
        
        Args:
            query: Query text
            k: Number of results
            fetch_k: Number of candidates to fetch before MMR
            lambda_mult: Diversity parameter (0=max diversity, 1=max relevance)
            filter: Optional metadata filter
        
        Returns:
            List of diverse documents
        """
        try:
            if filter:
                results = self.vectorstore.max_marginal_relevance_search(
                    query,
                    k=k,
                    fetch_k=fetch_k,
                    lambda_mult=lambda_mult,
                    filter=filter
                )
            else:
                results = self.vectorstore.max_marginal_relevance_search(
                    query,
                    k=k,
                    fetch_k=fetch_k,
                    lambda_mult=lambda_mult
                )
            
            logger.debug(f"MMR search returned {len(results)} diverse documents")
            return results
        except Exception as e:
            logger.error(f"MMR search failed: {str(e)}")
            raise
    
    def delete_documents(self, ids: List[str]) -> bool:
        """
        Delete documents by ID.
        
        Args:
            ids: List of document IDs to delete
        
        Returns:
            Success status
        """
        try:
            self.vectorstore.delete(ids)
            logger.info(f"Deleted {len(ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        try:
            collection = self.vectorstore._collection
            return {
                "collection_name": collection.name,
                "document_count": collection.count(),
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {}


# Singleton instance
_vectorstore_manager = None


def get_vectorstore_manager() -> VectorStoreManager:
    """Get or create vector store manager."""
    global _vectorstore_manager
    if _vectorstore_manager is None:
        _vectorstore_manager = VectorStoreManager()
    return _vectorstore_manager
