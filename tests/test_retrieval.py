import unittest
from unittest.mock import Mock, patch
import os
import sys
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.utils.config import Config
from src.retrieval.retriever import Retriever
from src.retrieval.vector_store import VectorStore
from src.retrieval.reranker import Reranker
from src.ingestion.embedder import Embedder


class TestRetrieval(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are reused across all tests"""
        # Create a temporary directory for test data
        cls.test_dir = tempfile.mkdtemp()
        cls.config_path = "configs/config.yaml"
        
        # Sample test data
        cls.sample_chunks = [
            {
                "text": "Lãi suất vay mua nhà BIDV từ 7.5%/năm",
                "embedding": np.random.rand(768).astype('float32'),
                "metadata": {"source": "test_doc_1", "page": 1}
            },
            {
                "text": "Thời hạn vay tối đa 25 năm",
                "embedding": np.random.rand(768).astype('float32'),
                "metadata": {"source": "test_doc_1", "page": 1}
            },
            {
                "text": "Hỗ trợ vay tới 80% giá trị tài sản",
                "embedding": np.random.rand(768).astype('float32'),
                "metadata": {"source": "test_doc_1", "page": 2}
            }
        ]
        cls.sample_query = "Cho tôi biết thông tin về lãi suất vay mua nhà?"
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.config = Config(self.config_path)
        self.retriever = Retriever(self.config)
        self.vector_store = VectorStore(self.config)
        self.reranker = Reranker(threshold=0.5)

    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures after all tests"""
        # Remove temporary directory and files
        shutil.rmtree(cls.test_dir)
    
    def test_vector_store_initialization(self):
        """Test that VectorStore is properly initialized"""
        self.assertIsNotNone(self.vector_store)
        self.assertIsNotNone(self.vector_store.index)
        self.assertEqual(self.vector_store.dimension, 768)  # Default dimension
        self.assertEqual(len(self.vector_store.chunks), 0)

    def test_add_and_search_chunks(self):
        """Test adding chunks and searching in vector store"""
        # Add chunks to vector store
        self.vector_store.add_chunks(self.sample_chunks)
        
        # Create a test query embedding
        query_embedding = np.random.rand(768).astype('float32')
        
        # Search
        results = self.vector_store.search(query_embedding, top_k=2)
        
        # Assertions
        self.assertEqual(len(results), 2)
        for chunk, score in results:
            self.assertIsInstance(chunk, dict)
            self.assertIsInstance(score, float)
            self.assertTrue("text" in chunk)
            self.assertTrue("embedding" in chunk)
            self.assertTrue("metadata" in chunk)

    def test_save_and_load_index(self):
        """Test saving and loading vector store index"""
        # Add chunks and save
        self.vector_store.add_chunks(self.sample_chunks)
        self.vector_store.save_index()
        
        # Create new vector store and load
        new_vector_store = VectorStore(self.config)
        success = new_vector_store.load_index()
        
        # Assertions
        self.assertTrue(success)
        self.assertEqual(len(new_vector_store.chunks), len(self.sample_chunks))
        
        # Test search with loaded index
        query_embedding = np.random.rand(768).astype('float32')
        results = new_vector_store.search(query_embedding, top_k=2)
        self.assertEqual(len(results), 2)

    @patch('src.ingestion.embedder.Embedder.embed_texts')
    def test_retriever_functionality(self, mock_embed):
        """Test retriever's main functionality"""
        # Mock embedder response
        mock_embed.return_value = [np.random.rand(768).astype('float32')]
        
        # Add test chunks to vector store
        self.retriever.vector_store.add_chunks(self.sample_chunks)
        
        # Test retrieval
        results = self.retriever.retrieve(self.sample_query)
        
        # Assertions
        self.assertIsInstance(results, list)
        for result in results:
            self.assertIsInstance(result, dict)
            self.assertTrue("text" in result)
            self.assertTrue("metadata" in result)
            self.assertTrue("retrieval_score" in result)

    def test_reranker_filtering(self):
        """Test reranker's threshold filtering"""
        # Create test results with various scores
        test_results = [
            {"text": "doc1", "distance": 0.3},
            {"text": "doc2", "distance": 0.6},
            {"text": "doc3", "distance": 0.4},
            {"text": "doc4", "distance": 0.8}
        ]
        
        # Filter results
        filtered = self.reranker.rerank(test_results)
        
        # Check that only results with distance < threshold remain
        self.assertEqual(len(filtered), 2)
        for result in filtered:
            self.assertLess(result["distance"], self.reranker.threshold)

    def test_retriever_empty_store(self):
        """Test retrieval behavior with empty vector store"""
        # Try to retrieve without adding any documents
        results = self.retriever.retrieve(self.sample_query)
        
        # Should return empty list
        self.assertEqual(len(results), 0)

    def test_get_stats(self):
        """Test retrieval statistics"""
        # Add chunks first
        self.retriever.vector_store.add_chunks(self.sample_chunks)
        
        # Get stats
        stats = self.retriever.get_stats()
        
        # Verify stats content
        self.assertIn('total_chunks', stats)
        self.assertIn('index_size', stats)
        self.assertIn('dimension', stats)
        self.assertIn('top_k', stats)
        self.assertIn('score_threshold', stats)
        
        # Verify values
        self.assertEqual(stats['total_chunks'], len(self.sample_chunks))
        self.assertEqual(stats['dimension'], 768)
        self.assertEqual(stats['top_k'], self.retriever.top_k)

if __name__ == '__main__':
    unittest.main()
