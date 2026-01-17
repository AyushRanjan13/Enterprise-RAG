# KnowFlow Architecture Documentation

**Version:** 2.2.0  
**Last Updated:** January 2026

## Overview

KnowFlow is an enterprise-grade Retrieval-Augmented Generation (RAG) system designed to transform internal documents into an intelligent knowledge assistant. This document provides comprehensive technical architecture details for developers and system administrators.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        END USER                                     │
│                   (Employee / Manager)                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP/REST API
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GRADIO FRONTEND                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┬──────────────────┬──────────────────────┐  │
│  │ Ask Questions      │ Upload Documents │ System Info          │  │
│  │ - Query input      │ - File picker    │ - Features list      │  │
│  │ - Role selector    │ - Metadata form  │ - Tech stack         │  │
│  │ - Dept filter      │ - Progress status│ - Statistics         │  │
│  │ - Retrieval method │ - Upload status  │ - Auto-refresh       │  │
│  └────────────────────┴──────────────────┴──────────────────────┘  │
│                                                                     │
│  Features:                                                          │
│  • Modern, professional UI design                                  │
│  • Markdown-formatted answers with sources                         │
│  • Real-time processing feedback                                   │
│  • Backend health checking                                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ REST API (HTTP)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ API ROUTERS                                                  │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ • /api/ingest/document  → Ingest single document            │  │
│  │ • /api/ingest/directory → Batch ingest from folder          │  │
│  │ • /api/ingest/stats     → Get collection statistics         │  │
│  │ • /api/query/ask        → Ask and get answer               │  │
│  │ • /api/query/search     → Search without answering          │  │
│  │ • /api/query/health     → Health check                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ REQUEST VALIDATION (Pydantic)                               │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ • DocumentMetadata → source, department, doc_type           │  │
│  │ • QueryRequest     → query, role, department, retriever_type│  │
│  │ • IngestRequest    → filename, department, access_level     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Python API Calls
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│               LANGCHAIN RAG PIPELINE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LAYER 1: DOCUMENT LOADING                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ MultiFormatLoader                                            │  │
│  │ • PDF Support (pypdf)      → Extract text + page numbers     │  │
│  │ • DOCX Support (python-docx) → Extract paragraphs           │  │
│  │ • TXT Support (native)     → Raw text reading                │  │
│  │ Metadata Enrichment        → source, department, section     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                       │
│  LAYER 2: TEXT SPLITTING                                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ MetadataAwareSplitter                                        │  │
│  │ • RecursiveCharacterTextSplitter                             │  │
│  │ • Chunk size: 1000 characters                                │  │
│  │ • Overlap: 200 characters                                    │  │
│  │ • Separators: [\\n\\n, \\n, ., space]                         │  │
│  │ • Metadata Preservation: chunk_index, total_chunks, source   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                       │
│  LAYER 3: EMBEDDINGS                                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ GeminiEmbeddingsProvider                                     │  │
│  │ • Model: models/embedding-001                               │  │
│  │ • Dimension: 768D vectors                                    │  │
│  │ • Free Tier: Yes (Google API)                                │  │
│  │ • Latency: ~100ms per request                                │  │
│  │ • Method: Batch embedding for documents                      │  │
│  │ • Single embedding for queries                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                       │
│  LAYER 4: VECTOR DATABASE                                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ VectorStoreManager (Chroma)                                  │  │
│  │ • Collection Name: knowflow_documents                        │  │
│  │ • Storage: Local (/data/chroma_db)                           │  │
│  │ • Persistence: Disk-based                                    │  │
│  │ • Metadata: Full-text search support                         │  │
│  │ • Operations: add, delete, search, filter                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                       │
│  LAYER 5: RETRIEVAL                                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ AdvancedRetriever                                            │  │
│  │                                                               │  │
│  │ Strategy 1: Similarity Search                                │  │
│  │   └─ Fast cosine similarity scoring                           │  │
│  │                                                               │  │
│  │ Strategy 2: MMR (Maximum Marginal Relevance)                 │  │
│  │   └─ Balances relevance (0.5) and diversity                  │  │
│  │   └─ Reduces redundancy in results                           │  │
│  │                                                               │  │
│  │ Strategy 3: MultiQuery Retriever                             │  │
│  │   └─ Generates query variations                              │  │
│  │   └─ Improves recall on ambiguous queries                    │  │
│  │                                                               │  │
│  │ Access Control Layer:                                        │  │
│  │   └─ Role-based metadata filtering                           │  │
│  │   └─ Department-specific document access                     │  │
│  │   └─ Admin bypass for all documents                          │  │
│  │                                                               │  │
│  │ Default: k=5, fetch_k=20, lambda=0.5                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                       │
│  LAYER 6: LLM INVOCATION                                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ RAGChain (LangChain)                                         │  │
│  │ • LLM: ChatGoogleGenerativeAI (Gemini 1.5 Flash)            │  │
│  │ • Temperature: 0.7 (Balanced, deterministic)                │  │
│  │ • Max Tokens: 1024 (Concise responses)                       │  │
│  │ • Free Tier: Yes                                             │  │
│  │ • Latency: ~500-1500ms per answer                            │  │
│  │ • Prompt Template: Enterprise-grade instructions             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                       │
│  CONTEXT INJECTION & FORMATTING                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ • Format retrieved documents                                 │  │
│  │ • Inject as context in prompt                                │  │
│  │ • Citation headers: [Document X: source - section]          │  │
│  │ • Metadata preservation: source, page, department            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                             │                                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Output
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      RESPONSE GENERATION                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ QueryResponse (Pydantic Model)                              │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ • answer              → Generated text response              │  │
│  │ • sources             → List of RetrievedDocument objects    │  │
│  │ • query               → Original user query                  │  │
│  │ • retrieval_method    → Method used (mmr/similarity/multi)   │  │
│  │ • model_used          → "gemini-1.5-flash"                   │  │
│  │ • tokens_used         → Optional usage tracking              │  │
│  │ • timestamp           → UTC timestamp                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Features:                                                          │
│  ✓ Answer is context-grounded (from documents)                    │
│  ✓ Source citations with document names                           │
│  ✓ Section references for easy navigation                         │
│  ✓ Role-based filtering applied throughout                        │
│  ✓ Reduced hallucination via prompt engineering                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
USER QUERY
    │
    ├─→ [Gradio] Parse query + metadata
    │
    ├─→ [FastAPI] POST /api/query/ask
    │
    ├─→ [RAGChain.query()]
    │
    ├─→ [Retriever.retrieve()]
    │   ├─→ [RoleFilter] Check user permissions
    │   └─→ [VectorStore] Vector search (MMR/Similarity/MultiQuery)
    │       ├─→ [Embeddings] Convert query to 768D vector
    │       ├─→ [Chroma] Similarity search
    │       ├─→ [MetadataFilter] Apply role-based filtering
    │       └─→ [Results] Top-K documents
    │
    ├─→ [RAGChain.generate_answer()]
    │   ├─→ [Formatter] Format documents for context
    │   ├─→ [PromptTemplate] Inject context
    │   ├─→ [Gemini LLM] Generate response
    │   └─→ [String Parser] Extract text answer
    │
    ├─→ [Response Builder]
    │   ├─→ Answer
    │   ├─→ Sources with metadata
    │   ├─→ Query echo
    │   └─→ Timestamp
    │
    └─→ [Gradio] Display formatted answer + sources in modern UI
