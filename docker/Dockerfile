# --- builder ---
FROM python:3.10-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels

# --- runtime ---
FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && useradd -m appuser
COPY . .
RUN mkdir -p data/processed/embeddings data/processed/chunks && chown -R appuser:appuser /app
USER appuser
# Mặc định chạy API (xem app_api.py ở mục 3)
CMD ["python", "app_api.py"]