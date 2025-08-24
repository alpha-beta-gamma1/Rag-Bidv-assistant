from textwrap import dedent
from typing import List
from src.utils.logger import setup_logger
import re

logger = setup_logger(__name__)

class PromptTemplate:
    def __init__(self):
        # Enhanced system message với better instructions
        self.system_message = dedent("""
            Bạn là Trợ lý AI chuyên nghiệp của Ngân hàng BIDV.

            ## NGUYÊN TẮC GIAO TIẾP

            - Xưng hô bằng “Quý khách hàng” đối với user.
            - Ngôn ngữ: Tiếng Việt, chuyên nghiệp, ngắn gọn, trung lập.

            ## PHẠM VI THÔNG TIN
            - Chỉ trả lời dựa trên TÀI LIỆU được cung cấp.
            - Không suy đoán, không dùng nguồn ngoài.
            - Nếu TÀI LIỆU không có đủ dữ liệu: chỉ trả lời  
            → “Quý khách vui lòng liên hệ chi nhánh để được tư vấn chi tiết.”

            ## QUY TẮC NỘI DUNG
            - Trả lời đúng trọng tâm câu hỏi.
            """).strip()


        self.max_chars = 4000

        # Patterns cho greeting detection
        self.greeting_patterns = [
            re.compile(r"^(chào|xin chào|hello|hi|hê lô)\b", re.IGNORECASE),
            re.compile(r"^(tôi cần hỗ trợ|cần giúp đỡ|giúp tôi|hỗ trợ)\b", re.IGNORECASE),
            re.compile(r"^(bạn là ai|bạn có thể làm gì)\b", re.IGNORECASE),
        ]
        self.simple_patterns = [
            re.compile(r"\bcảm ơn\b", re.IGNORECASE),
            re.compile(r"\bthank you\b", re.IGNORECASE),
            re.compile(r"^ok\b", re.IGNORECASE),
            re.compile(r"\bđược rồi\b", re.IGNORECASE),
            re.compile(r"\btạm biệt\b|\bbye\b", re.IGNORECASE),
        ]

        # Stopwords cho deduplication
        self._stop = set("và hoặc là của các những được từ cho với tại trên dưới trong khi nếu hoặc hay một số".split())

    def _is_greeting(self, query: str) -> bool:
        q = (query or "").strip().lower()
        return any(pat.match(q) for pat in self.greeting_patterns)

    def _is_simple_query(self, query: str) -> bool:
        q = (query or "").strip().lower()
        return any(pat.search(q) for pat in self.simple_patterns)

    def _enhanced_clean_context(self, text: str) -> str:
        """Enhanced context cleaning."""
        if not text:
            return ""
        
        t = text
        
        # Remove citations
        t = re.sub(r"\[\s*\d+\s*\]", " ", t)
        t = re.sub(r"\(\s*\d+\s*\)", " ", t)
        
        # Remove standalone reference numbers (careful with years)
        t = re.sub(r"(?:(?<=\s)|(?<=\.|,|;|:))\d{1,2}(?=\s|$)", " ", t)
        
        # Better space normalization
        t = re.sub(r"[ \t]+", " ", t)
        t = re.sub(r"\s+([,.;:%\)\?])", r"\1", t)
        t = re.sub(r"(\()\s+", r"\1", t)
        
        # Better line break handling
        t = re.sub(r"\n{3,}", "\n\n", t)
        t = "\n".join(ln.rstrip() for ln in t.splitlines())
        
        return t.strip()

    def _tokenize(self, s: str) -> List[str]:
        return [w for w in re.findall(r"\w+", s.lower()) if w not in self._stop]

    def _similarity_score(self, a: str, b: str) -> float:
        """Improved similarity calculation."""
        ta, tb = set(self._tokenize(a)), set(self._tokenize(b))
        if not ta or not tb:
            return 0.0
        
        intersection = len(ta & tb)
        union = len(ta | tb)
        
        # Jaccard + length penalty cho contexts quá khác biệt về độ dài
        jaccard = intersection / union
        len_ratio = min(len(ta), len(tb)) / max(len(ta), len(tb))
        
        return jaccard * (0.7 + 0.3 * len_ratio)  # Weight by length similarity

    def _optimize_context(self, contexts: List[str]) -> List[str]:
        """Enhanced context optimization."""
        if not contexts:
            return []

        # Clean all contexts first
        cleaned = []
        for ctx in contexts[:5]:  # Limit input contexts
            clean_ctx = self._enhanced_clean_context(ctx)
            if clean_ctx and len(clean_ctx.strip()) > 20:  # Filter too short
                cleaned.append(clean_ctx)

        # Enhanced deduplication
        unique = []
        for ctx in cleaned:
            # Check similarity with existing contexts
            is_duplicate = any(
                self._similarity_score(ctx, existing) > 0.75 
                for existing in unique
            )
            
            if not is_duplicate:
                unique.append(ctx)
                
            if len(unique) >= 3:  # Max 3 contexts
                break

        return unique

    def build_messages(self, query: str, contexts: List[str]) -> List[dict]:
        """Enhanced message building."""
        query = (query or "").strip()

        # Handle greetings
        if self._is_greeting(query):
            return [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": query}
            ]

        # Handle simple acknowledgments
        if self._is_simple_query(query):
            return [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": query}
            ]

        # Optimize contexts
        optimized = self._optimize_context(contexts)

        # Build user message với better structure
        if not optimized:
            user_content = dedent(f"""\
                CÂU HỎI: {query}

                THÔNG TIN TÀI LIỆU: Không có thông tin liên quan

                Hãy trả lời theo quy tắc khi thiếu thông tin.
            """).strip()
        else:
            # Better context formatting
            context_blocks = []
            for i, ctx in enumerate(optimized, 1):
                # Smart truncation - keep important parts
                if len(ctx) > 600:
                    # Try to truncate at sentence boundary
                    truncated = ctx[:600]
                    last_period = truncated.rfind('.')
                    if last_period > 400:  # If we can find a good break point
                        ctx = truncated[:last_period + 1] + "..."
                    else:
                        ctx = truncated.rstrip() + "..."
                
                context_blocks.append(f"[Nguồn {i}]: {ctx}")
            
            context_text = "\n\n".join(context_blocks)
            
            user_content = dedent(f"""\
                CÂU HỎI: {query}

                THÔNG TIN TÀI LIỆU BIDV:
                {context_text}

                Trả lời theo ĐỊNH DẠNG CHUẨN. Tập trung vào thông tin quan trọng nhất cho câu hỏi.
            """).strip()

        # Length safety check
        if len(user_content) > self.max_chars:
            logger.warning("Prompt length (%d) exceeds limit, truncating...", len(user_content))
            
            # Smart truncation strategy
            header = f"CÂU HỎI: {query}\n\nTHÔNG TIN TÀI LIỆU BIDV:\n"
            footer = "\n\nTrả lời theo ĐỊNH DẠNG CHUẨN, tập trung vào thông tin quan trọng nhất."
            
            available_space = self.max_chars - len(header) - len(footer) - 50
            
            if optimized:
                # Truncate contexts proportionally
                total_ctx_len = sum(len(ctx) for ctx in optimized)
                truncated_contexts = []
                
                for i, ctx in enumerate(optimized):
                    target_len = int((len(ctx) / total_ctx_len) * available_space)
                    target_len = max(100, min(target_len, len(ctx)))  # Min 100, max original
                    
                    if len(ctx) > target_len:
                        ctx = ctx[:target_len].rstrip() + "..."
                    
                    truncated_contexts.append(f"[Nguồn {i+1}]: {ctx}")
                
                context_text = "\n\n".join(truncated_contexts)
            else:
                context_text = "Không có thông tin liên quan"
            
            user_content = header + context_text + footer

        return [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": user_content}
        ]

    def create_prompt(self, query: str, contexts: List[str]) -> str:
        """Backward compatibility method."""
        messages = self.build_messages(query, contexts)
        if len(messages) == 3:
            return f"{messages[0]['content']}\n\nUser: {messages[1]['content']}\nAssistant: {messages[2]['content']}"
        else:
            return f"{messages[0]['content']}\n\n{messages[1]['content']}"