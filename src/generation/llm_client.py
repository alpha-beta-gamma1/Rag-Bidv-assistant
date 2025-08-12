import os
import time
from typing import List, Dict, Any, Union, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI
from dotenv import load_dotenv
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class GeminiLLMClient:
    """OpenAI-compatible client for Google AI Studio (Gemini).
    - Reads GEMINI_API_KEY + GEMINI_BASE_URL from env (with sane defaults)
    - Accepts either a prompt string OR OpenAI-style messages
    - Optional streaming (config: generation.stream)
    - Retries on transient HTTP/RateLimit errors
    """
    def __init__(self, config):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY") or config.get("providers.gemini.api_key")
        base_url = os.getenv("GEMINI_BASE_URL")
        if not api_key:
            raise RuntimeError("Thiếu GEMINI_API_KEY")

        # Model & generation params
        self.model_name = config.get("models.llm_model", "gemini-2.5-flash")
        self.max_tokens = int(config.get("generation.max_new_tokens", 512))  # normalize name
        self.temperature = float(config.get("generation.temperature", 0.4))
        self.top_p = float(config.get("generation.top_p", 0.9))
        self.stream = bool(config.get("generation.stream", False))
        self.timeout = int(config.get("generation.timeout_sec", 60))

        t0 = time.time()
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=self.timeout)
        logger.info(f"Gemini client ready in {time.time()-t0:.2f}s | model={self.model_name}")

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.0, min=1, max=8),
        retry=retry_if_exception_type(Exception),
    )
    def _call_completion(self, messages: List[Dict[str, str]]):
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stream=self.stream,
        )

    def generate(self, prompt_or_messages: Union[str, List[Dict[str, str]]], language: str = "vi") -> str:
        fallback = (
            "Xin lỗi, tôi không thể tạo câu trả lời cho câu hỏi này." if language == "vi"
            else "Sorry, I couldn't generate a response for this query."
        )
        try:
            if isinstance(prompt_or_messages, str):
                messages = [{"role": "user", "content": prompt_or_messages}]
            else:
                messages = prompt_or_messages

            resp = self._call_completion(messages)

            if self.stream:
                # Collect streamed chunks into a single string
                full_text = []
                for chunk in resp:  # type: ignore[union-attr]
                    delta = getattr(chunk.choices[0].delta, "content", None)
                    if delta:
                        full_text.append(delta)
                return ("".join(full_text)).strip() or fallback

            return (resp.choices[0].message.content or "").strip() or fallback
        except Exception as e:
            logger.error(f"Lỗi gọi Gemini: {e}")
            return fallback