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

    def generate_response(self, query: str, contexts: List[str]) -> Dict[str, Any]:
        """Tạo phản hồi với text cleaning được tích hợp sẵn trong LLM client."""
        logger.info(f"Generating response for query with {len(contexts)} contexts")

        # Build messages (đã được làm sạch bên trong LLM client)
        messages = self.prompt_template.build_messages(query, contexts)
        
        # Generate response (text cleaning được thực hiện tự động trong LLM client)
        raw_response = self.llm_client.generate(messages)

        # Áp dụng làm sạch response nếu cần thiết
        if self._should_clean_response(raw_response):
            cleaned_response = self._clean_response(raw_response)
        else:
            cleaned_response = raw_response

        result = {
            "response": cleaned_response,
            "metadata": {
                "contexts_used": len(contexts),
                "query_type": self._classify_query(query),
                "response_cleaned": cleaned_response != raw_response
            }
        }
        
        logger.info("Response generated successfully")
        return result

    def _should_clean_response(self, response: str) -> bool:
        """Kiểm tra xem có nên làm sạch response hay không."""
        # Không làm sạch các response chuẩn
        skip_patterns = [
            "Tôi không tìm thấy thông tin phù hợp",
            "Chào quý khách",
            "Xin chào",
            "Cảm ơn"
        ]
        
        for pattern in skip_patterns:
            if pattern in response:
                return False
        
        return True

    def _classify_query(self, query: str) -> str:
        """Phân loại loại câu hỏi để ghi log."""
        query_lower = query.lower().strip()
        
        if any(greeting in query_lower for greeting in ["hi", "hello", "chào", "xin chào"]):
            return "greeting"
        elif any(thanks in query_lower for thanks in ["cảm ơn", "thank you", "thanks"]):
            return "thanks"
        elif any(simple in query_lower for simple in ["ok", "được rồi", "bye", "tạm biệt"]):
            return "simple"
        else:
            return "business_query"

    def _clean_response(self, raw_response: str) -> str:
        """Làm sạch response sau khi nhận từ LLM."""
        text = raw_response.strip()
        
        # Áp dụng các hàm làm sạch theo thứ tự ưu tiên
        text = self._remove_generated_questions(text)
        text = self._remove_unwanted_phrases(text)
        text = self._format_response(text)
        
        return text.strip()

    def _remove_generated_questions(self, s: str) -> str:
        """Xóa các câu hỏi được tạo tự động và options a), b), c), d)."""
        lines = [ln.strip() for ln in s.split("\n") if ln.strip()]
        out = []
        
        for ln in lines:
            # Bỏ qua các dòng có dạng câu hỏi hoặc options
            if self._is_question_line(ln) or re.match(r"^[a-dA-D][).]", ln):
                continue
            out.append(ln)
            
        return "\n".join(out)

    def _is_question_line(self, line: str) -> bool:
        """Kiểm tra xem có phải là dòng câu hỏi không."""
        question_patterns = [
            r"\?$",  # Kết thúc bằng dấu hỏi
            r"^(có bao nhiêu|hãy|liệt kê|mô tả|tại sao)",  # Bắt đầu bằng từ hỏi
            r"(là gì|như thế nào|ra sao)\?"  # Chứa cấu trúc câu hỏi
        ]
        
        return any(re.search(pattern, line, re.I) for pattern in question_patterns)

    def _remove_unwanted_phrases(self, s: str) -> str:
        """Xóa các cụm từ không mong muốn."""
        patterns = [
            r"dựa trên thông tin (trên|đã cung cấp),?\s*",
            r"theo (thông tin|tài liệu),?\s*",
            r"căn cứ vào,?\s*",
            r"chúc.*?$",
            r"rất mong.*?$",
            r"cảm ơn.*?$",
            r"xin chào.*?$",
        ]
        
        # Áp dụng các pattern để làm sạch
        for pattern in patterns:
            s = re.sub(pattern, "", s, flags=re.I | re.M)
            
        return s

    def _format_response(self, s: str) -> str:
        """Định dạng lại response."""
        if not s:
            return s
            
        # Chuẩn hóa khoảng trắng
        s = re.sub(r"\s+", " ", s)
        
        # Xóa nhiều dòng trống liên tiếp
        s = re.sub(r"\n\s*\n+", "\n", s)
        
        # Viết hoa chữ cái đầu nếu cần
        if s and s[0].islower():
            s = s[0].upper() + s[1:]
            
        # Thêm khoảng trắng sau dấu câu nếu thiếu
        s = re.sub(r"([.!?])([A-Z])", r"\1 \2", s)
        
        # Định dạng lại số thứ tự
        s = re.sub(r"^(\d+)\.\s+", r"\1. ", s, flags=re.M)
        
        return s