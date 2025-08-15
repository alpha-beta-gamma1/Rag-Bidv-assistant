from textwrap import dedent
from typing import List
from src.utils.logger import setup_logger
import re

logger = setup_logger(__name__)

class PromptTemplate:
    def __init__(self):
        # System message đầy đủ quy tắc + định dạng
        self.system_message = dedent("""\
            Bạn là trợ lý AI của Ngân hàng BIDV.
            CHỈ trả lời dựa trên phần "Thông tin từ tài liệu" do người dùng cung cấp trong mỗi lượt hỏi.

            QUY TẮC:
            - Nếu tài liệu không nêu rõ, hãy trả lời: "Tôi không tìm thấy thông tin phù hợp trong tài liệu được cung cấp."
            - Không thêm kiến thức ngoài tài liệu. Bỏ qua ký hiệu chú thích/đánh số như (16), [1], ¹, ²...
            - Ưu tiên tính chính xác; nếu có khác biệt giữa chi nhánh/PGD, hãy ghi chú ngắn.
            - Ngôn ngữ: tiếng Việt, chuyên nghiệp, ngắn gọn.

            TRƯỜNG HỢP NGOẠI LỆ (không cần tài liệu):
            - Nếu người dùng chỉ CHÀO HỎI/CẢM ƠN/XÁC NHẬN ngắn (ví dụ: "hi", "xin chào", "ok", "cảm ơn"),
            hãy chào lại lịch sự và gợi ý 2–3 chủ đề có thể hỗ trợ. Không đưa số liệu/điều kiện nghiệp vụ.

            ĐỊNH DẠNG:
            1) Câu trả lời trực tiếp (1–2 câu).
            2) (Nếu cần) Ghi chú ngoại lệ/điều kiện áp dụng.
        """).strip()


        self.max_chars = 4000

        # Mẫu chào hỏi / acknowledgement
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

        # Stopwords rất gọn để dedup (đủ dùng cho kiểm trùng đơn giản)
        self._stop = set("và hoặc là của các những được từ cho với tại trên dưới trong khi nếu hoặc hay một số".split())

    # ---------- Helpers ----------
    def _is_greeting(self, query: str) -> bool:
        q = (query or "").strip().lower()
        return any(pat.match(q) for pat in self.greeting_patterns)

    def _is_simple_query(self, query: str) -> bool:
        q = (query or "").strip().lower()
        return any(pat.search(q) for pat in self.simple_patterns)

    def _clean_context(self, text: str) -> str:
        """Làm sạch: bỏ [1], (16), ký hiệu chú thích rời rạc; gộp khoảng trắng."""
        if not text:
            return ""
        t = text

        # Bỏ [n] và (n)
        t = re.sub(r"\[\s*\d+\s*\]", " ", t)
        t = re.sub(r"\(\s*\d+\s*\)", " ", t)

        # Bỏ số chú thích lẻ đứng độc lập sau dấu cách/dấu câu (hạn chế đụng năm như 2024)
        t = re.sub(r"(?:(?<=\s)|(?<=\.|,|;|:))\d{1,2}(?=\s|$)", " ", t)

        # Gộp khoảng trắng
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _tokenize(self, s: str) -> List[str]:
        return [w for w in re.findall(r"\w+", s.lower()) if w not in self._stop]

    def _similar(self, a: str, b: str) -> float:
        ta, tb = set(self._tokenize(a)), set(self._tokenize(b))
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def _optimize_context(self, contexts: List[str]) -> List[str]:
        """Làm sạch + khử trùng lặp đơn giản (giữ thứ tự), lấy tối đa 3 đoạn."""
        if not contexts:
            return []

        cleaned = [self._clean_context(c) for c in contexts if c and c.strip()]
        unique = []
        for c in cleaned:
            if not c:
                continue
            if all(self._similar(c, u) <= 0.8 for u in unique):
                unique.append(c)
            if len(unique) >= 3:
                break
        return unique

    # ---------- Public API ----------
    def build_messages(self, query: str, contexts: List[str]) -> List[dict]:
        """Trả về danh sách messages theo chuẩn chat-completions."""
        query = (query or "").strip()

        # 1) Đường tắt cho chào hỏi -> để LLM chào theo system
        if self._is_greeting(query):
            user = dedent(f"""\
                Người dùng gửi lời chào: "{query}"
                Nhiệm vụ:
                - Chào lại lịch sự (1 câu, xưng "tôi").
                - Giới thiệu rất ngắn 1 câu về những gì tôi có thể hỗ trợ (không nêu số liệu/điều kiện nghiệp vụ).
                - Đưa 2–3 gợi ý câu hỏi mẫu dạng gạch đầu dòng (ví dụ: lãi suất, phí, mở thẻ).
            """).strip()
            return [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user},
            ]


        # 2) Acknowledgement ngắn
        if self._is_simple_query(query):
            user = dedent(f"""\
                Câu hỏi/Thông điệp: {query}
                Hãy phản hồi lịch sự, ngắn gọn (1 câu).
            """).strip()
            return [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user},
            ]

        # 3) Tối ưu context
        optimized = self._optimize_context(contexts)

        # 4) Không có context → yêu cầu nói "không tìm thấy"
        if not optimized:
            user = dedent(f"""\
                Câu hỏi của khách hàng: {query}

                Thông tin từ tài liệu:
                (Không có)

                Nếu thiếu thông tin, hãy trả lời đúng quy tắc: 
                "Tôi không tìm thấy thông tin phù hợp trong tài liệu được cung cấp."
            """).strip()
            return [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": user},
            ]

        # 5) Ghép context có cấu trúc
        blocks, total_len = [], 0
        for i, c in enumerate(optimized, 1):
            # cắt từng đoạn nếu quá dài, ưu tiên giữ đầu đoạn
            part = c if len(c) <= 800 else (c[:800].rstrip() + " …")
            seg = f"Đoạn {i}: {part}"
            blocks.append(seg)
            total_len += len(seg)

        context_text = "\n\n".join(blocks)

        user = dedent(f"""\
            Câu hỏi của khách hàng: {query}

            Thông tin từ tài liệu BIDV:
            {context_text}

            Hãy phân tích và trả lời đúng trọng tâm theo ĐỊNH DẠNG trong system.
        """).strip()

        # 6) Bảo hiểm độ dài (char ≠ token nhưng đủ an toàn cơ bản)
        if len(user) > self.max_chars:
            logger.warning("Prompt length (%d) exceeds limit (%d), truncating contexts...", len(user), self.max_chars)
            head = dedent(f"""\
                Câu hỏi của khách hàng: {query}

                Thông tin từ tài liệu BIDV:
            """).strip()
            budget = max(200, self.max_chars - len(head) - 150)
            ctx = (context_text[:budget] + "\n[…đã cắt bớt do giới hạn độ dài…]").strip()
            user = dedent(f"""\
                {head}
                {ctx}

                Hãy trả lời đúng trọng tâm theo ĐỊNH DẠNG trong system.
            """).strip()

        return [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": user},
        ]

    # Backward compatibility (giữ nguyên hành vi cũ)
    def create_prompt(self, query: str, contexts: List[str]) -> str:
        messages = self.build_messages(query, contexts)
        if len(messages) == 3:  # trường hợp có assistant trong pipeline khác (giữ logic cũ nếu cần)
            return f"{messages[0]['content']}\n\nUser: {messages[1]['content']}\nAssistant: {messages[2]['content']}"
        else:
            return f"{messages[0]['content']}\n\n{messages[1]['content']}"
