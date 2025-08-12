import os
from typing import Dict, Any
import yaml
from pathlib import Path

class Config:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = "configs/config.yaml"
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'models': {
                'embedding_model': 'bkai-foundation-models/vietnamese-bi-encoder',
                'llm_model': 'gemini-2.5-flash',
                'device': 'cuda' if os.getenv('CUDA_AVAILABLE', 'false').lower() == 'true' else 'cpu'
            },
            'chunking': {
                'max_tokens': 400,
                'overlap': 50
            },
            'retrieval': {
                'top_k': 3,
                'score_threshold': 0.4
            },
            'vector_store': {
                'type': 'faiss',
                'index_path': 'data/processed/embeddings/faiss_index',
                'dimension': 768
            },
            'generation': {
                'max_new_tokens': 512,
                'temperature': 0.7,
                'do_sample': True
            }
        }
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, {})
        return value if value != {} else default