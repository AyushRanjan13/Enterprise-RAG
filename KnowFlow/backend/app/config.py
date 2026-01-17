"""
Configuration management for KnowFlow RAG system.
Loads environment variables and provides config classes.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Literal

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_title: str = "KnowFlow - Enterprise Knowledge Assistant"
    api_version: str = "1.0.0"
    api_description: str = "RAG-based system for querying internal documents"
    
    # LLM Configuration (Google Gemini)
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_model: str = "gemini-1.5-flash"  # Free tier model
    temperature: float = 0.7
    max_tokens: int = 1024
    
    # Vector DB Configuration
    vector_db_type: Literal["chroma"] = "chroma"
    chroma_persist_dir: str = "./data/chroma_db"
    
    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    supported_file_types: list = ["pdf", "docx", "txt"]
    max_file_size_mb: int = 25
    
    # Retrieval Configuration
    retriever_type: Literal["similarity", "mmr", "multi_query"] = "mmr"
    retriever_k: int = 5  # Number of documents to retrieve
    
    # Role-based access control
    roles: dict = {
        "admin": ["all"],
        "hr": ["HR", "People"],
        "engineer": ["Engineering", "Tech"],
        "finance": ["Finance", "Budget"],
        "general": ["General", "Public"]
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
settings = Settings()
