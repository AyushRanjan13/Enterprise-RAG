"""
Embedding generation using Google Generative AI (Gemini).
Free embeddings API with high performance.
"""

import logging
from typing import List
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiEmbeddingsProvider:
    """Provides embeddings using Google's Gemini API (free tier)."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the embeddings provider.
        
        Args:
            api_key: Google API key (defaults to env variable)
        """
        self.api_key = api_key or settings.google_api_key
        
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. Set it as environment variable.\n"
                "Get free API key at: https://makersuite.google.com/app/apikey"
            )
        
        # Configure genai
        genai.configure(api_key=self.api_key)
        
        # Initialize LangChain embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.api_key
        )
        
        logger.info("Gemini embeddings provider initialized")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector (list of floats)
        """
        try:
            embedding = self.embeddings.embed_query(text)
            logger.debug(f"Embedded text of length {len(text)}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to embed text: {str(e)}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = self.embeddings.embed_documents(texts)
            logger.debug(f"Embedded {len(texts)} documents")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to embed documents: {str(e)}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings.
        
        Returns:
            Dimension (typically 768 for Gemini)
        """
        # Gemini embedding-001 uses 768 dimensions
        return 768


# Singleton instance
_embeddings_provider = None


def get_embeddings_provider() -> GeminiEmbeddingsProvider:
    """Get or create embeddings provider."""
    global _embeddings_provider
    if _embeddings_provider is None:
        _embeddings_provider = GeminiEmbeddingsProvider()
    return _embeddings_provider