```

---

## 📊 Component Interactions

### Document Ingestion Flow

```
File Upload
    │
    ├─→ FileValidator
    │   ├─ Check format (PDF/DOCX/TXT)
    │   ├─ Check size (<25MB)
    │   └─ Check virus (optional)
    │
    ├─→ MultiFormatLoader.load_file()
    │   ├─ Route to format-specific loader
    │   ├─ Extract text
    │   └─ Attach metadata
    │
    ├─→ MetadataAwareSplitter.split_documents()
    │   ├─ Chunk text (1000 chars, 200 overlap)
    │   ├─ Preserve metadata
    │   └─ Add chunk indices
    │
    ├─→ GeminiEmbeddingsProvider.embed_documents()
    │   ├─ Batch embed chunks
    │   └─ Get 768D vectors
    │
    ├─→ VectorStoreManager.add_documents()
    │   ├─ Store vectors in Chroma
    │   ├─ Index metadata
    │   └─ Persist to disk
    │
    └─→ IngestResponse
        ├─ chunks_created
        ├─ document_id
        └─ timestamp
```

---

## 🔐 Security & Access Control

```
User Authentication
    │
    ├─→ Role Definition
    │   ├─ admin     → All documents
    │   ├─ hr        → HR, People, General
    │   ├─ engineer  → Engineering, Tech, General
    │   ├─ finance   → Finance, Budget, General
    │   └─ general   → General, Public only
    │
    ├─→ Query Processing
    │   ├─ Role extracted from request
    │   ├─ Department optionally specified
    │   └─ Metadata filter built
    │
    ├─→ Retrieval
    │   ├─ VectorStore filters by metadata
    │   ├─ Only accessible documents returned
    │   └─ Audit log (optional)
    │
    └─→ Response
        └─ Only role-accessible sources included
