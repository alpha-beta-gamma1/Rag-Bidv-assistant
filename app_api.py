from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging
from src.rag_system import RAGSystem

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG API")

rag = RAGSystem(config_path="config.yaml")
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/query")
async def query(body: Dict[Any, Any]):
    try:
        # Log the incoming request
        logger.debug(f"Received request body: {body}")
        
        q = (body or {}).get("question")
        if not q:
            raise HTTPException(400, "Missing 'question' in body")
            
        # Log the question
        logger.debug(f"Processing question: {q}")
        
        # Your RAG system query
        result = rag.query(q)
        
        # Log the result
        logger.debug(f"Query result: {result}")
        
        return {
            "status": "success",
            "query": q,
            "response": result.get("response", ""),
            "contexts": result.get("contexts", []),
            "meta": {k: v for k, v in result.items() if k not in ["response", "contexts"]},
        }
    except Exception as e:
        # Log the full error
        logger.error(f"Query error: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Query error: {str(e)}")