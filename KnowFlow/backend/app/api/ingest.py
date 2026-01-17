"""
Document ingestion endpoints with comprehensive error handling.
Handles file uploads, chunking, embedding, and vector store insertion.
"""

import logging
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile
from typing import Optional

from app.schemas import IngestResponse
from app.config import settings
from app.rag.loader import MultiFormatLoader
from app.rag.splitter import MetadataAwareSplitter
from app.rag.vectorstore import get_vectorstore_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])

# Initialize components
loader = MultiFormatLoader()
splitter = MetadataAwareSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap
)
vectorstore_manager = get_vectorstore_manager()

# Valid options for metadata
VALID_DEPARTMENTS = ["General", "HR", "Engineering", "Finance", "Legal", "Operations"]
VALID_DOC_TYPES = ["Policy", "SOP", "Manual", "Guide", "Report", "Training", "Other"]
VALID_ACCESS_LEVELS = ["Public", "Employee", "Manager", "Executive", "Restricted"]


def validate_metadata(department: str, doc_type: str, access_level: str) -> tuple:
    """Validate and normalize metadata values."""
    department = department.strip() if department else "General"
    doc_type = doc_type.strip() if doc_type else "Document"
    access_level = access_level.strip() if access_level else "Employee"
    
    return department, doc_type, access_level


@router.post("/document", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    department: str = Form(default="General"),
    doc_type: str = Form(default="Document"),
    access_level: str = Form(default="Employee")
):
    """
    Ingest a single document (PDF, DOCX, or TXT).
    
    Args:
        file: Document file to upload
        department: Department classification
        doc_type: Document type classification
        access_level: Access level restriction
    
    Returns:
        IngestResponse with operation status and details
    
    Raises:
        HTTPException: For invalid files or processing errors
    """
    
    tmp_path = None
    try:
        # Validate file existence
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower().lstrip(".")
        if not file_ext or file_ext not in loader.SUPPORTED_FORMATS:
            supported = ", ".join(loader.SUPPORTED_FORMATS)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Supported: {supported}"
            )
        
        # Validate filename
        filename_clean = Path(file.filename).name
        if len(filename_clean) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename too long (max 255 characters)"
            )
        
        if not filename_clean or filename_clean.startswith("."):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Read and validate file size
        file_content = await file.read()
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size: {settings.max_file_size_mb}MB, got {file_size_mb:.2f}MB"
            )
        
        # Validate and normalize metadata
        department, doc_type, access_level = validate_metadata(
            department, doc_type, access_level
        )
        
        # Save temporary file
        with tempfile.NamedTemporaryFile(
            suffix=f".{file_ext}",
            delete=False
        ) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        
        # Verify temp file was created
        if not os.path.exists(tmp_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save temporary file"
            )
        
        # Load document
        try:
            metadata = {
                "department": department,
                "doc_type": doc_type,
                "access_level": access_level,
                "source": filename_clean
            }
            
            documents = loader.load_file(tmp_path, metadata)
            
            if not documents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No content found in document"
                )
            
            logger.info(f"Loaded {len(documents)} documents from {filename_clean}")
            
        except ValueError as e:
            logger.error(f"Document loading failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document format: {str(e)}"
            )
        
        # Split documents into chunks
        try:
            chunked_docs = splitter.split_documents(documents)
            if not chunked_docs:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to process document chunks"
                )
            logger.info(f"Created {len(chunked_docs)} chunks from {filename_clean}")
        except Exception as e:
            logger.error(f"Document chunking failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process document"
            )
        
        # Add to vector store
        try:
            doc_ids = vectorstore_manager.add_documents(chunked_docs)
            logger.info(f"Successfully ingested {filename_clean} with {len(doc_ids)} chunk IDs")
        except Exception as e:
            logger.error(f"Vector store insertion failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store embeddings"
            )
        
        return IngestResponse(
            success=True,
            message=f"Successfully ingested {filename_clean}",
            chunks_created=len(chunked_docs),
            document_id=f"{department}_{Path(filename_clean).stem}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during document processing"
        )
    
    finally:
        # Clean up temporary file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {tmp_path}: {str(e)}")


@router.post("/directory", tags=["Ingestion"])
async def ingest_directory(
    directory_path: str = Form(...),
    department: str = Form(default="General")
):
    """
    Ingest all supported documents from a directory.
    
    Args:
        directory_path: Path to directory containing documents
        department: Department classification for all documents
    
    Returns:
        Summary of ingestion results
    """
    try:
        # Validate directory
        dir_path = Path(directory_path)
        if not dir_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {directory_path}"
            )
        
        if not dir_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is not a directory: {directory_path}"
            )
        
        # Validate and normalize metadata
        department, _, _ = validate_metadata(department, "Document", "Employee")
        
        # Load all documents
        try:
            metadata = {"department": department}
            documents = loader.load_directory(str(dir_path), metadata, recursive=True)
            
            if not documents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No supported files found in directory"
                )
            
            logger.info(f"Loaded {len(documents)} documents from directory")
        except Exception as e:
            logger.error(f"Directory loading failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load documents from directory"
            )
        
        # Split and ingest
        try:
            chunked_docs = splitter.split_documents(documents)
            doc_ids = vectorstore_manager.add_documents(chunked_docs)
            
            return JSONResponse({
                "success": True,
                "message": f"Successfully ingested directory",
                "files_processed": len(documents),
                "chunks_created": len(chunked_docs),
                "department": department
            })
        except Exception as e:
            logger.error(f"Batch ingestion failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process documents"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during directory ingestion: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/stats", tags=["Ingestion"])
async def get_collection_stats():
    """
    Get vector store collection statistics.
    
    Returns:
        Collection statistics including document count and metadata
    """
    try:
        stats = vectorstore_manager.get_collection_stats()
        return JSONResponse({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection statistics"
        )
