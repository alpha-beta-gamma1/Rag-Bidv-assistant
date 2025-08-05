import os
import sys
from typing import List, Dict

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.rag_system import RAGSystem
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class InteractiveChat:
    def __init__(self, config_path: str = None):
        self.rag_system = RAGSystem(config_path)
        self.chat_history: List[Dict[str, str]] = []
        
    def run(self):
        """Run interactive chat loop"""
        print("🤖 RAG System Chat Interface")
        print("Nhập 'quit' để thoát, 'clear' để xóa lịch sử, 'stats' để xem thống kê")
        print("-" * 50)
        
        while True:
            try:
                # Get user input
                user_input = input("\n👤 Bạn: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() == 'quit':
                    print("👋 Tạm biệt!")
                    break
                elif user_input.lower() == 'clear':
                    self.chat_history = []
                    print("🧹 Đã xóa lịch sử chat")
                    continue
                elif user_input.lower() == 'stats':
                    self._show_stats()
                    continue
                
                # Process query
                print("🤔 Đang tìm kiếm thông tin...")
                result = self.rag_system.query(user_input, self.chat_history)
                
                # Display response
                response = result['response']
                print(f"\n🤖 Assistant: {response}")
                
                # Show context information
                contexts = result['contexts']
                if contexts:
                    print(f"\n📚 Tìm thấy {len(contexts)} đoạn thông tin liên quan:")
                    for i, ctx in enumerate(contexts[:3], 1):  # Show top 3
                        title = ctx.get('title', 'Không có tiêu đề')
                        score = ctx.get('retrieval_score', 0)
                        print(f"  {i}. {title} (độ liên quan: {score:.2f})")
                
                # Update chat history
                self.chat_history.append({
                    'user': user_input,
                    'assistant': response
                })
                
                # Keep only last 5 exchanges
                if len(self.chat_history) > 5:
                    self.chat_history = self.chat_history[-5:]
                
            except KeyboardInterrupt:
                print("\n\n👋 Tạm biệt!")
                break
            except Exception as e:
                logger.error(f"Error in chat: {e}")
                print(f"❌ Lỗi: {e}")
    
    def _show_stats(self):
        """Show system statistics"""
        stats = self.rag_system.get_system_stats()
        print("\n📊 Thống kê hệ thống:")
        print(f"  • Tổng số chunks: {stats['retriever_stats']['total_chunks']}")
        print(f"  • Kích thước index: {stats['retriever_stats']['index_size']}")
        print(f"  • Embedding model: {stats['config']['embedding_model']}")
        print(f"  • LLM model: {stats['config']['llm_model']}")
        print(f"  • Top-K: {stats['config']['top_k']}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Interactive chat with RAG system')
    parser.add_argument('--config', help='Path to config file', default=None)
    
    args = parser.parse_args()
    
    chat = InteractiveChat(args.config)
    chat.run()