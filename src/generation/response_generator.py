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
        #cleaned_response = self._clean_response(raw_response)

        result = {
            #"query": query,
            "response": raw_response,
            # "contexts": contexts,
            # "metadata": {
            #     "num_contexts": len(contexts),
            #     "prompt_length": sum(len(m.get("content", "")) for m in messages),
            #     "raw_response_length": len(raw_response),
            #     "cleaned_response_length": len(cleaned_response),
            # },
        }
        logger.info("Response generated and cleaned successfully")
        return result

    def _clean_response(self, raw_response: str) -> str:
        text = raw_response.strip()
        text = self._remove_generated_questions(text)
        text = self._extract_main_content(text)
        text = self._remove_unwanted_phrases(text)
        text = self._format_response(text)
        return text.strip()

    def _remove_generated_questions(self, s: str) -> str:
        lines = [ln.strip() for ln in s.split("\n") if ln.strip()]
        out = []
        for ln in lines:
            if self._is_question_line(ln):
                continue
            if re.match(r"^[a-dA-D][).]", ln):
                continue
            out.append(ln)
        return "\n".join(out)

    def _is_question_line(self, line: str) -> bool:
        return bool(re.search(r"\?$", line) or re.search(r"^(có bao nhiêu|hãy|liệt kê|mô tả|tại sao)", line, re.I) or re.search(r"(là gì|như thế nào|ra sao)\?", line, re.I))

    def _extract_main_content(self, s: str) -> str:
        for p in [r"kết quả trả lời:?\s*(.+)", r"trả lời:?\s*(.+)", r"đáp án:?\s*(.+)"]:
            m = re.search(p, s, re.I | re.S)
            if m:
                return m.group(1).strip()
        return s

    def _remove_unwanted_phrases(self, s: str) -> str:
        patterns = [
            r"dựa trên thông tin (trên|đã cung cấp),?\s*",
            r"theo (thông tin|tài liệu),?\s*",
            r"căn cứ vào,?\s*",
            r"chúc.*?(thành công|may mắn|tốt lành)!?$",
            r"rất mong.*?ủng hộ!?$",
            r"cảm ơn.*?$",
            r"xin chào.*?$",
        ]
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