import torch
import numpy as np
import json
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class Embedder:
    def __init__(self, config: Config):
        self.model_name = config.get('models.embedding_model', 'bkai-foundation-models/vietnamese-bi-encoder')
        self.device = config.get('models.device', 'cpu')
        
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.model.to(self.device)
        
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.dimension}")
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if not texts:
            logger.warning("No texts provided for embedding.")
            return np.array([])
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        with torch.no_grad():
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
        
        return embeddings

    def _format_table_content(self, chunk):
        """Format table content into readable text for embedding"""
        title = chunk.get("title", "")
        columns = chunk.get("columns", [])
        rows = chunk.get("rows", [])

        lines = [f"Bảng: {title}"]
        if columns:
            lines.append(f"Các cột: {', '.join(columns)}")
        if rows:
            lines.append("Dữ liệu:")
            for row in rows:  # Limit to 10 rows for embedding
                if isinstance(row, list):
                    lines.append(" | ".join(str(cell) for cell in row))
                elif isinstance(row, dict):
                    lines.append(" | ".join(f"{k}: {v}" for k, v in row.items()))
        return "\n".join(lines)

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add embeddings to a list of chunks with flexible structure"""
        texts = []
        
        for chunk in chunks:
            # Handle different chunk types
            if chunk.get("type") == "table":
                # Format table content for embedding
                text_to_embed = self._format_table_content(chunk)
            else:
                # Handle text chunks
                title = chunk.get('title', '')
                content = chunk.get('content', '')
                
                if title and content:
                    text_to_embed = f"{title}\n{content}"
                elif title:
                    text_to_embed = title
                elif content:
                    text_to_embed = content
                else:
                    logger.warning(f"Empty chunk found: {chunk}")
                    text_to_embed = ""
            
            texts.append(text_to_embed)
        
        # Generate embeddings
        embeddings = self.embed_texts(texts)
        
        # Add embeddings to each chunk
        for i, chunk in enumerate(chunks):
            if i < len(embeddings):  # Safety check
                chunk['embedding'] = embeddings[i].tolist()
                chunk['embedding_dimension'] = self.dimension
        
        logger.info(f"Added embeddings to {len(chunks)} chunks")
        return chunks

    def validate_chunks(self, chunks: Any) -> List[Dict[str, Any]]:
        """Validate chunks structure"""
        # Handle wrapper dict
        if isinstance(chunks, dict):
            for key in ['chunks', 'data', 'items']:
                if key in chunks and isinstance(chunks[key], list):
                    logger.info(f"Detected wrapper key '{key}' — extracting chunks.")
                    chunks = chunks[key]
                    break
        
        if not isinstance(chunks, list):
            raise ValueError("JSON must be a list")
        
        valid_chunks = []
        for i, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                raise ValueError(f"Item {i} must be a dictionary")
            
            # Check if chunk has content or is a table
            has_content = 'content' in chunk and chunk['content'].strip()
            is_table = chunk.get('type') == 'table' and ('columns' in chunk or 'rows' in chunk)
            has_title = 'title' in chunk and chunk['title'].strip()
            
            if has_content or is_table or has_title:
                valid_chunks.append(chunk)
            else:
                logger.warning(f"Skipping empty chunk {i}: {chunk}")
        
        return valid_chunks

# if __name__ == "__main__":
#     # Load config
#     config = Config()
#     embedder = Embedder(config)

#     # Load input file
#     input_path = "D:\\rag-project\\data\\processed\\chunks\\bidv_chunks.json"
#     try:
#         with open(input_path, "r", encoding="utf-8") as f:
#             raw_chunks = json.load(f)
#     except Exception as e:
#         logger.error(f"❌ Error reading '{input_path}': {e}")
#         exit(1)

#     # Validate chunks
#     try:
#         chunks = embedder.validate_chunks(raw_chunks)
#         logger.info(f"✅ Successfully validated {len(chunks)} chunks")
#     except ValueError as e:
#         logger.error(f"❌ Invalid format: {e}")
#         exit(1)

#     # Run embedding
#     enriched_chunks = embedder.embed_chunks(chunks)

#     # Save output
#     output_path = "bidv_with_embeddings.json"
#     try:
#         with open(output_path, "w", encoding="utf-8") as f:
#             json.dump(enriched_chunks, f, ensure_ascii=False, indent=2)
#         logger.info(f"✅ Embedded {len(enriched_chunks)} chunks and saved to '{output_path}'")
#     except Exception as e:
#         logger.error(f"❌ Error saving to '{output_path}': {e}")