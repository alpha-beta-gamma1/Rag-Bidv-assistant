# from typing import List, Dict, Any
# import re
# from src.generation.llm_client import LocalQwenLLMClient  # Updated import
# from src.generation.prompt_template import PromptTemplate
# from src.utils.config import Config
# from src.utils.logger import setup_logger

# logger = setup_logger(__name__)

# class ResponseGenerator:
#     def __init__(self, config: Config):
#         self.config = config
#         self.llm_client = LocalQwenLLMClient(config)  # Changed to LocalQwenLLMClient
#         self.prompt_template = PromptTemplate()

#     def generate_response(self, query: str, contexts: List[str]) -> Dict[str, Any]:
#         logger.info(f"Generating response for query with {len(contexts)} contexts")

#         messages = self.prompt_template.build_messages(query, contexts)
#         raw_response = self.llm_client.generate(messages)

#         # Apply cleaning only when response is not a hardcoded answer
#         # Or if prompt is not a greeting
#         if "Tôi không tìm thấy thông tin phù hợp" not in raw_response and "Chào quý khách" not in raw_response:
#             cleaned_response = self._clean_response(raw_response)
#         else:
#             cleaned_response = raw_response

#         result = {
#             "response": cleaned_response,
#         }
#         logger.info("Response generated and cleaned successfully")
#         return result

#     def _clean_response(self, raw_response: str) -> str:
#         text = raw_response.strip()
#         # Apply cleaning functions in priority order
#         text = self._remove_generated_questions(text)
#         text = self._remove_unwanted_phrases(text)
#         text = self._format_response(text)
#         return text.strip()

#     def _remove_generated_questions(self, s: str) -> str:
#         lines = [ln.strip() for ln in s.split("\n") if ln.strip()]
#         out = []
#         for ln in lines:
#             if self._is_question_line(ln) or re.match(r"^[a-dA-D][).]", ln):
#                 continue
#             out.append(ln)
#         return "\n".join(out)

#     def _is_question_line(self, line: str) -> bool:
#         return bool(re.search(r"\?$", line) or re.search(r"^(có bao nhiêu|hãy|liệt kê|mô tả|tại sao)", line, re.I) or re.search(r"(là gì|như thế nào|ra sao)\?", line, re.I))

#     def _remove_unwanted_phrases(self, s: str) -> str:
#         patterns = [
#             r"dựa trên thông tin (trên|đã cung cấp),?\s*",
#             r"theo (thông tin|tài liệu),?\s*",
#             r"căn cứ vào,?\s*",
#             r"chúc.*?$",
#             r"rất mong.*?$",
#             r"cảm ơn.*?$",
#             r"xin chào.*?$",
#         ]
        
#         # Apply patterns for cleaning
#         for p in patterns:
#             s = re.sub(p, "", s, flags=re.I | re.M)
            
#         return s

#     def _format_response(self, s: str) -> str:
#         if not s:
#             return s
#         s = re.sub(r"\s+", " ", s)
#         s = re.sub(r"\n\s*\n+", "\n", s)
#         if s and s[0].islower():
#             s = s[0].upper() + s[1:]
#         s = re.sub(r"([.!?])([A-Z])", r"\1 \2", s)
#         s = re.sub(r"^(\d+)\.\s+", r"\1. ", s, flags=re.M)
#         return s

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
        logger.info(f"Generating response for query with {len(contexts)} contexts")

        messages = self.prompt_template.build_messages(query, contexts)
        raw_response = self.llm_client.generate(messages)

        # Áp dụng làm sạch chỉ khi câu trả lời không phải là câu trả lời cứng
        # Hoặc nếu prompt không phải là lời chào
        if "Tôi không tìm thấy thông tin phù hợp" not in raw_response and "Chào quý khách" not in raw_response:
            cleaned_response = self._clean_response(raw_response)
        else:
            cleaned_response = raw_response

        result = {
            "response": cleaned_response
        }
        logger.info("Response generated and cleaned successfully")
        return result

    def _clean_response(self, raw_response: str) -> str:
        text = raw_response.strip()
        # Áp dụng các hàm làm sạch theo thứ tự ưu tiên
        text = self._remove_generated_questions(text)
        text = self._remove_unwanted_phrases(text)
        text = self._format_response(text)
        return text.strip()

    def _remove_generated_questions(self, s: str) -> str:
        lines = [ln.strip() for ln in s.split("\n") if ln.strip()]
        out = []
        for ln in lines:
            if self._is_question_line(ln) or re.match(r"^[a-dA-D][).]", ln):
                continue
            out.append(ln)
        return "\n".join(out)

    def _is_question_line(self, line: str) -> bool:
        return bool(re.search(r"\?$", line) or re.search(r"^(có bao nhiêu|hãy|liệt kê|mô tả|tại sao)", line, re.I) or re.search(r"(là gì|như thế nào|ra sao)\?", line, re.I))

    def _remove_unwanted_phrases(self, s: str) -> str:
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
        for p in patterns:
            s = re.sub(p, "", s, flags=re.I | re.M)
            
        return s

    def _format_response(self, s: str) -> str:
        if not s:
            return s
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"\n\s*\n+", "\n", s)
        if s and s[0].islower():
            s = s[0].upper() + s[1:]
        s = re.sub(r"([.!?])([A-Z])", r"\1 \2", s)
        s = re.sub(r"^(\d+)\.\s+", r"\1. ", s, flags=re.M)
        return s