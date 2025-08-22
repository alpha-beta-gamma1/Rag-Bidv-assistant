from typing import List, Dict, Any
import re
from src.generation.llm_client import GeminiLLMClient
from src.generation.prompt_template import PromptTemplate
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class ResponseGenerator:
    def __init__(self, config: Config):
        self.config = config
        self.llm_client = GeminiLLMClient(config)
        self.prompt_template = PromptTemplate()
        
        # Enhanced patterns for better processing
        self.incomplete_info_patterns = [
            r"không được cung cấp đầy đủ",
            r"thông tin không đầy đủ", 
            r"thiếu thông tin",
            r"chưa có thông tin cụ thể"
        ]

    def generate_response(self, query: str, contexts: List[str]) -> Dict[str, Any]:
        """Tạo phản hồi với enhanced processing."""
        logger.info(f"Generating response for query with {len(contexts)} contexts")

        # Build messages
        messages = self.prompt_template.build_messages(query, contexts)
        
        # Generate response
        raw_response = self.llm_client.generate(messages)

        # Enhanced cleaning
        if self._should_clean_response(raw_response):
            cleaned_response = self._enhanced_clean_response(raw_response)
        else:
            cleaned_response = raw_response

        # Quality assessment
        quality_score = self._assess_response_quality(cleaned_response, query)

        result = {
            "response": cleaned_response,
            "metadata": {
                "contexts_used": len(contexts),
                "query_type": self._classify_query(query),
                "response_cleaned": cleaned_response != raw_response,
                "quality_score": quality_score,
                "word_count": len(cleaned_response.split())
            }
        }
        
        logger.info(f"Response generated - Quality: {quality_score:.2f}")
        return result

    def _should_clean_response(self, response: str) -> bool:
        """Kiểm tra xem có nên làm sạch response hay không."""
        skip_patterns = [
            "Tôi không tìm thấy thông tin phù hợp",
            "Chào quý khách",
            "Xin chào",
            "Cảm ơn"
        ]
        
        return not any(pattern in response for pattern in skip_patterns)

    def _enhanced_clean_response(self, raw_response: str) -> str:
        """Enhanced response cleaning pipeline."""
        text = raw_response.strip()
        
        # Pipeline theo thứ tự ưu tiên
        text = self._fix_incomplete_info_statements(text)
        # text = self._fix_nested_numbering_issues(text)
        text = self._reduce_redundant_phrases(text)
        text = self._improve_formatting(text)
        text = self._remove_generated_questions(text)
        text = self._final_polish(text)
        
        return text.strip()

    def _fix_incomplete_info_statements(self, text: str) -> str:
        """Xử lý các câu nói về thông tin không đầy đủ."""
        for pattern in self.incomplete_info_patterns:
            # Nếu cả câu chỉ nói về thiếu thông tin
            sentence_pattern = f"[^.]*{pattern}[^.]*\\."
            if re.search(sentence_pattern, text, re.I):
                # Thay bằng professional message
                text = re.sub(sentence_pattern, 
                             "Quý khách vui lòng liên hệ chi nhánh để được tư vấn chi tiết.", 
                             text, flags=re.I)
        
        return text

    # def _fix_nested_numbering_issues(self, text: str) -> str:
    #     """Fix vấn đề đánh số lồng nhau confusing."""
    #     # Tìm pattern: "1. Title: 1. SubItem 2. SubItem"
    #     # Chuyển thành: "**Title:** - SubItem - SubItem"
        
    #     lines = text.split('\n')
    #     processed = []
    #     in_numbered_section = False
        
    #     for line in lines:
    #         line = line.strip()
    #         if not line:
    #             processed.append('')
    #             continue
            
    #         # Main section: "1. Title:"
    #         main_match = re.match(r'^(\d+)\.\s+([^:]+):\s*(.*)', line)
    #         if main_match:
    #             title = main_match.group(2)
    #             remainder = main_match.group(3)
    #             processed.append(f"**{title}:**")
    #             if remainder.strip():
    #                 processed.append(remainder)
    #             in_numbered_section = True
    #             continue
            
    #         # Sub-items: "1. Content 2. Content" trong cùng dòng
    #         if in_numbered_section and re.search(r'\d+\.\s+', line):
    #             # Split multiple numbered items trong 1 dòng
    #             parts = re.split(r'(\d+\.\s+)', line)
    #             for i in range(1, len(parts), 2):
    #                 if i+1 < len(parts):
    #                     content = parts[i+1].strip()
    #                     if content:
    #                         processed.append(f"- {content}")
    #             continue
            
    #         # Regular line
    #         processed.append(line)
    #         if not re.search(r'^\s*-', line):  # Reset if not bullet
    #             in_numbered_section = False
        
    #     return '\n'.join(processed)

    def _reduce_redundant_phrases(self, text: str) -> str:
        """Giảm redundancy trong cách diễn đạt."""
        # Giảm "Quý khách hàng" lặp lại
        sentences = text.split('. ')
        for i in range(1, len(sentences)):
            sentences[i] = re.sub(r'\bquý khách hàng\b', 'bạn', sentences[i], flags=re.I)
        
        text = '. '.join(sentences)
        
        # Remove redundant opening phrases
        redundant_openings = [
            r"quý khách hàng có thể tham khảo\s*",
            r"theo thông tin từ tài liệu\s*,?\s*",
            r"dựa trên thông tin được cung cấp\s*,?\s*"
        ]
        
        for pattern in redundant_openings:
            text = re.sub(pattern, "", text, flags=re.I)
        
        return text

    def _improve_formatting(self, text: str) -> str:
        """Cải thiện formatting tổng thể."""
        # Standardize bullet points
        text = re.sub(r'^\s*[•*]\s+', '- ', text, flags=re.M)
        
        # Fix spacing issues
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)
        text = re.sub(r'([,.;:!?])([A-ZÁĂÂÉÊÍÓÔƠÚƯÝ])', r'\1 \2', text)
        
        # Normalize spaces
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Better section breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text

    def _remove_generated_questions(self, text: str) -> str:
        """Xóa các câu hỏi được tạo tự động và options."""
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip question lines
            if self._is_question_line(line):
                continue
                
            # Skip option lines (a), b), c), d)
            if re.match(r'^[a-dA-D][).]', line):
                continue
                
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

    def _is_question_line(self, line: str) -> bool:
        """Kiểm tra dòng câu hỏi."""
        question_indicators = [
            r'\?$',  # Ends with ?
            r'^(có bao nhiêu|hãy|liệt kê|mô tả|tại sao)',
            r'(là gì|như thế nào|ra sao)\?',
            r'^(what|how|why|when|where)\b'
        ]
        
        return any(re.search(pattern, line, re.I) for pattern in question_indicators)

    def _final_polish(self, text: str) -> str:
        """Polish cuối cùng."""

        text = text.strip()

        # Thay **...** bằng xuống dòng
        def replacer(match):
            content = match.group(1).strip()
            return f"\n{content}"
        text = re.sub(r"\*\*(.*?)\*\*", replacer, text)

        # Remove empty bullets
        text = re.sub(r'^\s*-\s*$', '', text, flags=re.M)

        # Ensure proper sentence endings (chỉ thêm . nếu kết thúc bằng chữ/số)
        if re.search(r"[A-Za-zÀ-ỹ0-9]$", text) and not text.endswith((':', '-', '\n')):
            text += "."

        # Clean up whitespace (xóa dòng trống thừa)
        lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)

        return text

    def _assess_response_quality(self, response: str, query: str) -> float:
        """Đánh giá chất lượng response (0-1)."""
        score = 1.0
        
        # Penalties
        if any(pattern in response.lower() for pattern in self.incomplete_info_patterns):
            score -= 0.3
        
        if response.count("quý khách hàng") > 2:
            score -= 0.2
            
        if re.search(r'\d+\.\s+.*\d+\.\s+', response):  # Nested numbering
            score -= 0.2
            
        word_count = len(response.split())
        if word_count < 10:
            score -= 0.2
        elif word_count > 150:
            score -= 0.1
            
        return max(0.0, score)

    def _classify_query(self, query: str) -> str:
        """Phân loại loại câu hỏi để ghi log."""
        query_lower = query.lower().strip()
        
        if any(greeting in query_lower for greeting in ["hi", "hello", "chào", "xin chào"]):
            return "greeting"
        elif any(thanks in query_lower for thanks in ["cảm ơn", "thank you", "thanks"]):
            return "thanks"
        elif any(card_term in query_lower for card_term in ["thẻ", "card", "tín dụng"]):
            return "card_inquiry"
        elif any(loan_term in query_lower for loan_term in ["vay", "loan", "credit"]):
            return "loan_inquiry"
        elif any(rate_term in query_lower for rate_term in ["lãi suất", "rate", "phí"]):
            return "rate_inquiry"
        else:
            return "general_inquiry"