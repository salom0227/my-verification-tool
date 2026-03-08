# 1. Python tasvirini tanlaymiz
FROM python:3.10-slim

# 2. Tizim kutubxonalarini o'rnatamiz
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

# 5. Loyihaning barcha fayllarini nusxalaymiz
COPY . .

# 6. Output papkasini yaratib qo'yamiz (rasmlar uchun)
RUN mkdir -p canva-teacher-tool/output

# 7. Railway portini aniqlaymiz va Web-serverni ishga tushiramiz
CMD ["python", "app.py"]
