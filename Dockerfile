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

# 安裝 Python 套件
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 複製專案程式碼
COPY . .

# 載入 .env 設定（可選）
COPY .env .env

# 設定 Port（與 Streamlit 對應）
ENV PORT=1111

EXPOSE ${PORT}

# 啟動 Streamlit（用 sh -c 方式與你原來一致）
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0"]