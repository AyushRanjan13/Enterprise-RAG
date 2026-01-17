"""
Query endpoints for RAG-based question answering.
Handles user queries with advanced validation and error recovery.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from app.schemas import QueryRequest, QueryResponse, RetrievedDocument
from app.rag.chain import get_rag_chain
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/query", tags=["Query"])

# Initialize RAG chain
try:
    rag_chain = get_rag_chain()
    logger.info("RAG chain initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RAG chain: {str(e)}")
    rag_chain = None

# Valid retriever types
VALID_RETRIEVER_TYPES = ["similarity", "mmr", "multi_query"]
VALID_ROLES = ["admin", "hr", "engineer", "finance", "general"]


def validate_query_input(request: QueryRequest) -> None:
    """Validate query input parameters."""
    # Validate query text
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )
    
    if len(request.query.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be at least 2 characters long"
        )
    
    if len(request.query) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query too long (maximum 1000 characters)"
        )
    
    # Validate role
    if request.role and request.role.lower() not in VALID_ROLES:
        logger.warning(f"Invalid role requested: {request.role}")
        # Default to general instead of erroring
        request.role = "general"
    
    # Validate retriever type
    if request.retriever_type not in VALID_RETRIEVER_TYPES:
        logger.warning(f"Invalid retriever type: {request.retriever_type}, using mmr")
        request.retriever_type = "mmr"
    
    # Validate top_k
    if request.top_k < 1 or request.top_k > 20:
        logger.warning(f"Invalid top_k: {request.top_k}, using default 5")
        request.top_k = 5


@router.post("/ask", response_model=QueryResponse, tags=["Query"])
async def ask_question(request: QueryRequest):
    """
    Ask a question to the knowledge base with RAG.
    
    Args:
        request: QueryRequest containing query and parameters
    
    Returns:
        QueryResponse with answer and source documents
    
    Raises:
        HTTPException: For validation or processing errors
    """
    
    if not rag_chain:
        logger.error("RAG chain not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again."
        )
    
    try:
        # Validate input
        validate_query_input(request)
        query_text = request.query.strip()
        
        logger.info(
            f"Processing query - Role: {request.role}, "
            f"Retriever: {request.retriever_type}, Query: {query_text[:50]}..."
        )
        
        # Execute RAG pipeline
        try:
            result = rag_chain.query(
                query=query_text,
                retrieval_method=request.retriever_type,
                top_k=request.top_k,
                role=request.role,
                department=request.department
            )
        except Exception as e:
            logger.error(f"RAG pipeline error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process query. Please try again with a different question."
            )
        
        # Validate result structure
        if not result or "answer" not in result:
            logger.error("Invalid result from RAG chain")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate answer"
            )
        
        # Format sources
        sources = []
        try:
            for idx, source_info in enumerate(result.get("sources", [])[:10]):  # Limit to 10
                if not isinstance(source_info, dict):
                    logger.warning(f"Invalid source format at index {idx}")
                    continue
                
                try:
                    sources.append(
                        RetrievedDocument(
                            content=source_info.get("content", "")[:500],  # Limit content
                            metadata={
                                "source": source_info.get("metadata", {}).get("source", "Unknown"),
                                "department": source_info.get("metadata", {}).get("department", "General"),
                                "doc_type": source_info.get("metadata", {}).get("doc_type", "Document"),
                                "section": source_info.get("metadata", {}).get("section", ""),
                                "page_number": source_info.get("metadata", {}).get("page", ""),
                                "access_level": source_info.get("metadata", {}).get("access_level", "Employee")
                            },
                            relevance_score=float(source_info.get("score", 0.5))
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to format source {idx}: {str(e)}")
                    continue
        except Exception as e:
            logger.warning(f"Error processing sources: {str(e)}")
            # Continue without sources rather than failing completely
        
        answer_text = str(result.get("answer", "")).strip()
        if not answer_text:
            answer_text = "I was unable to find relevant information to answer your question."
        
        return QueryResponse(
            answer=answer_text,
            sources=sources,
            query=query_text,
            timestamp=datetime.utcnow(),
            model_used="gemini-1.5-flash",
            tokens_used=result.get("tokens_used")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ask_question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again."
        )


@router.post("/search", tags=["Query"])
async def search_documents(request: QueryRequest):
    """
    Search documents without generating an answer.
    Returns raw retrieved documents.
    
    Args:
        request: QueryRequest with search parameters
    
    Returns:
        List of retrieved documents with metadata
    """
    
    if not rag_chain:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )
    
    try:
        # Validate input
        validate_query_input(request)
        query_text = request.query.strip()
        
        logger.info(f"Search query: {query_text[:50]}...")
        
        # Retrieve documents
        try:
            retriever = rag_chain.retriever
            docs = retriever.retrieve(
                query=query_text,
                method=request.retriever_type,
                k=min(request.top_k, 20),  # Cap at 20
                role=request.role,
                department=request.department
            )
        except Exception as e:
            logger.error(f"Retrieval error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve documents"
            )
        
        if not docs:
            logger.info("No documents found for query")
            return {
                "query": query_text,
                "documents": [],
                "count": 0,
                "message": "No matching documents found"
            }
        
        # Format response
        results = []
        for idx, doc in enumerate(docs):
            try:
                results.append({
                    "id": idx,
                    "content": str(doc.page_content)[:1000],  # Limit content size
                    "metadata": {
                        "source": doc.metadata.get("source", "Unknown") if doc.metadata else "Unknown",
                        "department": doc.metadata.get("department", "General") if doc.metadata else "General",
                        "doc_type": doc.metadata.get("doc_type", "Document") if doc.metadata else "Document",
                        "section": doc.metadata.get("section", "") if doc.metadata else "",
                        "page": doc.metadata.get("page_number", "") if doc.metadata else "",
                        "access_level": doc.metadata.get("access_level", "Employee") if doc.metadata else "Employee"
                    }
                })
            except Exception as e:
                logger.warning(f"Error formatting document {idx}: {str(e)}")
                continue
        
        return {
            "query": query_text,
            "documents": results,
            "count": len(results),
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed. Please try again."
        )


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for system status.
    
    Returns:
        System health status and connectivity information
    """
    try:
        if not rag_chain:
            return {
                "status": "unhealthy",
                "error": "RAG chain not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }, status.HTTP_503_SERVICE_UNAVAILABLE
        
        # Test vector store connection
        try:
            stats = rag_chain.retriever.vectorstore_manager.get_collection_stats()
            vector_store_healthy = True
        except Exception as e:
            logger.warning(f"Vector store check failed: {str(e)}")
            stats = {"error": str(e)}
            vector_store_healthy = False
        
        return {
            "status": "healthy" if vector_store_healthy else "degraded",
            "components": {
                "rag_chain": "initialized",
                "vector_store": "connected" if vector_store_healthy else "error",
                "llm": "ready"
            },
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "unhealthy",
            "error": "Health check failed",
            "timestamp": datetime.utcnow().isoformat()
        }, status.HTTP_500_INTERNAL_SERVER_ERROR
