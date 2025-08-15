from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os

from src.rag_system import RAGSystem

app = FastAPI(title="RAG API")

# CORS: chỉnh whitelist khi deploy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # TODO: thay bằng ["http://localhost:5173", "..."] khi cần
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo 1 lần để tránh load model nhiều lần
rag = RAGSystem("configs/config.yaml")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/query")
async def query(body: dict):
    q = (body or {}).get("question")
    if not q:
        raise HTTPException(400, "Missing 'question' in body")
    try:
        result = rag.query(q)  # kỳ vọng có keys: response, contexts, ...
        return {
            "status": "success",
            "query": q,
            "response": result.get("response"),
            "contexts": result.get("contexts", []),
            "meta": {k: v for k, v in result.items() if k not in ["response", "contexts"]},
        }
    except Exception as e:
        raise HTTPException(500, f"Query error: {e}")