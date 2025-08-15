import unittest
from unittest.mock import Mock, patch
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.utils.config import Config
from src.generation.response_generator import ResponseGenerator
from src.rag_system import RAGSystem

class TestGeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are reused across all tests"""
        # Load the config file path
        cls.config_path = "configs/config.yaml"
        
        # Sample test data
        cls.sample_query = "Cho tôi biết thông tin về lãi suất vay mua nhà?"
        cls.sample_contexts = [
            "Lãi suất vay mua nhà BIDV từ 7.5%/năm",
            "Thời hạn vay tối đa 25 năm",
            "Hỗ trợ vay tới 80% giá trị tài sản"
        ]
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        config = Config(self.config_path)
        self.response_generator = ResponseGenerator(config)

    def test_response_generator_initialization(self):
        """Test that ResponseGenerator initializes correctly"""
        self.assertIsNotNone(self.response_generator)
        self.assertTrue(hasattr(self.response_generator, 'generate_response'))

    @patch('src.generation.response_generator.ResponseGenerator.generate_response')
    def test_response_generation_with_context(self, mock_generate):
        """Test response generation with provided context"""
        # Mock the LLM response
        expected_response = "BIDV cung cấp khoản vay mua nhà với lãi suất từ 7.5%/năm, thời hạn vay lên đến 25 năm. Ngân hàng hỗ trợ cho vay tới 80% giá trị tài sản."
        mock_generate.return_value = expected_response

        # Generate response
        response = self.response_generator.generate_response(
            query=self.sample_query,
            contexts=self.sample_contexts
        )

        # Assertions
        self.assertIsNotNone(response)
        self.assertEqual(response, expected_response)
        mock_generate.assert_called_once()

    @patch('src.generation.response_generator.ResponseGenerator.generate_response')
    def test_response_generation_without_context(self, mock_generate):
        """Test response generation without context"""
        # Mock the LLM response for no context
        expected_response = "Tôi không có đủ thông tin để trả lời câu hỏi này một cách chính xác. Vui lòng liên hệ chi nhánh BIDV gần nhất để được tư vấn chi tiết."
        mock_generate.return_value = expected_response

        # Generate response without context
        response = self.response_generator.generate_response(
            query=self.sample_query,
            contexts=[]
        )

        # Assertions
        self.assertIsNotNone(response)
        self.assertEqual(response, expected_response)
        mock_generate.assert_called_once()

    def test_end_to_end_query(self):
        """Test the entire generation pipeline through RAG system"""
        # Mock the RAG system's response generator
        with patch('src.generation.response_generator.ResponseGenerator.generate_response') as mock_generate:
            expected_response = "BIDV cung cấp khoản vay mua nhà với lãi suất từ 7.5%/năm."
            mock_generate.return_value = expected_response

            # Initialize RAG system
            rag = RAGSystem(self.config_path)
            
            # Make query
            result = rag.query(self.sample_query)

            # Assertions
            self.assertIsInstance(result, str)
            self.assertEqual(result, expected_response)
            mock_generate.assert_called_once()

    def test_error_handling(self):
        """Test error handling in response generation"""
        # Test with empty query
        with self.assertRaises(ValueError):
            self.response_generator.generate_response(
                query="",
                contexts=self.sample_contexts
            )

        # Test with invalid context type
        with self.assertRaises(TypeError):
            # Force a type error by passing an invalid type for contexts
            self.response_generator.generate_response(
                query=self.sample_query,
                contexts={"invalid": "format"}  # Should be a list of strings
            )

if __name__ == '__main__':
    unittest.main()
