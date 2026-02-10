FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY monitor.py .

# 建立資料目錄
RUN mkdir -p /data

# 設定環境變數
ENV PYTHONUNBUFFERED=1

# 執行監控腳本
CMD ["python", "-u", "monitor.py"]
