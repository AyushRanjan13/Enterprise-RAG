# KnowFlow API Documentation

**Base URL:** `http://localhost:8000`  
**API Version:** 1.0  
**Authentication:** None (Role-based in query headers)  
**Version:** 2.2.0  
**Last Updated:** January 2026

---

## 📋 Table of Contents

1. [Health & Status](#health--status)
2. [Document Ingestion](#document-ingestion)
3. [Query Endpoints](#query-endpoints)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Examples](#examples)

---

## Health & Status

### Get Health Status

**Endpoint:** `GET /health`

**Description:** Quick health check for the API.

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

---

### Detailed Health Check

**Endpoint:** `GET /api/query/health`

**Description:** Comprehensive health check including vector store status.

**Response:**
```json
{
  "status": "healthy",
  "vectorstore": "connected",
  "stats": {
    "collection_name": "knowflow_documents",
    "document_count": 42
  }
}
```

**Status Codes:**
- `200 OK` - Service is healthy
- `500 Internal Server Error` - Service issues

---

## Document Ingestion

### Upload Single Document

**Endpoint:** `POST /api/ingest/document`

**Content-Type:** `multipart/form-data`

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | PDF, DOCX, or TXT file (max 25MB) |
| `department` | String | No | Department classification (HR, Engineering, Finance, General) |
| `doc_type` | String | No | Document type (Policy, SOP, Manual, Guide, etc.) |
| `access_level` | String | No | Access level (Employee, Manager, Executive) |

**Example Request (cURL):**
```bash
curl -X POST http://localhost:8000/api/ingest/document \
  -F "file=@hr_policy.pdf" \
  -F "department=HR" \
  -F "doc_type=Policy" \
  -F "access_level=Employee"
```

**Example Request (Python):**
```python
import requests

with open('hr_policy.pdf', 'rb') as f:
    files = {'file': f}
    data = {
        'department': 'HR',
        'doc_type': 'Policy',
        'access_level': 'Employee'
    }
    response = requests.post(
        'http://localhost:8000/api/ingest/document',
        files=files,
        data=data
    )
    print(response.json())
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Successfully ingested hr_policy.pdf",
  "chunks_created": 42,
  "document_id": "HR_hr_policy",
  "timestamp": "2024-01-17T10:30:00"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Unsupported file format. Supported: {'.pdf', '.docx', '.txt'}"
}
```

**Response (413 Payload Too Large):**
```json
{
  "detail": "File too large. Max size: 25MB"
}
```

**Status Codes:**
- `200 OK` - Document successfully ingested
- `400 Bad Request` - Invalid file or parameters
- `413 Payload Too Large` - File exceeds size limit
- `500 Internal Server Error` - Processing error

**Note on Batch Uploads:**  
To upload multiple documents, make multiple requests to this endpoint. The frontend automatically handles batch uploads by looping through files and sending individual requests with the same metadata. Each file is processed independently, with success/failure tracking per file.

---

### Ingest Directory

**Endpoint:** `POST /api/ingest/directory`

**Content-Type:** `application/x-www-form-urlencoded`

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `directory_path` | String | Yes | Path to directory containing documents |
| `department` | String | No | Department for all documents |
| `recursive` | Boolean | No | Search subdirectories (default: true) |

**Example Request (cURL):**
```bash
curl -X POST http://localhost:8000/api/ingest/directory \
  -d "directory_path=/path/to/documents" \
  -d "department=HR" \
  -d "recursive=true"
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Ingested 5 files",
  "chunks_created": 234,
  "department": "HR"
}
```

**Status Codes:**
- `200 OK` - Directory processed successfully
- `400 Bad Request` - Invalid path
- `500 Internal Server Error` - Processing error

---

### Get Collection Statistics

**Endpoint:** `GET /api/ingest/stats`

**Description:** Retrieve information about the vector store collection.

**Response:**
```json
{
  "success": true,
  "stats": {
    "collection_name": "knowflow_documents",
    "document_count": 42
  }
}
```

**Status Codes:**
- `200 OK` - Statistics retrieved
- `500 Internal Server Error` - Query failed

---

## Query Endpoints

### Ask Question

**Endpoint:** `POST /api/query/ask`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "query": "What is the leave policy?",
  "role": "general",
  "department": null,
  "retriever_type": "mmr",
  "top_k": 5
}
```

**Parameters:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `query` | String | Yes | 3-500 chars | Natural language question |
| `role` | String | No | admin, hr, engineer, finance, general | User role for access control |
| `department` | String | No | HR, Engineering, Finance, General | Optional department filter |
| `retriever_type` | String | No | similarity, mmr, multi_query | Retrieval strategy (default: mmr) |
| `top_k` | Integer | No | 1-20 | Number of documents (default: 5) |

**Example Request (Python):**
```python
import requests

response = requests.post(
    'http://localhost:8000/api/query/ask',
    json={
        'query': 'How many leaves am I entitled to?',
        'role': 'general',
        'department': 'HR',
        'retriever_type': 'mmr',
        'top_k': 5
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
for source in result['sources']:
    print(f"  - {source['metadata']['source']}")
```

**Response (200 OK):**
```json
{
  "query": "What is the leave policy?",
  "answer": "According to the company leave policy, employees are entitled to 24 paid leave days per year. This includes regular weekday leave (Monday-Friday) and long weekends if aligned with public holidays. New employees receive 15 days after completing 6 months with the company.",
  "sources": [
    {
      "content": "ANNUAL LEAVE - Full-time employees are entitled to 24 paid leave days per year. This includes...",
      "metadata": {
        "source": "hr_policy.pdf",
        "section": "Leave Policy",
        "page_number": 3,
        "department": "HR"
      },
      "relevance_score": 0.98
    },
    {
      "content": "New employees receive 15 days after completing 6 months with the company...",
      "metadata": {
        "source": "hr_policy.pdf",
        "section": "Leave Policy",
        "page_number": 3,
        "department": "HR"
      },
      "relevance_score": 0.87
    }
  ],
  "model_used": "gemini-1.5-flash",
  "tokens_used": null,
  "timestamp": "2024-01-17T10:35:00"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Query must be at least 3 characters"
}
```

**Response (500 Internal Server Error):**
```json
{
  "detail": "Query failed: [error details]"
}
```

**Status Codes:**
- `200 OK` - Answer generated successfully
- `400 Bad Request` - Invalid query or parameters
- `500 Internal Server Error` - Processing error

---

### Search Documents (No Generation)

**Endpoint:** `POST /api/query/search`

**Content-Type:** `application/json`

**Description:** Retrieve relevant documents without generating an answer.

**Request Body:** Same as `/api/query/ask`

**Example Request (cURL):**
```bash
curl -X POST http://localhost:8000/api/query/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "leave policy",
    "role": "general",
    "top_k": 5
  }'
```

**Response (200 OK):**
```json
{
  "query": "leave policy",
  "documents": [
    {
      "content": "ANNUAL LEAVE - Full-time employees are entitled to 24 paid leave days per year...",
      "metadata": {
        "source": "hr_policy.pdf",
        "department": "HR",
        "section": "Leave Policy",
        "page": 3
      }
    },
    {
      "content": "SICK LEAVE - All employees have 10 paid sick leave days per year...",
      "metadata": {
        "source": "hr_policy.pdf",
        "department": "HR",
        "section": "Leave Policy",
        "page": 3
      }
    }
  ],
  "count": 2
}
```

**Status Codes:**
- `200 OK` - Documents retrieved
- `400 Bad Request` - Invalid parameters
- `500 Internal Server Error` - Search failed

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

### Common Error Codes

| Code | Message | Reason |
|------|---------|--------|
| 400 | Bad Request | Invalid parameters, missing required fields, malformed query |
| 413 | Payload Too Large | File exceeds 25MB limit |
| 500 | Internal Server Error | Server error, API key missing, database connection failed |

### Error Examples

**Missing API Key:**
```json
{
  "detail": "GOOGLE_API_KEY not found. Set it as environment variable."
}
```

**Invalid Role:**
```json
{
  "detail": "Invalid role: invalid_role. Allowed: [admin, hr, engineer, finance, general]"
}
```

**No Documents Found:**
```json
{
  "detail": "I don't have any relevant information in the knowledge base to answer this question."
}
```

---

## Rate Limiting

### Current Implementation
- **Backend:** No rate limiting (production should add)
- **Gemini API:** Subject to Google's free tier limits

### Recommended Rate Limits (Production)

```
Per User:
- Documents upload: 10 per day
- Queries: 100 per day
- Max concurrent: 5

Per IP:
- API calls: 1000 per hour
- Maximum burst: 10 requests/sec
```

---

## Response Time Guarantees

| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| Document upload (1MB) | 2s | 5s | 10s |
| Query answer | 1.5s | 2.5s | 4s |
| Similarity search | 50ms | 100ms | 200ms |
| Vector store stats | 10ms | 20ms | 50ms |

---

## Authentication (Future)

```
TODO: Add Bearer token authentication

Header:
Authorization: Bearer <token>

Endpoint:
POST /auth/login
POST /auth/refresh
POST /auth/logout
```

---

## Examples

### Complete Workflow: Upload & Query

**Step 1: Upload Document**
```bash
curl -X POST http://localhost:8000/api/ingest/document \
  -F "file=@company_policies.pdf" \
  -F "department=HR"
```

Response:
```json
{
  "success": true,
  "chunks_created": 42,
  "document_id": "HR_company_policies"
}
```

**Step 2: Check Collection**
```bash
curl http://localhost:8000/api/ingest/stats
```

Response:
```json
{
  "success": true,
  "stats": {
    "document_count": 42
  }
}
```

**Step 3: Ask Question**
```bash
curl -X POST http://localhost:8000/api/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the maternity leave policy?",
    "role": "general",
    "top_k": 3
  }'
```

Response:
```json
{
  "query": "What is the maternity leave policy?",
  "answer": "The company provides 6 months paid maternity leave for birth mothers...",
  "sources": [
    {
      "content": "Maternity Leave: 6 months paid maternity leave...",
      "metadata": {
        "source": "company_policies.pdf",
        "section": "Special Leave"
      }
    }
  ],
  "model_used": "gemini-1.5-flash",
  "timestamp": "2024-01-17T10:40:00"
}
```

---

### Multi-Format Document Ingestion

**Batch Upload Multiple Formats:**
```python
import requests
from pathlib import Path

documents = [
    ("policy.pdf", "HR", "Policy"),
    ("procedure.docx", "Engineering", "SOP"),
    ("guide.txt", "General", "Guide")
]

for filename, department, doc_type in documents:
    with open(filename, 'rb') as f:
        files = {'file': f}
        data = {'department': department, 'doc_type': doc_type}
        response = requests.post(
            'http://localhost:8000/api/ingest/document',
            files=files,
            data=data
        )
        print(f"{filename}: {response.json()['message']}")
```

---

### Role-Based Access Control Example

**HR User (can access HR docs):**
```bash
curl -X POST http://localhost:8000/api/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "salary structure",
    "role": "hr"
  }'
```
→ Returns HR-accessible documents

**Engineer User (can't access HR docs):**
```bash
curl -X POST http://localhost:8000/api/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "salary structure",
    "role": "engineer"
  }'
