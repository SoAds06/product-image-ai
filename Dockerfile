FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Projeyi clone et
RUN git clone https://github.com/SoAds06/product-image-ai.git .

# Python bağımlılıkları yükle
RUN pip install --no-cache-dir -r requirements.txt

# .env dosyasını oluştur
RUN cp .env.example .env

# Port aç
EXPOSE 8000

# Uygulamayı başlat
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
