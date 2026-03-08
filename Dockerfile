# 1. Python tasvirini tanlaymiz
FROM python:3.10-slim

# 2. Tizim kutubxonalarini o'rnatamiz (Pillow, curl_cffi va shriftlar uchun)
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# 3. Ishchi katalogni belgilaymiz
WORKDIR /app

# 4. Kutubxonalarni o'rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# FastAPI va Web-server uchun qo'shimcha kutubxonalar
RUN pip install --no-cache-dir fastapi uvicorn jinja2 python-multipart curl_cffi cloudscraper pillow httpx

# 5. Loyihaning barcha fayllarini nusxalaymiz
COPY . .

# 6. Railway portini aniqlaymiz va Web-serverni ishga tushiramiz
# app.py - bu biz yaratgan yangi Frontend+Backend birlashtiruvchi fayl
CMD ["python", "app.py"]
