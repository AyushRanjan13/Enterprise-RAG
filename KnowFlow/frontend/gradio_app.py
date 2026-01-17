"""
KnowFlow RAG System - Professional AI-Powered Interface
Enterprise Knowledge Assistant with Chat History
"""

import gradio as gr
import requests
from pathlib import Path
import json
from datetime import datetime

# Backend API configuration
API_URL = "http://localhost:8000"

# Chat history storage
chat_history_storage = []

# Custom CSS for professional AI-themed look
custom_css = """
.gradio-container {
    font-family: 'Inter', sans-serif !important;
}
"""

def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.json()["status"] == "healthy"
    except:
        return False

def upload_document(file, department, doc_type, access_level):
    """Upload single document to backend"""
    if file is None:
        return "❌ Please select a file to upload", None
    
    try:
        files = {"file": (Path(file.name).name, open(file.name, "rb"))}
        data = {"department": department, "doc_type": doc_type, "access_level": access_level}
        response = requests.post(f"{API_URL}/api/ingest/document", files=files, data=data, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            stats = get_stats()
            return (
                f"✅ Upload Successful!\n\n"
                f"📄 File: {result['filename']}\n"
                f"📊 Chunks: {result['chunks_created']}\n"
                f"⏱️ Time: {result['processing_time_seconds']:.2f}s",
                stats
            )
        else:
            return f"❌ Upload Failed: {response.json().get('detail', 'Unknown error')}", None
    except Exception as e:
        return f"❌ Error: {str(e)}", None

def upload_batch_documents(files, department, doc_type, access_level):
    """Upload multiple documents in batch"""
    if not files:
        return "❌ Please select at least one file to upload", None
    
    results = []
    total_chunks = 0
    total_time = 0
    failed = 0
    
    for file in files:
        try:
            file_obj = open(file, "rb")
            files_dict = {"file": (Path(file).name, file_obj)}
            data = {"department": department, "doc_type": doc_type, "access_level": access_level}
            
            response = requests.post(f"{API_URL}/api/ingest/document", files=files_dict, data=data, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                total_chunks += result['chunks_created']
                total_time += result['processing_time_seconds']
                results.append(
                    f"✅ {Path(file).name}: {result['chunks_created']} chunks"
                )
            else:
                failed += 1
                error = response.json().get('detail', 'Unknown error')
                results.append(f"❌ {Path(file).name}: {error}")
            
            file_obj.close()
        except Exception as e:
            failed += 1
            results.append(f"❌ {Path(file).name}: {str(e)}")
    
    # Create summary
    summary = f"\n## 📊 Batch Upload Summary\n"
    summary += f"**Files Processed:** {len(files)}\n"
    summary += f"**Successful:** {len(files) - failed}\n"
    summary += f"**Failed:** {failed}\n"
    summary += f"**Total Chunks:** {total_chunks}\n"
    summary += f"**Total Time:** {total_time:.2f}s\n\n"
    summary += f"## 📝 Details\n"
    summary += "\n".join(results)
    
    stats = get_stats()
    return summary, stats

def query_documents(question, role, department, retrieval_method, top_k, history):
    """Query the knowledge base with chat history support"""
    if not question.strip():
        return history, "", ""
    
    try:
        data = {
            "question": question,
            "role": role,
            "department": department if department != "All" else None,
            "retrieval_method": retrieval_method.lower(),
            "top_k": top_k
        }
        
        response = requests.post(f"{API_URL}/api/query/ask", json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            answer = f"{result['answer']}\n\n"
            
            if result.get("sources"):
                answer += "**📚 Sources:**\n"
                for i, source in enumerate(result["sources"], 1):
                    answer += f"{i}. {source['filename']} (Page {source.get('page', 'N/A')})\n"
            
            history = history or []
            history.append((question, answer))
            
            chat_history_storage.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "question": question,
                "answer": result['answer'],
                "sources": result.get("sources", []),
                "role": role
            })
            
            metadata = f"⏱️ {result.get('query_time_seconds', 0):.2f}s | 📊 {result.get('sources_count', 0)} sources | 🔍 {retrieval_method}"
            return history, "", metadata
        else:
            history.append((question, f"❌ Error: {response.json().get('detail', 'Unknown error')}"))
            return history, "", ""
    except Exception as e:
        history.append((question, f"❌ Error: {str(e)}"))
        return history, "", ""

def clear_chat():
    """Clear chat history"""
    return [], ""

def export_chat_history():
    """Export chat history as JSON"""
    if not chat_history_storage:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_history_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(chat_history_storage, f, indent=2, ensure_ascii=False)
    return filename

def get_stats():
    """Get system statistics"""
    try:
        response = requests.get(f"{API_URL}/api/ingest/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            return f"📁 Documents: {stats.get('total_documents', 0)} | 📝 Chunks: {stats.get('total_chunks', 0)} | 💾 Storage: {stats.get('storage_size_mb', 0):.2f} MB"
        return "Stats unavailable"
    except:
        return "Backend not connected"

# Create Gradio interface
with gr.Blocks(title="KnowFlow - AI Knowledge Assistant", css=custom_css, theme=gr.themes.Soft()) as demo:
    
    gr.Markdown("# 🤖 KnowFlow\n### AI-Powered Enterprise Knowledge Assistant\n*Advanced RAG System with Multi-Query Retrieval & Chat History*")
    
    status_text = gr.Markdown(get_stats())
    
    with gr.Tabs():
        # Chat Interface Tab
        with gr.Tab("💬 AI Assistant"):
            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(label="Conversation", height=500, avatar_images=(None, "🤖"))
                    
                    with gr.Row():
                        question_input = gr.Textbox(label="Ask a question", placeholder="Type your question here...", lines=2, scale=4)
                        query_btn = gr.Button("Send", variant="primary", scale=1, size="lg")
                    
                    query_metadata = gr.Textbox(label="Query Info", interactive=False, show_label=False)
                    
                    with gr.Row():
                        clear_btn = gr.Button("🗑️ Clear Chat", size="sm")
                        export_btn = gr.Button("💾 Export History", size="sm")
                        export_file = gr.File(label="Downloaded File", visible=False)
                
                with gr.Column(scale=1):
                    gr.Markdown("### ⚙️ Settings")
                    role_dropdown = gr.Dropdown(choices=["General", "Admin", "HR", "Engineer", "Finance", "Manager"], value="General", label="Your Role")
                    dept_dropdown = gr.Dropdown(choices=["All", "General", "HR", "Engineering", "Finance", "Legal", "Operations"], value="All", label="Department")
                    method_radio = gr.Radio(choices=["Similarity", "MMR", "Multi-Query"], value="Multi-Query", label="Retrieval Method")
                    top_k_slider = gr.Slider(minimum=1, maximum=10, value=5, step=1, label="Sources")
                    gr.Markdown("---\n**💡 Tips:**\n- Multi-Query: Best for complex questions\n- MMR: Balanced results\n- Similarity: Fastest")
            
            query_btn.click(fn=query_documents, inputs=[question_input, role_dropdown, dept_dropdown, method_radio, top_k_slider, chatbot], outputs=[chatbot, question_input, query_metadata])
            question_input.submit(fn=query_documents, inputs=[question_input, role_dropdown, dept_dropdown, method_radio, top_k_slider, chatbot], outputs=[chatbot, question_input, query_metadata])
            clear_btn.click(fn=clear_chat, outputs=[chatbot, query_metadata])
            export_btn.click(fn=export_chat_history, outputs=export_file)
        
        # Upload Tab
        with gr.Tab("📤 Upload Documents"):
            gr.Markdown("### 📁 Single File Upload")
            with gr.Row():
                with gr.Column(scale=2):
                    file_input = gr.File(label="Select Document", file_types=[".pdf", ".docx", ".txt"])
                    with gr.Row():
                        dept_input = gr.Dropdown(choices=["General", "HR", "Engineering", "Finance", "Legal", "Operations"], value="General", label="Department")
                        type_input = gr.Dropdown(choices=["Policy", "SOP", "Manual", "Guide", "Report", "Training", "Other"], value="Policy", label="Document Type")
                    access_input = gr.Dropdown(choices=["Public", "Employee", "Manager", "Executive", "Restricted"], value="Employee", label="Access Level")
                    upload_btn = gr.Button("⬆️ Upload", variant="primary", size="lg")
                
                with gr.Column(scale=3):
                    upload_output = gr.Markdown(label="Upload Status")
            
            upload_btn.click(fn=upload_document, inputs=[file_input, dept_input, type_input, access_input], outputs=[upload_output, status_text])
            
            gr.Markdown("---\n### 📚 Batch Upload (Multiple Files)\n**Upload multiple documents at once with the same metadata**")
            
            with gr.Row():
                with gr.Column(scale=2):
                    batch_files = gr.File(label="Select Multiple Files", file_count="multiple", file_types=[".pdf", ".docx", ".txt"])
                    with gr.Row():
                        batch_dept = gr.Dropdown(choices=["General", "HR", "Engineering", "Finance", "Legal", "Operations"], value="General", label="Department (All Files)")
                        batch_type = gr.Dropdown(choices=["Policy", "SOP", "Manual", "Guide", "Report", "Training", "Other"], value="Policy", label="Document Type (All Files)")
                    batch_access = gr.Dropdown(choices=["Public", "Employee", "Manager", "Executive", "Restricted"], value="Employee", label="Access Level (All Files)")
                    batch_upload_btn = gr.Button("⬆️ Upload All Files", variant="primary", size="lg")
                
                with gr.Column(scale=3):
                    batch_upload_output = gr.Markdown(label="Batch Upload Status")
            
            batch_upload_btn.click(fn=upload_batch_documents, inputs=[batch_files, batch_dept, batch_type, batch_access], outputs=[batch_upload_output, status_text])
        
        # System Info Tab
        with gr.Tab("ℹ️ About"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("""
## 🎯 Features

### Document Processing
- 📄 Multi-format support (PDF, DOCX, TXT)
- 🎯 Smart chunking with context preservation
- ⚡ Fast embedding generation
- 💾 Persistent vector storage

### AI Capabilities
- 🤖 Google Gemini 1.5 Flash LLM
- 🔍 3 Retrieval strategies (Similarity, MMR, Multi-Query)
- 🎓 Context-aware responses
- 📚 Source citation and verification

### Access & Security
- 🔐 Role-based access control
- 🏢 Department-level filtering
- 🛡️ Secure API communication
- 📊 Query analytics
                    """)
                
                with gr.Column():
                    gr.Markdown("""
## 🔬 Tech Stack

**Backend**
- FastAPI (Python web framework)
- LangChain 0.3.13 (RAG framework)
- ChromaDB (Vector database)
- Google Gemini API (LLM)

**Frontend**
- Gradio 6.3 (AI interface)
- Modern responsive design
- Real-time chat interface
- Chat history export

**Retrieval Methods**
- **Similarity:** Fast semantic search
- **MMR:** Balanced diversity & relevance
- **Multi-Query:** Query expansion for better recall

---

**Version:** 2.1.0  
**Updated:** January 2026
                    """)
            
            refresh_btn = gr.Button("🔄 Refresh Stats", size="sm")
            refresh_btn.click(fn=get_stats, outputs=status_text)
    
    gr.Markdown("---\n<center>🤖 **Powered by AI** | Built with LangChain, Gemini & Gradio | Enterprise Knowledge Management</center>")

# Launch the app
if __name__ == "__main__":
    if check_backend_health():
        print("✅ Backend is healthy - Starting Gradio UI...")
        demo.launch(server_name="0.0.0.0", server_port=7860, share=False, show_error=True)
    else:
        print("❌ Backend is not running! Please start the backend first:")
        print("   cd backend && python -m app.main")
