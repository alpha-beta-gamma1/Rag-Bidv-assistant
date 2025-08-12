from textwrap import dedent
from typing import List
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class PromptTemplate:
    def __init__(self):
        self.system_message = (
    "Bạn là trợ lý AI của BIDV. Nhiệm vụ: trả lời dựa DUY NHẤT vào mục 'Thông tin từ tài liệu' được cung cấp.\n"
    "QUY TẮC:\n"
    "1) Ưu tiên trả lời NGẮN GỌN, TRỰC TIẾP (2–5 câu hoặc gạch đầu dòng).\n"
    "2) CHỈ dùng thông tin trong ngữ cảnh; KHÔNG suy đoán/ngoại suy.\n"
    "3) Nếu không có dữ liệu khớp câu hỏi: nói 'Không tìm thấy thông tin phù hợp.'\n"
    "4) Nêu con số/ngày tháng kèm đơn vị & phạm vi áp dụng nếu tài liệu có.\n"
    "5) Không dùng thuật ngữ nội bộ hoặc viết tắt mơ hồ; nếu buộc phải dùng, giải thích ngắn trong ngoặc.\n"
    "6) Không chào hỏi, không lời chúc, không thêm câu hỏi ngược.\n"
    "7) Nếu có dữ liệu gần nhất nhưng không trùng khớp: báo rõ là 'Thông tin liên quan gần nhất' rồi mới nêu.\n"
    "ĐỊNH DẠNG TRẢ LỜI:\n"
    "- Dòng 1: câu trả lời cô đọng nhất.\n"
    "- Sau đó (tuỳ cần): 2–4 gạch đầu dòng chi tiết quan trọng, mỗi gạch ≤ 20 từ.\n"
    "- Nếu là thông tin liên quan gần nhất: đặt nhãn [Liên quan gần nhất]."
)

        self.max_chars = 4000

    def build_messages(self, query: str, contexts: List[str]):
        """Return OpenAI-style messages: [system, user]."""
        if not contexts:
            user = dedent(f"""
                Câu hỏi: {query}
                Thông tin từ tài liệu: Không tìm thấy thông tin phù hợp.
                Trả lời:
            """)
            return [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user.strip()},
            ]

        # keep up to 3 chunks; trim length defensively
        blocks = []
        for i, c in enumerate(contexts[:3], 1):
            c = (c or "").strip()
            if not c:
                continue
            blocks.append(f"Đoạn {i}: {c}")
        context_text = "\n".join(blocks)

        user = dedent(f"""
            Câu hỏi: {query}

            Thông tin từ tài liệu:
            {context_text}

            Dựa trên thông tin trên, hãy trả lời chính xác và đầy đủ:
        """)
        msg = user.strip()
        if len(msg) > self.max_chars:
            logger.warning("Prompt length exceeds limit, truncating...")
            msg = msg[: self.max_chars] + "..."
        return [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": msg},
        ]

    # Backward-compatible helper if callers still expect a string
    def create_prompt(self, query: str, contexts: List[str]) -> str:
        messages = self.build_messages(query, contexts)
        # Flatten to a single string for legacy callers
        sys = messages[0]["content"]
        usr = messages[1]["content"]
        return f"{sys}\n\n{usr}"