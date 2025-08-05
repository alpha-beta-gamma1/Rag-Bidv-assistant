import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.rag_system import RAGSystem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description='RAG System - Vietnamese Document Q&A')
    parser.add_argument('--config', help='Path to config file', default='configs/config.yaml')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest documents')
    ingest_parser.add_argument('files', nargs='+', help='Files to ingest')
    
    # Query command  
    query_parser = subparsers.add_parser('query', help='Query the system')
    query_parser.add_argument('question', help='Question to ask')
    
    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Interactive chat')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show system statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize RAG system
    rag_system = RAGSystem(args.config)
    
    if args.command == 'ingest':
        logger.info(f"Ingesting {len(args.files)} files")
        results = rag_system.ingest_multiple_documents(args.files)
        
        for result in results:
            if 'error' in result:
                print(f"❌ {result['file_path']}: {result['error']}")
            else:
                print(f"✅ {result['file_path']}: {result['chunks_created']} chunks")
    
    elif args.command == 'query':
        logger.info(f"Processing query: {args.question}")
        result = rag_system.query(args.question)
        
        print(f"\n📝 Câu hỏi: {result['query']}")
        print(f"🤖 Trả lời: {result['response']}")
        
        # if result['contexts']:
        #     print(f"\n📚 Nguồn thông tin ({len(result['contexts'])} đoạn):")
        #     for i, ctx in enumerate(result['contexts'], 1):
        #         title = ctx.get('title', 'Không có tiêu đề')
        #         score = ctx.get('retrieval_score', 0)
        #         print(f"  {i}. {title} (độ liên quan: {score:.2f})")
    
    elif args.command == 'chat':
        from scripts.interactive_chat import InteractiveChat
        chat = InteractiveChat(args.config)
        chat.run()
    
    elif args.command == 'stats':
        stats = rag_system.get_system_stats()
        print("📊 Thống kê hệ thống RAG:")
        print(f"  • Tổng chunks: {stats['retriever_stats']['total_chunks']}")
        print(f"  • Kích thước index: {stats['retriever_stats']['index_size']}")
        print(f"  • Embedding model: {stats['config']['embedding_model']}")
        print(f"  • LLM model: {stats['config']['llm_model']}")

if __name__ == "__main__":
    main()