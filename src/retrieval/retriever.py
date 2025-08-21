import numpy as np
from typing import List, Dict, Any, Tuple
from src.retrieval.vector_store import VectorStore
from src.ingestion.embedder import Embedder
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class Retriever:
    def __init__(self, config: Config):
        self.config = config
        self.embedder = Embedder(config)
        self.vector_store = VectorStore(config)
        self.top_k = config.get('retrieval.top_k', 2)
        self.score_threshold = config.get('retrieval.score_threshold', 0.5)
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks for a query"""
        logger.info(f"Retrieving chunks for query: {query[:100]}...")
        
        # Generate query embedding
        query_embedding = self.embedder.embed_texts([query])[0]
        
        # Search in vector store
        results = self.vector_store.search(query_embedding, self.top_k)
        
        # Filter by score threshold
        filtered_results = [
            (chunk, score) for chunk, score in results 
            if score >= self.score_threshold
        ]
        
        logger.info(f"Found {len(filtered_results)} relevant chunks")
        
        # Return chunks with scores
        return [
            {
                **chunk,
                'retrieval_score': score
            }
            for chunk, score in filtered_results
        ]
    
    def load_vector_store(self) -> bool:
        """Load existing vector store"""
        return self.vector_store.load_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics"""
        return {
            **self.vector_store.get_stats(),
            'top_k': self.top_k,
            'score_threshold': self.score_threshold
        }