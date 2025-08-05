import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from typing import List, Dict, Any
import time
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class LLMClient:
    def __init__(self, config: Config):
        """Khởi tạo LLMClient với cấu hình từ config."""
        self.model_name = config.get('models.llm_model', 'Qwen/Qwen2.5-1.5B-Instruct')
        self.device = 'cuda' if torch.cuda.is_available() and config.get('models.device', 'cpu') == 'cuda' else 'cpu'
        self.max_new_tokens = config.get('generation.max_new_tokens', 512)
        self.temperature = config.get('generation.temperature', 0.7)
        self.do_sample = config.get('generation.do_sample', True)
        
        logger.info(f"Khởi tạo LLMClient với mô hình: {self.model_name}, thiết bị: {self.device}")
        
        try:
            # Ghi lại thời gian tải mô hình
            start_time = time.time()
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Đảm bảo pad_token_id hợp lệ
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
                logger.info("Đã gán pad_token_id từ eos_token_id")
            
            # Load mô hình
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                device_map='auto' if self.device == 'cuda' else None,
                trust_remote_code=True
            )
            
            # Chuyển mô hình sang chế độ đánh giá
            self.model.eval()
            
            # Tạo pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == 'cuda' else -1
            )
            
            logger.info(f"Tải mô hình thành công trong {time.time() - start_time:.2f} giây")
        
        except (RuntimeError, ValueError) as e:
            logger.error(f"Lỗi khi tải mô hình: {e}")
            raise
    
    def generate(self, prompt: str, language: str = 'vi') -> str:
        """Tạo phản hồi từ prompt với hỗ trợ đa ngôn ngữ cho thông báo lỗi."""
        error_msgs = {
            'vi': "Xin lỗi, tôi không thể tạo câu trả lời cho câu hỏi này.",
            'en': "Sorry, I couldn't generate a response for this query."
        }
        
        try:
            with torch.no_grad():  # Tối ưu bộ nhớ
                outputs = self.pipeline(
                    prompt,
                    max_new_tokens=self.max_new_tokens,
                    temperature=self.temperature,
                    do_sample=self.do_sample,
                    pad_token_id=self.tokenizer.pad_token_id,
                    return_full_text=False
                )
                
                response = outputs[0]['generated_text'].strip()
                logger.info(f"Đã tạo phản hồi cho prompt dài {len(prompt)} ký tự")
                return response
                
        except (RuntimeError, ValueError) as e:
            logger.error(f"Lỗi khi tạo phản hồi: {e}")
            return error_msgs.get(language, error_msgs['vi'])