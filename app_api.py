from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from src.rag_system import RAGSystem

app = FastAPI(title="RAG API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc whitelist domain React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = RAGSystem("configs/config.yaml")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
async def ingest(files: List[UploadFile] = File(...)):
    try:
        paths = []
        for f in files:
            p = f"/tmp/{f.filename}"
            with open(p, "wb") as out:
                out.write(await f.read())
            paths.append(p)
        return rag.ingest_multiple_documents(paths)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/query")
async def query(body: dict):
    q = body.get("question")
    if not q:
        raise HTTPException(400, "Missing question")
    return rag.query(q)

@app.get("/stats")
def stats():
    return rag.get_system_stats()