FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .
COPY .env .env

ENV PYTHONPATH=/app

CMD ["sh", "-c", "streamlit run app/api/ui.py --server.port=1111 --server.address=0.0.0.0"]
