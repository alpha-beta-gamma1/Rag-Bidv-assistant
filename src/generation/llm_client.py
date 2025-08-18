import os
import time
import re
import unicodedata
from typing import List, Dict, Any, Union
from openai import OpenAI
from dotenv import load_dotenv
from src.utils.logger import setup_logger
from openai.types.chat import ChatCompletion

logger = setup_logger(__name__)

def _cfg(d: Any, path: str, default: Any = None) -> Any:
    """Safe dotted-get cho dict config."""
    cur = d
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur

class TextCleaner:
    """Class để làm sạch văn bản trước khi gửi tới LLM."""
    
    SMART_MAP = {
        "\u2018": "'", "\u2019": "'", "\u201A": "'", "\u201B": "'",
        "\u201C": '"', "\u201D": '"', "\u201E": '"',
        "\u2013": "-", "\u2014": "-", "\u2212": "-",  # en/em dash, minus
        "\u00A0": " ",  # non-breaking space
        "\u2026": "..." # ellipsis
    }
    
    ZERO_WIDTH = {
        "\u200B", "\u200C", "\u200D", "\u2060", "\uFEFF"  # ZWSP, ZWNJ, ZWJ, WJ, BOM
    }
    
    @classmethod
    def replace_smart_chars(cls, s: str) -> str:
        """Thay thế các ký tự thông minh bằng ASCII tương đương."""
        return "".join(cls.SMART_MAP.get(ch, ch) for ch in s)
    
    @classmethod
    def remove_zero_width_and_controls(cls, s: str) -> str:
        """Xóa zero-width chars và control chars, giữ lại \n, \t."""
        out = []
        for ch in s:
            if ch in cls.ZERO_WIDTH:
                continue
            cat = unicodedata.category(ch)
            # Bỏ control chars (Cc) và format (Cf), nhưng giữ \n, \t thủ công
            if ch in ("\n", "\t"):
                out.append(ch)
            elif cat in ("Cc", "Cf"):
                continue
            else:
                out.append(ch)
        return "".join(out)
    
    @classmethod
    def unescape_common_sequences(cls, s: str) -> str:
        """Unescape các chuỗi thoát thường gặp."""
        # Chỉ thay khi có backslash thật (\\n → \n). Nếu đã là newline thật thì không bị ảnh hưởng.
        s = s.replace("\\n", "\n")
        s = s.replace("\\t", "\t")
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        return s
    
    @classmethod
    def normalize_spaces_and_punct(cls, s: str) -> str:
        """Chuẩn hóa khoảng trắng và dấu câu."""
        # Nén nhiều khoảng trắng
        s = re.sub(r"[ \t]+", " ", s)
        # Xoá khoảng trắng trước dấu câu , . ; : % ) ?
        s = re.sub(r"\s+([,.;:%\)\?])", r"\1", s)
        # Xoá khoảng trắng sau ( và trước mở ngoặc
        s = re.sub(r"(\()\s+", r"\1", s)
        # Chuẩn hoá dòng trống: tối đa 1 dòng trống liên tiếp
        s = re.sub(r"\n{3,}", "\n\n", s)
        # Trim từng dòng
        s = "\n".join(ln.rstrip() for ln in s.splitlines())
        return s.strip()
    
    @classmethod
    def clean_text(cls, s: str) -> str:
        """Làm sạch văn bản hoàn chỉnh."""
        if not s:
            return s
        # 1) Chuẩn hoá Unicode
        s = unicodedata.normalize("NFKC", s)
        # 2) Unescape các chuỗi thoát thường gặp
        s = cls.unescape_common_sequences(s)
        # 3) Thay ký tự "thông minh" → ASCII
        s = cls.replace_smart_chars(s)
        # 4) Bỏ zero-width, BOM, control chars (trừ \n, \t)
        s = cls.remove_zero_width_and_controls(s)
        # 5) Chuẩn hoá khoảng trắng & dấu câu
        s = cls.normalize_spaces_and_punct(s)
        return s

class GeminiLLMClient:
    """OpenAI-compatible client for Google AI Studio (Gemini)."""
    def __init__(self, config: Dict[str, Any]):
        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY") or _cfg(config, "providers.gemini.GEMINI_API_KEY")
        base_url = os.getenv("GEMINI_BASE_URL") or _cfg(config, "providers.gemini.GEMINI_BASE_URL")

        if not api_key:
            raise RuntimeError("Thiếu GEMINI_API_KEY")

        self.model_name = _cfg(config, "models.llm_model", "gemini-2.5-flash")
        self.max_tokens = int(_cfg(config, "generation.max_tokens", 1200))
        self.temperature = float(_cfg(config, "generation.temperature", 0.4))
        self.top_p = float(_cfg(config, "generation.top_p", 0.9))
        self.stream = bool(_cfg(config, "generation.stream", False))
        self.timeout = int(_cfg(config, "generation.timeout_sec", 60))

        # Khởi tạo text cleaner
        self.text_cleaner = TextCleaner()

        t0 = time.time()
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=self.timeout)
        logger.info(f"Gemini client ready in {time.time()-t0:.2f}s | model={self.model_name}")

    def _clean_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Làm sạch nội dung các messages trước khi gửi."""
        clean_messages = []
        for msg in messages:
            clean_content = self.text_cleaner.clean_text(msg['content'])
            clean_messages.append({'role': msg['role'], 'content': clean_content})
        return clean_messages

    def generate(self, prompt_or_messages: Union[str, List[Dict[str, str]]], language: str = "vi") -> str:
        """Sinh câu trả lời từ Gemini với text cleaning."""
        fallback = (
            "Xin lỗi, tôi không thể tạo câu trả lời cho câu hỏi này."
            if language == "vi"
            else "Sorry, I couldn't generate a response for this query."
        )
        try:
            if isinstance(prompt_or_messages, str):
                # Làm sạch prompt string
                clean_prompt = self.text_cleaner.clean_text(prompt_or_messages)
                messages = [{"role": "user", "content": clean_prompt}]
            else:
                # Làm sạch tất cả messages
                messages = self._clean_messages(prompt_or_messages)

            logger.debug(f"Cleaned messages: {messages}")

            # Tạo completion với streaming tùy thuộc vào config
            if self.stream:
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    stream=True
                )

                # Ghép các chunk content lại
                full_text = []
                for chunk in resp:
                    delta = getattr(chunk.choices[0].delta, "content", None)
                    if delta:
                        full_text.append(delta)

                return ("".join(full_text)).strip() or fallback
            else:
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    stream=False
                )
                
                return resp.choices[0].message.content.strip() or fallback

        except Exception as e:
            logger.error(f"Lỗi khi gọi Gemini: {e}")
            return fallback