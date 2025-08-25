# Sử dụng Python 3.10 slim làm base image
FROM python:3.10-slim

# Đặt thư mục làm việc trong container
WORKDIR /app

# Cài đặt các dependencies cần thiết cho các thư viện
# Ví dụ: FAISS cần build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements.txt vào thư mục làm việc
COPY requirements.txt ./

# Cài đặt các thư viện Python từ requirements.txt
RUN pip install  -r requirements.txt

# Copy tất cả các file mã nguồn và tệp HTML vào container
COPY . .

# Mở cổng 8000 để ứng dụng FastAPI lắng nghe
EXPOSE 8000

# Chạy ứng dụng bằng Uvicorn khi container khởi động
# app_api:app - tham chiếu đến file app_api.py và đối tượng FastAPI được đặt tên là "app"
CMD ["uvicorn", "app_api:app", "--host", "0.0.0.0", "--port", "8000"]