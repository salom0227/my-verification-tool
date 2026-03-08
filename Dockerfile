FROM python:3.10-slim

# Tizim kutubxonalari (Pillow va TLS bypass uchun shart)
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir curl_cffi cloudscraper pillow httpx

COPY . .

# Server ishga tushishi bilan Spotify toolni boshlaydi
CMD ["python", "spotify-verify-tool/main.py"]
