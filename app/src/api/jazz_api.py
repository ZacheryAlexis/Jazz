"""
Jazz REST API - FastAPI wrapper for Ubuntu VM deployment
Provides HTTP endpoints for chat, RAG queries, and token tracking
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks  # type: ignore
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
import sys
import logging
from datetime import datetime

# Setup path for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, BASE_DIR)

from app import CLI
from app.src.core.ui import AgentUI
from rich.console import Console

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Jazz REST API",
    description="Two-stage RAG system with web search and knowledge base integration",
    version="1.0.0"
)

# Initialize Jazz CLI once at startup
jazz_cli = None
jazz_console = None

@app.on_event("startup")
async def startup_event():
    """Initialize Jazz system on startup"""
    global jazz_cli, jazz_console
    try:
        jazz_console = Console(
            force_terminal=True,
            legacy_windows=False,
            width=100
        )
        
        # Load config
        config_path = os.path.join(BASE_DIR, "config.json")
        with open(config_path) as f:
            config = json.load(f)
        
        # Initialize CLI
        api_keys = {
            "cerebras": os.getenv("CEREBRAS_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "google": os.getenv("GOOGLE_GEN_AI_API_KEY"),
            "ollama": os.getenv("OLLAMA_API_KEY", "dummy")
        }
        
        provider = config.get("provider")
        model = config.get("model")
        api_key = api_keys.get(provider)
        
        AGENT_TYPES = ["general", "code_gen", "brainstormer", "web_searcher"]
        raw_provider_per_model = config.get("provider_per_model") or {}
        provider_per_model = {k: (raw_provider_per_model.get(k) or provider) for k in AGENT_TYPES}
        
        raw_models = config.get("models") or {}
        models = {k: (raw_models.get(k) or model) for k in AGENT_TYPES}
        
        api_key_per_model = {k: api_keys.get(provider_per_model.get(k), api_key) for k in AGENT_TYPES}
        
        temperatures = config.get("temperatures") or {}
        system_prompts = config.get("system_prompts") or {}
        
        embedding_provider = config.get("embedding_provider") or ""
        embedding_model = config.get("embedding_model") or ""
        scraping_method = config.get("scraping_method") or "simple"
        
        jazz_cli = CLI(
            provider=provider,
            provider_per_model=provider_per_model,
            models=models,
            api_key=api_key,
            api_key_per_model=api_key_per_model,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            temperatures=temperatures,
            system_prompts=system_prompts,
            scraping_method=scraping_method,
            stream=False,  # API mode doesn't stream
        )
        
        logger.info("Jazz system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Jazz: {str(e)}")
        raise

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request model"""
    query: str
    agent_type: Optional[str] = "web_searcher"
    use_rag: Optional[bool] = True
    use_web_search: Optional[bool] = True
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    sources: Optional[List[Dict[str, Any]]] = None
    stage1_output: Optional[str] = None
    tokens_estimated: Optional[Dict[str, int]] = None
    timestamp: str
    duration_seconds: float

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    jazz_initialized: bool
    timestamp: str

class StatusResponse(BaseModel):
    """System status response"""
    status: str
    system_info: Dict[str, Any]
    timestamp: str

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", response_class=dict)
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Jazz REST API",
        "version": "1.0.0",
        "description": "Two-stage RAG system with web search and knowledge base",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "chat": "/api/chat",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if jazz_cli else "degraded",
        jazz_initialized=jazz_cli is not None,
        timestamp=datetime.now().isoformat()
    )

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system status"""
    if not jazz_cli:
        raise HTTPException(status_code=503, detail="Jazz system not initialized")
    
    return StatusResponse(
        status="ready",
        system_info={
            "platform": sys.platform,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "jazz_initialized": True,
            "rag_enabled": hasattr(jazz_cli, 'rag') and jazz_cli.rag,
            "web_search_enabled": hasattr(jazz_cli, 'internet') and jazz_cli.internet,
        },
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint
    
    Executes two-stage RAG pipeline:
    - Stage 1: Web search + narrative extraction
    - Stage 2: Theoretical synthesis with knowledge base
    
    Args:
        request: ChatRequest with query and options
    
    Returns:
        ChatResponse with output, sources, and token estimates
    """
    if not jazz_cli:
        raise HTTPException(status_code=503, detail="Jazz system not initialized")
    
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    import time
    start_time = time.time()
    
    try:
        # Use the web_searcher agent from the CLI (which has two-stage RAG integrated)
        agent = jazz_cli.default_web_searcher_agent
        
        # Set configuration
        agent.rag = request.use_rag
        agent.internet = request.use_web_search
        
        # Execute chat using invoke method (returns dict with response)
        # invoke is the agent execution method used in langgraph
        result = agent.invoke(request.query)
        response_text = result.get("response", str(result)) if isinstance(result, dict) else str(result)
        
        # Extract token estimates if available
        tokens = {"stage1": 0, "stage2": 0, "total": 0}
        if hasattr(agent, '_stage1_tokens'):
            tokens["stage1"] = agent._stage1_tokens
        if hasattr(agent, '_stage2_tokens'):
            tokens["stage2"] = agent._stage2_tokens
        tokens["total"] = tokens["stage1"] + tokens["stage2"]
        
        # Extract stage1 output if available
        stage1_output = None
        if hasattr(agent, '_stage1_output'):
            stage1_output = agent._stage1_output[:500]  # First 500 chars
        
        # Extract sources if available
        sources = None
        if hasattr(agent, 'last_sources') and agent.last_sources:
            sources = agent.last_sources
        
        duration = time.time() - start_time
        
        return ChatResponse(
            response=response_text,
            sources=sources,
            stage1_output=stage1_output,
            tokens_estimated=tokens if tokens["total"] > 0 else None,
            timestamp=datetime.now().isoformat(),
            duration_seconds=duration
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        duration = time.time() - start_time
        
        return ChatResponse(
            response=f"Error processing query: {str(e)}",
            sources=None,
            stage1_output=None,
            tokens_estimated=None,
            timestamp=datetime.now().isoformat(),
            duration_seconds=duration
        )

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unexpected error: {str(exc)}")
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn  # type: ignore
    
    # Get configuration from environment
    host = os.getenv("JAZZ_API_HOST", "0.0.0.0")
    port = int(os.getenv("JAZZ_API_PORT", "5000"))
    workers = int(os.getenv("JAZZ_API_WORKERS", "1"))
    
    print(f"""
    ╔════════════════════════════════════════╗
    ║   JAZZ REST API - STARTING             ║
    ╠════════════════════════════════════════╣
    ║   Host: {host:<30} ║
    ║   Port: {port:<30} ║
    ║   Workers: {workers:<26} ║
    ║   Docs: http://{host}:{port}/docs{' '*16} ║
    ╚════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
        log_level="info"
    )
