from openai import OpenAI
import re
import unicodedata

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

def replace_smart_chars(s: str) -> str:
    return "".join(SMART_MAP.get(ch, ch) for ch in s)

def remove_zero_width_and_controls(s: str) -> str:
    out = []
    for ch in s:
        if ch in ZERO_WIDTH:
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

def unescape_common_sequences(s: str) -> str:
    # Chỉ thay khi có backslash thật (\\n → \n). Nếu đã là newline thật thì không bị ảnh hưởng.
    s = s.replace("\\n", "\n")
    s = s.replace("\\t", "\t")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s

def normalize_spaces_and_punct(s: str) -> str:
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

def clean_text(s: str) -> str:
    if not s:
        return s
    # 1) Chuẩn hoá Unicode
    s = unicodedata.normalize("NFKC", s)
    # 2) Unescape các chuỗi thoát thường gặp
    s = unescape_common_sequences(s)
    # 3) Thay ký tự “thông minh” → ASCII
    s = replace_smart_chars(s)
    # 4) Bỏ zero-width, BOM, control chars (trừ \n, \t)
    s = remove_zero_width_and_controls(s)
    # 5) Chuẩn hoá khoảng trắng & dấu câu
    s = normalize_spaces_and_punct(s)
    return s



# Khởi tạo client (thay GEMINI_API_KEY bằng key của bạn)
client = OpenAI(
    api_key="AIzaSyBW9zyrIcNo6d3QSGx6eoMQNYgcCTbFmjw",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

messages = [
    {
        'role': 'system',
        'content': 'Bạn là trợ lý AI của Ngân hàng BIDV.\nCHỈ trả lời dựa trên phần "Thông tin từ tài liệu" do người dùng cung cấp trong mỗi lượt hỏi.\n\nQUY TẮC:\n- Nếu tài liệu không nêu rõ, hãy trả lời: "Tôi không tìm thấy thông tin phù hợp trong tài liệu được cung cấp."\n- Không thêm kiến thức ngoài tài liệu.\n- Ngôn ngữ: tiếng Việt, chuyên nghiệp, ngắn gọn.\n\nTRƯỜNG HỢP NGOẠI LỆ (không cần tài liệu):\n- Nếu người dùng chỉ CHÀO HỎI/CẢM ƠN/XÁC NHẬN ngắn (ví dụ: "hi", "xin chào", "ok", "cảm ơn"),\nhãy chào lại lịch sự và gợi ý 2–3 chủ đề có thể hỗ trợ. Không đưa số liệu/điều kiện nghiệp vụ.\n\nĐỊNH DẠNG:\n1) (Nếu cần) Ghi chú ngoại lệ/điều kiện áp dụng.'
    },
    {
        'role': 'user',
        'content': 'hi'
    }
]

def ask():

    clean_messages = []
    for msg in messages:
        clean_content = clean_text(msg['content'])
        clean_messages.append({'role': msg['role'], 'content': clean_content})
    print("Cleaned messages:", clean_messages)
    resp = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=clean_messages,           # giữ nguyên
        temperature=0.4,             # theo yêu cầu
        max_tokens=1200                # theo yêu cầu
    )
    print(resp.choices[0].message.content)

if __name__ == "__main__":
    ask()
