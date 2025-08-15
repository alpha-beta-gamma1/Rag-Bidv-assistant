# import os
# import time
# import torch
# from typing import List, Dict, Any, Union, Optional
# from transformers import AutoModelForCausalLM, AutoTokenizer
# from dotenv import load_dotenv
# from src.utils.logger import setup_logger

# logger = setup_logger(__name__)

# class LocalQwenLLMClient:
#     """Local Qwen client using Transformers library."""
    
#     def __init__(self, config):
#         load_dotenv()
        
#         # Model configuration
#         self.model_name = config.get("models.llm_model", "Qwen/Qwen3-0.6B")
#         self.max_tokens = int(config.get("generation.max_new_tokens", 512))
#         self.temperature = float(config.get("generation.temperature", 0.4))
#         self.top_p = float(config.get("generation.top_p", 0.9))
#         self.do_sample = self.temperature > 0.0
#         self.enable_thinking = bool(config.get("generation.enable_thinking", True))
        
#         # Device configuration
#         self.device = self._get_device()
#         logger.info(f"Using device: {self.device}")
        
#         # Load model and tokenizer
#         t0 = time.time()
#         self._load_model()
#         logger.info(f"Qwen model loaded in {time.time()-t0:.2f}s | model={self.model_name}")

#     def _get_device(self) -> str:
#         """Determine the best device to use."""
#         if torch.cuda.is_available():
#             return "cuda"
#         elif torch.backends.mps.is_available():  # For Apple Silicon
#             return "mps"
#         else:
#             return "cpu"

#     def _load_model(self):
#         """Load the tokenizer and model."""
#         try:
#             logger.info(f"Loading tokenizer from {self.model_name}...")
#             self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
#             logger.info(f"Loading model from {self.model_name}...")
#             self.model = AutoModelForCausalLM.from_pretrained(
#                 self.model_name,
#                 torch_dtype="auto",
#                 device_map="auto" if self.device == "cuda" else None,
#                 trust_remote_code=True  # Required for some Qwen models
#             )
            
#             # Move to device if not using device_map
#             if self.device != "cuda":
#                 self.model = self.model.to(self.device)
                
#         except Exception as e:
#             logger.error(f"Failed to load model: {e}")
#             raise RuntimeError(f"Could not load Qwen model: {e}")

#     def _parse_thinking_content(self, output_ids: List[int]) -> tuple:
#         """Parse thinking content from output tokens."""
#         try:
#             # Find the last occurrence of 151668 (</think>) token
#             index = len(output_ids) - output_ids[::-1].index(151668)
#         except ValueError:
#             # No thinking token found
#             index = 0
            
#         thinking_content = self.tokenizer.decode(
#             output_ids[:index], 
#             skip_special_tokens=True
#         ).strip("\n")
        
#         content = self.tokenizer.decode(
#             output_ids[index:], 
#             skip_special_tokens=True
#         ).strip("\n")
        
#         return thinking_content, content

#     def generate(self, prompt_or_messages: Union[str, List[Dict[str, str]]], language: str = "vi") -> str:
#         """Generate response using the local Qwen model."""
#         fallback = "Xin lỗi, tôi không thể tạo câu trả lời cho câu hỏi này." if language == "vi" else "Sorry, I couldn't generate a response for this query."
        
#         try:
#             # Convert string prompt to message format
#             if isinstance(prompt_or_messages, str):
#                 messages = [{"role": "user", "content": prompt_or_messages}]
#             else:
#                 messages = prompt_or_messages

#             # Apply chat template
#             text = self.tokenizer.apply_chat_template(
#                 messages,
#                 tokenize=False,
#                 add_generation_prompt=True,
#                 enable_thinking=self.enable_thinking
#             )

#             # Tokenize input
#             model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            
#             # Generate response
#             with torch.no_grad():
#                 generated_ids = self.model.generate(
#                     **model_inputs,
#                     max_new_tokens=self.max_tokens,
#                     temperature=self.temperature if self.do_sample else None,
#                     top_p=self.top_p if self.do_sample else None,
#                     do_sample=self.do_sample,
#                     pad_token_id=self.tokenizer.eos_token_id,
#                     repetition_penalty=1.1,
#                 )

#             # Extract only the new tokens (response)
#             output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
            
#             if self.enable_thinking:
#                 # Parse thinking and content separately
#                 thinking_content, content = self._parse_thinking_content(output_ids)
                
#                 # Log thinking content for debugging (optional)
#                 if thinking_content:
#                     logger.debug(f"Thinking content: {thinking_content[:100]}...")
                
#                 return content.strip() or fallback
#             else:
#                 # Direct decode without thinking parsing
#                 response = self.tokenizer.decode(output_ids, skip_special_tokens=True)
#                 return response.strip() or fallback
                
#         except Exception as e:
#             logger.error(f"Error generating response with local Qwen: {e}")
#             return fallback

#     def __del__(self):
#         """Cleanup GPU memory when client is destroyed."""
#         try:
#             if hasattr(self, 'model'):
#                 del self.model
#             if torch.cuda.is_available():
#                 torch.cuda.empty_cache()
#         except Exception as e:
#             logger.warning(f"Error during cleanup: {e}")

import os
import time
from typing import List, Dict, Any, Union, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI
from dotenv import load_dotenv
from src.utils.logger import setup_logger
from openai.types.chat import ChatCompletion

logger = setup_logger(__name__)

class GeminiLLMClient:
    """OpenAI-compatible client for Google AI Studio (Gemini)."""
    def __init__(self, config):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY") or config.get("providers.gemini.api_key")
        base_url = os.getenv("GEMINI_BASE_URL")
        if not api_key:
            raise RuntimeError("Thiếu GEMINI_API_KEY")

        self.model_name = config.get("models.llm_model", "gemini-2.5-flash")
        self.max_tokens = int(config.get("generation.max_new_tokens", 512))
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
        # Chỉ thử lại đối với các lỗi liên quan đến kết nối hoặc rate limit
        retry=retry_if_exception_type((
            Exception,
            # Thêm các loại lỗi cụ thể của thư viện OpenAI nếu có
        )),
    )
    def _call_completion(self, messages: List[Dict[str, str]]) -> Union[ChatCompletion, Any]:
        """Gọi API chat completion với cơ chế retry."""
        try:
            return self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                stream=self.stream,
            )
        except Exception as e:
            logger.error(f"Lỗi khi gọi API Gemini: {e}")
            raise # Re-raise để tenacity xử lý

    def generate(self, prompt_or_messages: Union[str, List[Dict[str, str]]], language: str = "vi") -> str:
        fallback = "Xin lỗi, tôi không thể tạo câu trả lời cho câu hỏi này." if language == "vi" else "Sorry, I couldn't generate a response for this query."
        try:
            if isinstance(prompt_or_messages, str):
                messages = [{"role": "user", "content": prompt_or_messages}]
            else:
                messages = prompt_or_messages

            resp = self._call_completion(messages)

            if self.stream:
                full_text = []
                for chunk in resp:
                    delta = getattr(chunk.choices[0].delta, "content", None)
                    if delta:
                        full_text.append(delta)
                return ("".join(full_text)).strip() or fallback
            else:
                return (resp.choices[0].message.content or "").strip() or fallback
        except Exception as e:
            logger.error(f"Lỗi nghiêm trọng khi gọi Gemini sau khi retry: {e}")
            return fallback
