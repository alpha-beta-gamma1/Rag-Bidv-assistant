from typing import List, Dict, Any
from src.utils.logger import setup_logger
logger = setup_logger(__name__)

class PromptTemplate:
    def __init__(self):
        self.system_message = """Bạn là trợ lý AI chuyên tư vấn ngân hàng BIDV. 
        Hãy trả lời câu hỏi một cách trực tiếp, chính xác và chuyên nghiệp.

        QUAN TRỌNG:
        - Trả lời trực tiếp câu hỏi, KHÔNG tạo câu hỏi trắc nghiệm.
        - Sử dụng CHÍNH XÁC thông tin từ tài liệu được cung cấp.
        - Nếu có nhiều mức lãi suất, liệt kê rõ ràng theo kỳ hạn trong định dạng bảng hoặc danh sách.
        - Đưa ra con số cụ thể và điều kiện áp dụng.
        - Nếu không tìm thấy thông tin cụ thể, trả lời: "Hiện tại, tôi không có thông tin chi tiết về [chủ đề]. Vui lòng liên hệ BIDV hoặc truy cập website chính thức để biết thêm chi tiết."
        - Nếu có chunk không liên quan (ví dụ: về vay vốn thay vì tiết kiệm), bỏ qua và ưu tiên chunk có tiêu đề hoặc nội dung phù hợp với truy vấn.

        Format trả lời:
        1. Trả lời trực tiếp câu hỏi dựa theo thông tin từ tài liệu.

        """

    def create_prompt(self, query: str, contexts: List[Dict[str, Any]]) -> str:
        """Create prompt for RAG generation"""
        max_prompt_length = 4000  # Giới hạn ký tự (tùy thuộc vào LLM)
        
        if not contexts:
            return f"""
            {self.system_message}

            Câu hỏi: {query}

            Thông tin từ tài liệu: Không tìm thấy thông tin phù hợp.

            Trả lời:"""

        # Format contexts
        context_text = ""
        for i, context in enumerate(sorted(contexts, key=lambda x: x.get('retrieval_score', 0), reverse=True)[:5], 1):
            title = context.get('title', 'Không có tiêu đề')
            content = context.get('content', '')
            score = context.get('retrieval_score', 0)
            
            context_text += f"""
            Đoạn {i} (Độ liên quan: {score:.2f}):
            Tiêu đề: {title}
            Nội dung: {content}
            ---"""

        prompt = f"""
        {self.system_message}

        Câu hỏi: {query}

        Thông tin từ tài liệu:
        {context_text}

        Dựa trên thông tin trên, hãy trả lời câu hỏi một cách chính xác và đầy đủ:"""
        
        # Kiểm tra độ dài prompt
        if len(prompt) > max_prompt_length:
            logger.warning("Prompt length exceeds limit, truncating...")
            prompt = prompt[:max_prompt_length] + "..."
        
        return prompt