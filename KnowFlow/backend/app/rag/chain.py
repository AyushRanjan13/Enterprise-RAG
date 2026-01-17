"""
RAG chain implementation with Gemini LLM.
Handles context injection, prompt engineering, and response generation.
"""

import logging
from typing import List, Optional, Dict
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from app.config import settings
from app.rag.retriever import get_retriever
from app.rag.vectorstore import get_vectorstore_manager

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are KnowFlow, an enterprise knowledge assistant for internal company documents.

Your responsibilities:
1. Answer questions ONLY using the provided context
2. Be precise, concise, and professional
3. If the answer is not found in the documents, clearly state: "I don't have this information in the knowledge base."
4. Always cite your sources with document name and section
5. Avoid speculation or information outside the provided context
6. Be helpful and user-friendly in tone

Context Documents:
{context}

Instructions:
- Focus on accuracy over completeness
- Provide actionable answers
- Use bullet points for complex answers
- Reference specific documents when relevant"""


PROMPT_TEMPLATE = """You are KnowFlow, an enterprise knowledge assistant.

Based on the provided context, answer the user's question accurately and concisely.
If the answer cannot be found in the context, say so clearly.
Always cite the source documents.

Context:
{context}

Question: {question}

Answer:"""


class RAGChain:
    """
    Retrieval-Augmented Generation chain with Gemini.
    Combines retrieval, context injection, and LLM for accurate answers.
    """
    
    def __init__(self):
        """Initialize the RAG chain."""
        self.retriever = get_retriever()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=settings.temperature,
            google_api_key=settings.google_api_key,
            convert_system_message_to_human=True
        )
        
        # Build prompt template
        self.prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=PROMPT_TEMPLATE
        )
        
        logger.info("RAG chain initialized with Gemini Flash")
    
    def format_documents(self, docs: List[Document]) -> str:
        """
        Format retrieved documents for context injection.
        
        Args:
            docs: List of retrieved documents
        
        Returns:
            Formatted context string
        """
        formatted = []
        
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            section = doc.metadata.get("section", "")
            page = doc.metadata.get("page_number", "")
            
            header = f"[Document {i}: {source}"
            if section:
                header += f" - {section}"
            if page:
                header += f" (Page {page})"
            header += "]"
            
            formatted.append(f"{header}\n{doc.page_content}\n")
        
        return "\n".join(formatted)
    
    def generate_answer(
        self,
        query: str,
        documents: List[Document],
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Generate answer using LLM with context.
        
        Args:
            query: User query
            documents: Retrieved documents
            metadata: Optional metadata about retrieval
        
        Returns:
            Generated answer
        """
        if not documents:
            return "I don't have any relevant information in the knowledge base to answer this question."
        
        # Format context
        context = self.format_documents(documents)
        
        # Create prompt
        prompt_input = self.prompt.format(
            context=context,
            question=query
        )
        
        try:
            # Generate response
            response = self.llm.invoke(prompt_input)
            answer = response.content
            
            logger.info(f"Generated answer for query: {query[:50]}...")
            return answer
        
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            raise
    
    def query(
        self,
        query: str,
        retrieval_method: str = "mmr",
        top_k: int = 5,
        role: str = "general",
        department: Optional[str] = None
    ) -> Dict:
        """
        Complete RAG pipeline: retrieve and answer.
        
        Args:
            query: User query
            retrieval_method: "similarity", "mmr", or "multi_query"
            top_k: Number of documents to retrieve
            role: User role for access control
            department: Optional department filter
        
        Returns:
            Dict with answer and sources
        """
        try:
            # Step 1: Retrieve documents
            retrieved_docs = self.retriever.retrieve(
                query,
                method=retrieval_method,
                k=top_k,
                role=role,
                department=department
            )
            
            # Step 2: Generate answer
            answer = self.generate_answer(query, retrieved_docs)
            
            # Step 3: Format sources
            sources = []
            for doc in retrieved_docs:
                sources.append({
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": {
                        "source": doc.metadata.get("source", "Unknown"),
                        "section": doc.metadata.get("section", ""),
                        "page": doc.metadata.get("page_number", ""),
                        "department": doc.metadata.get("department", "General")
                    }
                })
            
            return {
                "query": query,
                "answer": answer,
                "sources": sources,
                "retrieval_method": retrieval_method,
                "documents_retrieved": len(retrieved_docs)
            }
        
        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            raise


# Singleton instance
_chain = None


def get_rag_chain() -> RAGChain:
    """Get or create RAG chain instance."""
    global _chain
    if _chain is None:
        _chain = RAGChain()
    return _chain
