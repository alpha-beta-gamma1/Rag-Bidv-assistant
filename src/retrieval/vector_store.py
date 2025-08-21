# ===== FILE: src/retrieval/vector_store.py =====
import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Any, Tuple
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class VectorStore:
    def __init__(self, config: Config):
        self.config = config
        self.dimension = config.get('vector_store.dimension', 768)
        self.index_path = config.get('vector_store.index_path', 'data/processed/embeddings/faiss_index')
        
        # Create directory if not exists
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        self.index = None
        self.chunks = []
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize FAISS index"""
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        logger.info(f"Initialized FAISS index with dimension {self.dimension}")
    
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add chunks with embeddings to vector store"""
        if not chunks:
            return
        
        embeddings = np.array([chunk['embedding'] for chunk in chunks]).astype('float32')
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        self.index.add(embeddings)
        self.chunks.extend(chunks)
        
        logger.info(f"Added {len(chunks)} chunks to vector store. Total: {len(self.chunks)}")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 2) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar chunks"""
        if self.index.ntotal == 0:
            return []
        
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:  # Valid index
                results.append((self.chunks[idx], float(score)))
        
        return results
    
    def save_index(self):
        """Save FAISS index and chunks to disk"""
        # Save FAISS index
        faiss.write_index(self.index, f"{self.index_path}.faiss")
        
        # Save chunks
        with open(f"{self.index_path}.chunks", 'wb') as f:
            pickle.dump(self.chunks, f)
        
        logger.info(f"Saved vector store to {self.index_path}")
    
    def load_index(self):
            """Load FAISS index and chunks from disk"""
            # Load FAISS index
            try:
                self.index = faiss.read_index(f"{self.index_path}.faiss")
            except (RuntimeError, FileNotFoundError, Exception) as e:
                logger.warning(f"Failed to load FAISS index: {e}")
                self._initialize_index()
                return False
                
            # Load chunks
            try:
                with open(f"{self.index_path}.chunks", 'rb') as f:
                    self.chunks = pickle.load(f)
                logger.info(f"Loaded vector store from {self.index_path}. {len(self.chunks)} chunks loaded.")
                return True
            except FileNotFoundError:
                logger.warning(f"Chunk file not found at {self.index_path}.chunks. Index loaded but no chunks.")
                self.chunks = []
                return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_chunks': len(self.chunks),
            'index_size': self.index.ntotal if self.index else 0,
            'dimension': self.dimension
        }
