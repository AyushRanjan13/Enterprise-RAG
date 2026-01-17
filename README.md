# 🧠 KnowFlow - Enterprise Knowledge Assistant

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-green)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.13-purple)](https://langchain.com/)
[![Gradio](https://img.shields.io/badge/Gradio-6.3-orange)](https://gradio.app/)

**KnowFlow** is an enterprise-grade Retrieval-Augmented Generation (RAG) system that transforms internal documents into an intelligent knowledge assistant. Employees can query company policies, SOPs, manuals, and guides using natural language and receive accurate, context-grounded, hallucination-free responses.

## 🎯 Problem Statement

**The Challenge:**
- Employees spend hours searching through scattered documents
- Knowledge silos prevent information sharing across departments
- Repeated queries on the same topics waste productivity
- Risk of inconsistent information due to manual document updates

**KnowFlow's Solution:**
- **Single Source of Truth:** Centralized knowledge management system
- **Natural Language Interface:** Ask questions in plain English
- **Accurate Answers:** Grounded in actual documents, not hallucinations
- **Role-Based Access:** Department-specific document retrieval
- **Instant Responses:** No waiting for human responses

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Gradio Frontend                          │
│    (Modern UI, Chat Interface, Document Upload, Stats)      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST
┌─────────────────────▼───────────────────────────────────────┐
│                   FastAPI Backend                           │
├─────────────────────────────────────────────────────────────┤
│  API Endpoints:                                             │
│  • POST /api/ingest/document    (Upload & ingest documents) │
│  • POST /api/query/ask          (Query knowledge base)      │
│  • GET  /api/ingest/stats       (Collection statistics)     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│            LangChain RAG Pipeline                           │
├─────────────────────────────────────────────────────────────┤
│  1. Document Loader (PDF, DOCX, TXT)                       │
│  2. Text Splitter (RecursiveCharacterTextSplitter)         │
│  3. Embeddings (Google Generative AI - 768-dim)            │
│  4. Vector Store (Chroma - Local Persistence)              │
│  5. Retriever (MMR/Similarity/MultiQuery) - LangChain 0.3  │
│  6. LLM Chain (Gemini 1.5 Flash - Free Tier)              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│         Gemini LLM (Answer Generation)                      │
│    • Temperature: 0.7 (Balanced, deterministic)             │
│    • Max Tokens: 1024 (Concise responses)                   │
│    • Free Tier: Perfect for MVP/Demo                        │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 1️⃣ Multi-Format Document Ingestion
- **Supported Formats:** PDF, DOCX, TXT
- **Single File Upload:** Upload one document with specific metadata
- **Batch Upload:** Upload multiple documents simultaneously with shared metadata
- **Metadata Enrichment:** Department, doc type, access level, source
- **Maximum File Size:** 25MB per document
- **Batch Processing:** Automatic chunking and embedding for all files

### 2️⃣ Advanced Text Chunking
- **Recursive Splitting:** Preserves natural boundaries (paragraphs → sentences)
- **Metadata Preservation:** Chunk index, section, page numbers
- **Configurable:** Chunk size (1000) and overlap (200)

### 3️⃣ Smart Retrieval
- **Similarity Search:** Fast, basic relevance matching
- **MMR (Maximum Marginal Relevance):** Balances relevance and diversity
- **MultiQuery:** Generates query variations to improve recall
- **Metadata Filtering:** Role-based and department-specific access control

### 4️⃣ Enterprise-Grade RAG
- **Google Generative AI Embeddings:** 768-dimensional vectors
- **Chroma Vector Store:** Local, persistent storage
- **Context Injection:** Automatically formats retrieved documents
- **Source Citation:** Answers include source documents with sections

### 5️⃣ Role-Based Access Control
```python
Roles:
  • admin     → Access to all documents
  • hr        → HR, People, General documents
  • engineer  → Engineering, Tech, General documents
  • finance   → Finance, Budget, General documents
  • general   → General, Public documents only
```

### 6️⃣ Chat History & Conversation Management
- **Persistent Conversations:** All chats saved with full context
- **Context Continuity:** Natural follow-up questions in same session
- **Export & Archive:** Download chat history as JSON with metadata
- **Metadata Tracking:** Timestamps, sources, query response times
- **Session Management:** Clear chat and restart conversations easily

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.13+** (tested with 3.13)
- **Google API Key** (free at: https://makersuite.google.com/app/apikey)
- **4GB RAM minimum**
- **Virtual Environment** (recommended)

### Installation

1. **Clone or create project directory:**
   ```bash
   cd GenAI_RAG/KnowFlow
   ```

2. **Create virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   # Edit .env file and add your GOOGLE_API_KEY
   # File already exists with all configuration variables
   ```

### Running the Application

**Terminal 1: Start Backend**
```bash
cd KnowFlow
venv\Scripts\activate  # Windows
python backend/app/main.py
```
API docs available at: http://localhost:8000/docs

**Terminal 2: Start Frontend**
```bash
cd KnowFlow
venv\Scripts\activate  # Windows
python frontend/gradio_app.py
```
Modern UI available at: http://localhost:7860

---

## 🎨 User Interface

KnowFlow features a modern, professional Gradio-based interface with AI-themed dark UI design. The application is organized into three main tabs for optimal user experience.

### AI Assistant Tab
The main chat interface with advanced retrieval settings and real-time conversation management.

![KnowFlow AI Assistant](KnowFlow/images/S1.png)

**Features Visible:**
- Conversation panel with full chat history
- Real-time message streaming
- Settings panel with role selection (General, Admin, HR, Engineer, Finance)
- Retrieval method selector (Multi-Query, MMR, Similarity)
- Source count configuration (1-10 documents)
- Clear Chat and Export History buttons
- Tips for optimal query results

**Capabilities:**
- Natural language queries with context awareness
- Multi-turn conversations with memory
- Source citation with document references
- Export conversations as JSON with metadata

### Upload Documents Tab
Professional document ingestion interface supporting both single and batch file uploads with intelligent metadata enrichment.

![KnowFlow Upload Interface](KnowFlow/images/S2.png)

**Features Visible:**
- Drag-and-drop file upload area (or click to browse)
- Department selector (General, HR, Engineering, Finance, Legal, Operations)
- Document Type selector (Policy, SOP, Manual, Guide, Report, Training, Other)
- Access Level selector (Public, Employee, Manager, Executive, Restricted)
- Single file upload button
- Batch upload section for multiple files
- Real-time processing status with chunk count

**Capabilities:**
- Multi-format support (PDF, DOCX, TXT)
- Automatic text chunking and embedding
- Metadata-aware document processing
- Batch processing with individual status tracking
- File size validation (max 25MB)
- Error handling with descriptive messages

### System Statistics & About Tab
Real-time dashboard displaying knowledge base metrics and system information.

![KnowFlow Statistics](KnowFlow/images/S3.png)

**Displays:**
- Total documents in knowledge base
- Total chunks created and indexed
- Vector storage usage in MB
- System health status
- Technology stack information
- Feature highlights
- Links to API documentation

**Information Provided:**
- Document count and chunk statistics
- Storage efficiency metrics
- Technology used (LangChain, Gemini, ChromaDB, Gradio)
- Links to full API reference
- Architecture documentation

---

### Setting Up UI Images

To display the UI screenshots in this README on GitHub and other platforms, follow these steps:

#### Step 1: Capture Screenshots
1. **Start the application:**
   ```bash
   # Terminal 1: Backend
   python backend/app/main.py
   
   # Terminal 2: Frontend
   python frontend/gradio_app.py
   ```

2. **Open in browser:** Navigate to `http://localhost:7860`

#### Step 2: Save Files to Assets Folder
Save screenshots in the `assets/` directory with these exact names:
- `ui-assistant.png` - AI Assistant tab screenshot
- `ui-upload.png` - Upload Documents tab screenshot
- `ui-stats.png` - Statistics/About tab screenshot

#### Step 3: Optimize Images (Optional)
Keep image sizes reasonable for faster loading:

**Using ImageMagick:**
```bash
# Resize to standard width, maintain aspect ratio
convert input.png -resize 1200x800 -quality 85 assets/ui-assistant.png
```

**Image Specifications:**
- **Format:** PNG (lossless)
- **Resolution:** 1200×800 pixels for tabs, 1200×600 for stats
- **Quality:** 85-90% (good balance of quality and file size)
- **File Size:** Aim for under 500KB per image
- **Color Profile:** sRGB

```

---

## 📖 Usage Guide

### 1. Start a Conversation (AI Assistant Tab)
1. Open the **"💬 AI Assistant"** tab
2. Type your question in the chat input
3. Configure settings in right panel:
   - Select your role (General, Admin, HR, etc.)
   - Choose department filter (optional)
   - Select retrieval method (Multi-Query recommended)
   - Adjust number of sources (1-10)
4. Click **"Send"** or press Enter
5. View AI response with source citations in chat
6. Continue conversation naturally - history is maintained

### 2. Manage Chat History
- **Clear Chat:** Click "🗑️ Clear Chat" to start fresh
- **Export History:** Click "💾 Export History" to download JSON file
- **View Metadata:** See query time and sources used below chat

### 3. Upload Documents

#### Single File Upload
1. Navigate to **"📤 Upload Documents"** tab
2. Select one document (PDF, DOCX, or TXT)
3. Configure metadata:
   - **Department:** HR, Engineering, Finance, General, etc.
   - **Document Type:** Policy, SOP, Manual, Guide, etc.
   - **Access Level:** Public, Employee, Manager, Executive, Restricted
4. Click **"⬆️ Upload"** and view processing status

#### Batch Upload (Multiple Files)
1. In **"📚 Batch Upload"** section, select multiple files
2. Ctrl+Click (Windows/Linux) or Cmd+Click (Mac) for multiple selection
3. Supports mixing file types (PDF, DOCX, TXT together)
4. Configure shared metadata for all files (applies to entire batch)
5. Click **"⬆️ Upload All Files"**
6. View batch report:
   - Files processed and success/failure count
   - Total chunks created across all files
   - Individual status for each file (✅/❌)
   - Processing time for batch

### 4. Example Queries
```
"What is our leave policy?"
"How do I submit expenses for reimbursement?"
"What are the code standards we follow?"
"Who handles HR inquiries?"
"What's our remote work policy?"
```

### 5. Chat History Features
- **Conversation Context:** Ask follow-up questions naturally
- **Export:** Download full conversation history with metadata
- **Review:** Scroll through past Q&A in the chat interface
- **Analytics:** Each export includes timestamps, sources, and query times

---

## 🛠️ Advanced Configuration

### Document Processing
```python
# In backend/app/config.py
chunk_size: int = 1000          # Size of each text chunk
chunk_overlap: int = 200         # Overlap between chunks
supported_file_types: list = ["pdf", "docx", "txt"]
max_file_size_mb: int = 25
```

### Retrieval Strategy
```python
# Similarity vs MMR vs MultiQuery
retriever_type: str = "mmr"     # Recommended for balanced results
retriever_k: int = 5             # Number of documents to retrieve
```

### LLM Configuration
```python
gemini_model: str = "gemini-1.5-flash"  # Free tier
temperature: float = 0.7                 # 0=deterministic, 1=creative
max_tokens: int = 1024                  # Max response length
```

---

## 📊 Project Structure

```
KnowFlow/
├── backend/                          # FastAPI Application
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── config.py                # Configuration management
│   │   ├── schemas.py               # Pydantic models
│   │   ├── api/
│   │   │   ├── ingest.py            # Document ingestion endpoints
│   │   │   └── query.py             # Query endpoints
│   │   └── rag/
│   │       ├── loader.py            # Multi-format document loader
│   │       ├── splitter.py          # Text chunking with metadata
│   │       ├── embeddings.py        # Google Generative AI embeddings
│   │       ├── vectorstore.py       # Chroma vector store manager
│   │       ├── retriever.py         # Advanced retrieval strategies
│   │       └── chain.py             # RAG pipeline with Gemini
│   └── requirements.txt
│
├── frontend/                         # Gradio UI
│   └── gradio_app.py                # Modern Gradio interface
│
├── data/                            # Data directory (created at runtime)
│   └── chroma_db/                   # Vector store persistence
│
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md              # System architecture (452 lines)
│   └── API.md                       # API documentation (624 lines)
│
├── README.md                        # This file (577 lines)
├── requirements.txt                 # All dependencies (158 packages)
├── .env                             # Environment configuration
└── .gitignore
```

---

## 🔌 API Reference


### Upload Document
```bash
POST /api/ingest/document
Content-Type: multipart/form-data

Parameters:
  - file: Document file
  - department: HR, Engineering, Finance, General
  - doc_type: Policy, SOP, Manual, etc.
  - access_level: Employee, Manager, Executive
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully ingested document.pdf",
  "chunks_created": 42,
  "document_id": "HR_document",
  "timestamp": "2024-01-17T10:30:00"
}
```

### Ask Question
```bash
POST /api/query/ask
Content-Type: application/json

{
  "query": "What is the leave policy?",
  "role": "general",
  "department": "HR",
  "retriever_type": "mmr",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "What is the leave policy?",
  "answer": "Employees are entitled to 24 paid leaves...",
  "sources": [
    {
      "content": "Leave Policy: Employees...",
      "metadata": {
        "source": "hr_policy.pdf",
        "section": "Leave Policy",
        "page_number": 3,
        "department": "HR"
      }
    }
  ],
  "model_used": "gemini-1.5-flash",
  "timestamp": "2024-01-17T10:35:00"
}
```

---

## 🚀 Deployment

### Option 1: Cloud Deployment (Recommended)

**Backend (FastAPI):**
- **Render.com:** Free tier available
- **Railway:** $5/month free tier
- **Google Cloud Run:** Pay-as-you-go

**Frontend (Gradio):**
- **HuggingFace Spaces:** Free hosting for Gradio apps
- **Gradio Share:** Temporary public links
- Same server as backend

### Option 2: Docker Deployment

```dockerfile
# Dockerfile for backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t knowflow-backend .
docker run -e GOOGLE_API_KEY=your_key -p 8000:8000 knowflow-backend
```

---

## 📈 Performance & Scalability

| Metric | Value | Notes |
|--------|-------|-------|
| **Chunk Processing** | ~50 chunks/sec | Depends on document size |
| **Embedding Time** | ~100ms per query | Gemini API latency |
| **Retrieval Time** | ~50ms | Chroma local search |
| **Answer Generation** | ~500-1500ms | Gemini LLM response |
| **Total Query Latency** | ~1-2 seconds | End-to-end |
| **Max Concurrent Users** | 5-10 | Local Chroma limitation |

---

## 🔐 Security Best Practices

### 1. API Security
- ✅ CORS configured for trusted origins only
- ✅ Input validation on all endpoints (Pydantic schemas)
- ✅ File type and size restrictions (PDF/DOCX/TXT, max 25MB)
- ✅ Error messages don't leak sensitive info
- ✅ Backend health checks before frontend operations

### 2. Data Privacy
- ✅ Role-based document access control (admin/hr/engineer/finance/general)
- ✅ Metadata filtering prevents unauthorized access
- ✅ No data sent to external APIs except Google Gemini
- ✅ Local vector store (ChromaDB, no cloud sync by default)
- ✅ Department-based document filtering

### 3. API Keys
- ✅ Environment variables via .env file
- ✅ Never commit `.env` to git (.gitignore configured)
- ✅ Rotate keys regularly
- ✅ Use separate keys for dev/prod

---

## 🎓 Learning Resources

### RAG Concepts
- [LangChain 0.3 Documentation](https://python.langchain.com/)
- [Vector Databases Explained](https://www.pinecone.io/learn/vector-database/)
- [Prompt Engineering Guide](https://github.com/dair-ai/Prompt-Engineering-Guide)
- [MultiQueryRetriever Guide](https://python.langchain.com/docs/how_to/MultiQueryRetriever/)

### Technologies Used
- [Gemini API Docs](https://ai.google.dev/docs)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Gradio Documentation](https://gradio.app/docs/)
- [LangChain 0.3 Docs](https://python.langchain.com/)
- [Chroma Documentation](https://docs.trychroma.com/)

---

Built with LangChain 0.3 • FastAPI • Gradio • ChromaDB • Google Gemini
