from typing import List, Dict, Any
from src.generation.llm_client import LLMClient
from src.generation.prompt_template import PromptTemplate
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class ResponseGenerator:
    def __init__(self, config: Config):
        self.config = config
        self.llm_client = LLMClient(config)
        self.prompt_template = PromptTemplate()
    
    def generate_response(self, query: str, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using retrieved contexts"""
        logger.info(f"Generating response for query with {len(contexts)} contexts")
        
        # Tạo prompt mà không dùng lịch sử hội thoại
        prompt = self.prompt_template.create_prompt(query, contexts)
        
        # Generate response
        response = self.llm_client.generate(prompt)
        
        # Prepare result
        result = {
            'query': query,
            'response': response,
            'contexts': contexts,
            'metadata': {
                'num_contexts': len(contexts),
                'context_scores': [ctx.get('retrieval_score', 0) for ctx in contexts],
                'prompt_length': len(prompt)
            }
        }
        
        logger.info("Response generated successfully")
        return result
    
    def generate_simple_response(self, query: str, contexts: List[Dict[str, Any]]) -> str:
        """Generate simple response (text only)"""
        result = self.generate_response(query, contexts)
        return result['response']