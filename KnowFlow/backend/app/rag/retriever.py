"""
Advanced retriever implementations: Similarity, MMR, and MultiQuery.
Handles metadata filtering and role-based access.
"""

import logging 
from typing import List, Optional, Dict 
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.retrievers.multi_query import MultiQueryRetriever
from app.config import settings
from app.rag.vectorstore import get_vectorstore_manager

logger = logging.getLogger(__name__)


class AdvancedRetriever:
    """
    Multi-strategy retriever supporting similarity, MMR, and multi-query.
    Includes metadata filtering and role-based access control.
    """
    
    def __init__(self):
        """Initialize retriever with vector store."""
        self.vectorstore_manager = get_vectorstore_manager()
        self.vectorstore = self.vectorstore_manager.get_vectorstore()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.google_api_key
        )
    
    def _build_metadata_filter(
        self,
        role: str,
        department: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Build metadata filter based on role and department.
        
        Args:
            role: User role (admin, hr, engineer, finance, general)
            department: Optional specific department filter
        
        Returns:
            Metadata filter dict or None
        """
        # Admin can access all
        if role == "admin":
            return None
        
        # Build department filter based on role
        role_departments = settings.roles.get(role, settings.roles["general"])
        
        # If specific department requested, use it if accessible
        if department and department in role_departments:
            return {"department": {"$eq": department}}
        
        # Use role's departments
        if role_departments == ["all"]:
            return None
        
        # Return filter for allowed departments
        if len(role_departments) == 1:
            return {"department": {"$eq": role_departments[0]}}
        
        return {"department": {"$in": role_departments}}
    
    def retrieve_similarity(
        self,
        query: str,
        k: int = 5,
        role: str = "general",
        department: Optional[str] = None
    ) -> List[tuple]:
        """
        Retrieve using similarity search.
        
        Args:
            query: Query text
            k: Number of results
            role: User role for access control
            department: Optional department filter
        
        Returns:
            List of (Document, score) tuples
        """
        metadata_filter = self._build_metadata_filter(role, department)
        
        try:
            results = self.vectorstore_manager.similarity_search_with_score(
                query,
                k=k,
                filter=metadata_filter
            )
            logger.info(f"Similarity retrieval returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Similarity retrieval failed: {str(e)}")
            return []
    
    def retrieve_mmr(
        self,
        query: str,
        k: int = 5,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        role: str = "general",
        department: Optional[str] = None
    ) -> List[Document]:
        """
        Retrieve using Maximum Marginal Relevance (reduces redundancy).
        
        Args:
            query: Query text
            k: Number of results
            fetch_k: Number of candidates to consider
            lambda_mult: Diversity parameter (0.5 = balanced)
            role: User role for access control
            department: Optional department filter
        
        Returns:
            List of diverse documents
        """
        metadata_filter = self._build_metadata_filter(role, department)
        
        try:
            results = self.vectorstore_manager.mmr_search(
                query,
                k=k,
                fetch_k=fetch_k,
                lambda_mult=lambda_mult,
                filter=metadata_filter
            )
            logger.info(f"MMR retrieval returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"MMR retrieval failed: {str(e)}")
            return []
    
    def retrieve_multi_query(
        self,
        query: str,
        k: int = 5,
        role: str = "general",
        department: Optional[str] = None
    ) -> List[Document]:
        """
        Retrieve using multi-query approach.
        Generates multiple query variations to improve recall.
        
        Args:
            query: Query text
            k: Number of results
            role: User role for access control
            department: Optional department filter
        
        Returns:
            List of documents from multiple query variations
        """
        try:
            logger.info(f"Multi-query retrieval for: {query}")
            
            # Create base retriever with metadata filter
            metadata_filter = self._build_metadata_filter(role, department)
            
            # Create base retriever from vector store
            base_retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": k, "filter": metadata_filter}
            )
            
            # Create MultiQueryRetriever with LLM
            retriever = MultiQueryRetriever.from_llm(
                retriever=base_retriever,
                llm=self.llm
            )
            
            # Get results using MultiQueryRetriever
            results = retriever.invoke(query)
            logger.info(f"Multi-query retrieval returned {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"Multi-query retrieval failed: {str(e)}")
            # Fallback to MMR retrieval
            return self.retrieve_mmr(query, k, role=role, department=department)
    
    def retrieve(
        self,
        query: str,
        method: str = "mmr",
        k: int = 5,
        role: str = "general",
        department: Optional[str] = None
    ) -> List[Document]:
        """
        Unified retrieval interface.
        
        Args:
            query: Query text
            method: "similarity", "mmr", or "multi_query"
            k: Number of results
            role: User role
            department: Optional department filter
        
        Returns:
            List of retrieved documents
        """
        if method == "similarity":
            results = self.retrieve_similarity(query, k, role, department)
            # Convert (doc, score) tuples to just docs
            return [doc for doc, score in results]
        elif method == "multi_query":
            return self.retrieve_multi_query(query, k, role, department)
        else:  # Default to MMR
            return self.retrieve_mmr(query, k, role=role, department=department)


# Singleton instance
_retriever = None


def get_retriever() -> AdvancedRetriever:
    """Get or create retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = AdvancedRetriever()
    return _retriever
