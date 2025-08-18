import os
import json
from typing import List, Dict, Any
from pathlib import Path
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.ingestion.document_loader import DocumentLoader
from src.ingestion.text_splitter import TextSplitter
from src.ingestion.embedder import Embedder
from src.retrieval.retriever import Retriever
from src.generation.response_generator import ResponseGenerator

logger = setup_logger(__name__)

class RAGSystem:
    def __init__(self, config_path: str = None):
        self.config = Config(config_path)
        
        # Initialize components
        self.document_loader = DocumentLoader()
        self.text_splitter = TextSplitter(self.config)
        self.embedder = Embedder(self.config)
        self.retriever = Retriever(self.config)
        logger.debug(f"Config for LLM generation: {self.config.get('generation')}")
        self.response_generator = ResponseGenerator(self.config)
        
        # Try to load existing vector store
        self.retriever.load_vector_store()
        
        logger.info("RAG System initialized successfully")
    
    def ingest_document(self, file_path: str) -> Dict[str, Any]:
        """Complete document ingestion pipeline"""
        logger.info(f"Starting document ingestion: {file_path}")
        
        # Load document
        document = self.document_loader.load_document(file_path)

        doc_for_splitter = {
            "file_path": file_path,
            "metadata": document.get("metadata", {"source": "BIDV.docx"})
        }
        
        # Split into chunks
        chunks = self.text_splitter.split_document(doc_for_splitter)

        # Generate embeddings
        chunks_with_embeddings = self.embedder.embed_chunks(chunks)
        
        # Add to vector store
        self.retriever.vector_store.add_chunks(chunks_with_embeddings)
        
        # Save vector store
        self.retriever.vector_store.save_index()
        
        # Save processed chunks
        self._save_chunks(chunks_with_embeddings, file_path)
        
        result = {
            'file_path': file_path,
            'chunks_created': len(chunks_with_embeddings),
            'document_metadata': document['metadata']
        }
        
        logger.info(f"Document ingestion completed: {result}")
        return result
    
    def ingest_multiple_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Ingest multiple documents"""
        results = []
        for file_path in file_paths:
            try:
                result = self.ingest_document(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error ingesting {file_path}: {e}")
                results.append({
                    'file_path': file_path,
                    'error': str(e)
                })
        return results
    
    def query(self, question: str) -> Dict[str, Any]:
        logger.info(f"Processing query: {question}")
        contexts = self.retriever.retrieve(question)
        contents = [
            self.embedder._format_table_content(ctx) if ctx.get("type") == "table"
            else (ctx.get("content") or ctx.get("text", ""))
            for ctx in contexts
        ]

        response = self.response_generator.generate_response(question, contents)

        return {
            "question": question,
            "response": response["response"],
            "contexts": contents  # thêm dòng này để debug context
        }

    
    def _save_chunks(self, chunks: List[Dict[str, Any]], file_path: str):
        """Save processed chunks to JSON file"""
        output_dir = "data/processed/chunks"
        os.makedirs(output_dir, exist_ok=True)
        
        file_name = Path(file_path).stem
        output_path = os.path.join(output_dir, f"{file_name}_chunks.json")
        
        # Remove embeddings for JSON serialization (they're stored in vector store)
        chunks_for_save = []
        for chunk in chunks:
            chunk_copy = chunk.copy()
            chunk_copy.pop('embedding', None)
            chunks_for_save.append(chunk_copy)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_for_save, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved chunks to: {output_path}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            'retriever_stats': self.retriever.get_stats(),
            'config': {
                'embedding_model': self.config.get('models.embedding_model'),
                'llm_model': self.config.get('models.llm_model'),
                'max_tokens': self.config.get('chunking.max_tokens'),
                'top_k': self.config.get('retrieval.top_k')
            }
        }