```

---

## 📈 Performance Characteristics

| Component | Latency | Throughput | Scalability |
|-----------|---------|-----------|-------------|
| **Embedding** | ~100ms | 100 docs/sec | Depends on API |
| **Vector Search** | ~50ms | 1000 queries/sec | Linear with data size |
| **LLM Generation** | ~800ms | 1 query/user | Rate limited by API |
| **Total E2E** | ~1-2s | 10-20 user concurrent | Local Chroma bottleneck |
| **Database** | ~10ms | Unlimited | Memory bound |

---

## 🚀 Scaling Strategies

### Vertical Scaling (Single Machine)
- Increase RAM for larger vector store
- Use SSD for faster disk I/O
- Multi-GPU for embeddings (if needed)

### Horizontal Scaling (Multiple Machines)
- Replace Chroma with **Pinecone** (distributed)
- Use **Redis** for query caching
- **Load balancer** for FastAPI instances
- **Message queue** for async processing

### Example Pinecone Integration
```python
# In vectorstore.py, add:
def get_vectorstore(db_type):
    if db_type == "chroma":
        return Chroma(...)
    elif db_type == "pinecone":
        return Pinecone.from_documents(
            documents,
            embeddings,
            index_name="knowflow"
        )
```

---

## � Technical Specifications

### Current Tech Stack (v2.2.0)
- **Frontend:** Gradio 6.3.0 (port 7860)
  - Chat history with conversation tracking
  - Batch document upload (multiple files)
  - Mixed file type support (PDF, DOCX, TXT)
  - Professional AI-themed dark UI
  - Export functionality (JSON)
  - Real-time chatbot interface
  - Batch processing report with success/failure summary
- **Backend:** FastAPI 0.128.0 (port 8000)
- **LangChain:** 0.3.13 ecosystem
- **LLM:** Google Gemini 1.5 Flash
- **Embeddings:** Google embedding-001 (768-dim)
- **Vector DB:** ChromaDB 1.4.1
- **Python:** 3.13
- **Total Packages:** 158

### Recent Updates (v2.2.0)
- Added batch upload for multiple documents simultaneously
- Support for mixed file types in single batch
- Batch processing report with detailed success/failure summary
- Improved upload UI with separated single and batch sections
- Chat history with persistent conversation tracking
- Implemented export functionality for chat sessions (JSON format)
- Redesigned UI with professional AI theme (dark mode with gradients)
- Enhanced chatbot component with avatars and better UX
- Migrated from Streamlit → Gradio (professional UI)
- Downgraded LangChain 1.2.6 → 0.3.13 (MultiQueryRetriever support)
- Fixed file extension validation bug in loader.py
- Consolidated .env configuration
- Updated CORS for Gradio port 7860

---

## �🔍 Monitoring Points

### Health Checks
- Backend API availability
- Vector store connectivity
- Gemini API quota status
- Document count in collection

### Performance Metrics
- Query latency (p50, p95, p99)
- Number of documents retrieved
- Answer generation time
- User session duration

### Error Tracking
- Failed document uploads
- Query processing errors
- API rate limiting
- Embedding failures

---

## 📝 API Contracts

### Request/Response Examples

**Ingest Document**
```json
POST /api/ingest/document
Content-Type: multipart/form-data

Request:
{
  "file": <binary>,
  "department": "HR",
  "doc_type": "Policy",
  "access_level": "Employee"
}

Response (200):
{
  "success": true,
  "message": "Successfully ingested hr_policy.pdf",
  "chunks_created": 42,
  "document_id": "HR_hr_policy",
  "timestamp": "2024-01-17T10:30:00"
}
```

**Query Knowledge Base**
```json
POST /api/query/ask
Content-Type: application/json

Request:
{
  "query": "What is the leave policy?",
  "role": "general",
  "department": null,
  "retriever_type": "mmr",
  "top_k": 5
}

Response (200):
{
  "query": "What is the leave policy?",
  "answer": "Employees are entitled to 24 paid leaves...",
  "sources": [
    {
      "content": "Leave Policy: Employees are entitled...",
      "metadata": {
        "source": "hr_policy.pdf",
        "section": "Leave Policy",
        "page_number": 3,
        "department": "HR"
      },
      "relevance_score": 0.95
    }
  ],
  "model_used": "gemini-1.5-flash",
  "timestamp": "2024-01-17T10:35:00"
}
```

---

## 🔄 Extension Points

### Easy to Extend
- **New Document Formats**: Add to `MultiFormatLoader`
- **Different LLMs**: Swap in `RAGChain`
- **Alternative Vector DBs**: Update `VectorStoreManager`
- **Custom Retrieval Logic**: Extend `AdvancedRetriever`
- **Fine-tuned Embeddings**: Replace `GeminiEmbeddingsProvider`

### Hard to Change
- Document metadata schema (breaking)
- Vector embedding dimension (768D → different)
- Core API contracts (query/response format)

---

## 📊 Database Schema

### Chroma Collection Structure
```
Collection: knowflow_documents

Each Document:
{
  "id": "doc_chunk_001",
  "embedding": [768-dimensional vector],
  "document": {
    "page_content": "actual text...",
    "metadata": {
      "source": "hr_policy.pdf",
      "department": "HR",
      "doc_type": "Policy",
      "section": "Leave Policy",
      "page_number": 3,
      "access_level": "Employee",
      "chunk_index": 0,
      "total_chunks": 42
    }
  }
}
```

---

Last Updated: January 17, 2026
