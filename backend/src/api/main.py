"""
FastAPI Backend for Indian Education Law Chatbot
Provides REST API endpoints for legal document search and chat functionality
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import our services
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from services.vector_service import VectorEmbeddingService
    from utils.data_loader import LegalDocumentLoader
    from utils.json_query_engine import JsonQueryEngine
    from utils.query_cache import CachedJsonQueryEngine
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to install all dependencies: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Indian Education Law Chatbot API",
    description="API for searching and querying Indian education law documents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://lawlink.skyzin.com", "https://lawlink.skyzin.com", "https://llm.skyzin.com", "https://llm.skyzin.com"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for services
vector_service: Optional[VectorEmbeddingService] = None
data_loader: Optional[LegalDocumentLoader] = None
json_query_engine: Optional[CachedJsonQueryEngine] = None

# Pydantic models for request/response
class ChatRequest(BaseModel):
    question: str = Field(..., description="User's legal question", min_length=1, max_length=1000)
    context: str = Field("", description="Additional context for the question", max_length=2000)
    source_mode: str = Field("json_only", description="Source selection: 'auto' | 'json_only' | 'vector'", pattern="^(auto|json_only|vector)$")

class DatasetChatResponse(BaseModel):
    """Dataset / RAG only — no Gemini. Empty answer means no usable match."""
    answer: str = Field("", description="Answer text from indexed legal documents")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Relevant legal document sources")

class DocumentSearchRequest(BaseModel):
    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    limit: int = Field(5, description="Number of results to return", ge=1, le=20)
    score_threshold: float = Field(0.0, description="Minimum similarity score", ge=0.0, le=1.0)

class DocumentSearchResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total number of results found")
    query_time: float = Field(..., description="Time taken to search in seconds")

class SystemHealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    status: str = Field(..., description="System status")
    vector_index_loaded: bool = Field(..., description="Whether vector index is loaded")
    total_documents: int = Field(..., description="Total number of indexed documents")
    model_name: str = Field(..., description="Name of the embedding model")
    uptime: str = Field(..., description="System uptime")

# Initialize services
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global vector_service, data_loader, json_query_engine
    
    try:
        logger.info("Starting up Indian Education Law Chatbot API...")
        
        # Initialize data loader
        data_loader = LegalDocumentLoader()
        # Ensure processed documents exist for JSON-only mode
        processed_docs = data_loader.load_processed_documents()
        if not processed_docs:
            logger.info("No processed documents found. Processing raw documents for JSON mode...")
            raw_docs = data_loader.load_json_documents()
            if raw_docs:
                processed_docs = data_loader.process_documents(raw_docs)
                data_loader.save_processed_documents(processed_docs)
            else:
                logger.warning("No raw documents found to process.")
        
        # Initialize JSON query engine with processed documents and caching
        base_json_engine = JsonQueryEngine(processed_docs)
        json_query_engine = CachedJsonQueryEngine(
            base_json_engine, 
            cache_size=500,  # Cache up to 500 queries
            cache_ttl=1800   # Cache for 30 minutes
        )
        logger.info(f"✅ Cached JSON Query Engine initialized with {len(processed_docs)} documents")
        
        # Initialize vector service
        vector_service = VectorEmbeddingService()
        
        # Try to load existing vector index (optional when json_only)
        try:
            vector_service.load_index_for_search()
            logger.info("Loaded existing vector index")
        except FileNotFoundError:
            logger.info("No existing vector index found. Building new index...")
            await build_vector_index()
        
        logger.info("API startup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

async def build_vector_index():
    """Build vector index from available documents"""
    global vector_service, data_loader
    
    try:
        # Load processed documents or create them
        processed_docs = data_loader.load_processed_documents()
        
        if not processed_docs:
            logger.info("No processed documents found. Processing raw documents...")
            raw_docs = data_loader.load_json_documents()
            if raw_docs:
                processed_docs = data_loader.process_documents(raw_docs)
                data_loader.save_processed_documents(processed_docs)
            else:
                logger.warning("No documents found to index!")
                return
        
        # Build vector index
        if processed_docs:
            logger.info(f"Building vector index for {len(processed_docs)} documents...")
            vector_service.build_and_save_index(processed_docs)
            logger.info("Vector index built successfully!")
        
    except Exception as e:
        logger.error(f"Error building vector index: {str(e)}")
        raise

# API Routes
@app.get("/", response_class=JSONResponse)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Indian Education Law Chatbot API",
        "version": "1.0.0",
        "status": "active",
        "documentation": "/docs"
    }

@app.get("/api/health", response_model=SystemHealthResponse)
async def get_system_health():
    """Get system health status"""
    try:
        if not data_loader:
            raise HTTPException(status_code=500, detail="Data loader not initialized")
        
        # Get basic stats
        processed_docs = data_loader.load_processed_documents()
        doc_count = len(processed_docs) if processed_docs else 0
        
        return SystemHealthResponse(
            status="healthy" if doc_count > 0 else "no_data",
            vector_index_loaded=vector_service is not None,
            total_documents=doc_count,
            model_name="json_query_engine",
            uptime="active"
        )
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search", response_model=DocumentSearchResponse)
async def search_documents(request: DocumentSearchRequest):
    """Search for relevant legal documents"""
    import time
    start_time = time.time()
    
    try:
        if not json_query_engine:
            raise HTTPException(status_code=500, detail="JSON query engine not initialized")
        
        # Perform JSON search
        results = json_query_engine.query(
            query_text=request.query,
            max_results=request.limit,
            min_score=request.score_threshold
        )
        
        query_time = time.time() - start_time
        
        return DocumentSearchResponse(
            results=results,
            total_found=len(results),
            query_time=round(query_time, 3)
        )
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _dataset_chat_only(request: ChatRequest) -> DatasetChatResponse:
    """
    Legal dataset / RAG search only. Returns empty answer when no indexed match.
    Gemini is handled by the Node.js orchestrator (port 8000), not here.
    """
    if not json_query_engine:
        raise HTTPException(status_code=500, detail="JSON query engine not initialized")

    search_results = json_query_engine.query(
        request.question,
        max_results=5,
        min_score=0.1,
    )

    if not search_results:
        return DatasetChatResponse(answer="", sources=[])

    answer = generate_legal_answer(request.question, search_results, request.context)

    sources = []
    for result in search_results:
        doc = result["document"]
        content = doc.get("content") or ""
        preview = content[:200] + "..." if len(content) > 200 else content
        sources.append({
            "section": doc.get("section"),
            "title": doc.get("title"),
            "year": doc.get("year"),
            "score": result.get("score"),
            "content_preview": preview,
        })

    return DatasetChatResponse(answer=answer, sources=sources)


@app.post("/api/chat", response_model=DatasetChatResponse)
async def chat_dataset_api(request: ChatRequest):
    try:
        return await _dataset_chat_only(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in dataset chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=DatasetChatResponse)
async def chat_dataset_root(request: ChatRequest):
    """Alias for Node orchestrator (POST https://llm.skyzin.com/chat)."""
    try:
        return await _dataset_chat_only(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in dataset chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_legal_answer(question: str, search_results: List[Dict[str, Any]], context: str = "") -> str:
    """
    Generate a legal answer based on search results
    """
    if not search_results:
        return """No clear answer found in the uploaded documents. Please consult official sources or a lawyer.

For Indian education law matters, I recommend:
1. Consulting the official Ministry of Education website
2. Reviewing the Right to Education Act, 2009
3. Checking UGC regulations for higher education
4. Seeking advice from qualified legal professionals

This system provides information from Indian education law sources. It is not a substitute for professional legal advice."""

    # Get the most relevant document
    top_result = search_results[0]
    top_doc = top_result["document"]
    
    # Build plain-text answer
    lines: List[str] = []
    lines.append("Based on the legal documents in our database, here's what I found regarding your question:")

    header = f"{top_doc.get('section', '').strip()} — {top_doc.get('title', '').strip()} — {top_doc.get('year', '')}"
    lines.append("")
    lines.append(header)
    lines.append("")

    # Add content
    content = top_doc.get('content', '').strip()
    if content and not content.lower().startswith('this is placeholder'):
        lines.append(content)
    else:
        lines.append(f"This section contains legal provisions related to {top_doc.get('section', '')}. Please refer to official sources for the exact legal text.")
    
    if len(search_results) > 1:
        lines.append("")
        lines.append("Related Provisions:")
        for result in search_results[1:3]:
            doc = result["document"]
            lines.append(f"• {doc.get('section', '').strip()} — {doc.get('title', '').strip()} — {doc.get('year', '')}")

    lines.append("")
    lines.append(
        "Important: This information is based on the documents in our legal database. Always verify with official sources and consult qualified legal professionals for specific legal advice."
    )

    return "\n".join(lines)

@app.get("/api/suggestions/{query}")
async def get_query_suggestions(query: str):
    """Get query suggestions based on user input"""
    try:
        if not json_query_engine:
            raise HTTPException(status_code=500, detail="JSON query engine not initialized")
        
        suggestions = json_query_engine.suggest_related_queries(query)
        
        return {
            "query": query,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting query suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics")
async def get_query_analytics():
    """Get detailed query analytics and cache statistics"""
    try:
        if not json_query_engine:
            raise HTTPException(status_code=500, detail="JSON query engine not initialized")
        
        analytics = json_query_engine.get_analytics()
        
        return {
            "analytics": analytics,
            "timestamp": datetime.now().isoformat(),
            "status": "active"
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cache/clear")
async def clear_query_cache():
    """Clear the query cache (admin endpoint)"""
    try:
        if not json_query_engine:
            raise HTTPException(status_code=500, detail="JSON query engine not initialized")
        
        json_query_engine.clear_cache()
        
        return {
            "message": "Query cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_system_statistics():
    """Get detailed system statistics"""
    try:
        if not data_loader:
            raise HTTPException(status_code=500, detail="Services not initialized")
        
        # Get document stats
        processed_docs = data_loader.load_processed_documents()
        doc_stats = data_loader.get_document_statistics(processed_docs) if processed_docs else {}
        
        return {
            "documents": doc_stats,
            "api_status": "active",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found", "message": "Please check the API documentation at /docs"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": "Please check the server logs"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=5000,
        reload=False,
        log_level="info"
    )