```
→ No HR documents in response

---

### Retriever Strategy Comparison

**Similarity (Fast but basic):**
```bash
curl -X POST http://localhost:8000/api/query/ask \
  -d '{"query": "leaves", "retriever_type": "similarity"}'
# Speed: ~1s | Relevance: Basic
```

**MMR (Balanced - Recommended):**
```bash
curl -X POST http://localhost:8000/api/query/ask \
  -d '{"query": "leaves", "retriever_type": "mmr"}'
# Speed: ~1.5s | Relevance: High | Diversity: Balanced
```

**MultiQuery (Best recall but slower):**
```bash
curl -X POST http://localhost:8000/api/query/ask \
  -d '{"query": "leaves", "retriever_type": "multi_query"}'
# Speed: ~2s | Relevance: High | Diversity: Good
```

---

## Changelog

### v2.1.0 (January 17, 2026) - Chat History & UI Enhancement
**New Features:**
- Chat history tracking with conversation context
- Export chat history as JSON with full metadata
- Professional AI-themed dark UI with gradients
- Chatbot interface with user/AI avatars
- Real-time conversation management
- Clear chat and restart functionality

**UI Improvements:**
- Modern dark theme (blue-purple gradients)
- Improved visual hierarchy
- Better mobile responsiveness
- Enhanced chat experience

---

### v2.0.0 (January 17, 2026) - Major UI & Framework Update
**Breaking Changes:**
- Replaced Streamlit with Gradio 6.3 (port changed 8501 → 7860)
- Migrated LangChain 1.2.6 → 0.3.13 (MultiQueryRetriever now available)

**New Features:**
- Professional Gradio UI with modern design
- Real-time backend health checking
- Auto-refreshing statistics (30s interval)
- Enhanced upload feedback with chunk count and processing time
- Markdown-formatted responses with source citations

**Bug Fixes:**
- Fixed file extension validation in document loader
- Updated CORS configuration for Gradio
- Resolved Google API dependency conflicts

**Configuration:**
- Consolidated .env files (removed .env.example)
- Added quotes around GOOGLE_API_KEY
- Updated CORS origins for port 7860

**Removed:**
- frontend/app.py (Streamlit, 552 lines)
- Dockerfile and docker-compose.yml (outdated)

---

### v1.0.0 (Initial Release)
- PDF, DOCX, TXT document support
- MMR, Similarity, MultiQuery retrievers
- Gemini 1.5 Flash LLM integration
- ChromaDB vector database
- Role-based access control
- FastAPI backend with REST API

---

## Support

- **Issues:** Check FastAPI logs at `http://localhost:8000/docs`
- **Documentation:** See [README.md](../README.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
- **Questions:** Review [QUICKSTART.md](../QUICKSTART.md)

---

Last Updated: January 17, 2026
