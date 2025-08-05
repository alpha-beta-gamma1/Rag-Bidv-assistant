import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.rag_system import RAGSystem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def batch_ingest_documents(input_dir: str, config_path: str = None):
    """Batch ingest all documents in a directory"""
    
    # Initialize RAG system
    rag_system = RAGSystem(config_path)
    
    # Find all supported documents
    input_path = Path(input_dir)
    supported_extensions = ['.docx', '.txt', '.json']
    
    document_files = []
    for ext in supported_extensions:
        document_files.extend(input_path.glob(f'**/*{ext}'))
    
    if not document_files:
        logger.warning(f"No supported documents found in {input_dir}")
        return
    
    logger.info(f"Found {len(document_files)} documents to process")
    
    # Process documents
    results = rag_system.ingest_multiple_documents([str(f) for f in document_files])
    
    # Summary
    successful = len([r for r in results if 'error' not in r])
    failed = len(results) - successful
    
    logger.info(f"Batch ingestion completed: {successful} successful, {failed} failed")
    
    # Print detailed results
    for result in results:
        if 'error' in result:
            logger.error(f"Failed: {result['file_path']} - {result['error']}")
        else:
            logger.info(f"Success: {result['file_path']} - {result['chunks_created']} chunks")
    
    # Print system stats
    stats = rag_system.get_system_stats()
    logger.info(f"System stats: {stats}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch ingest documents into RAG system')
    parser.add_argument('input_dir', help='Directory containing documents to ingest')
    parser.add_argument('--config', help='Path to config file', default=None)
    
    args = parser.parse_args()
    
    batch_ingest_documents(args.input_dir, args.config)