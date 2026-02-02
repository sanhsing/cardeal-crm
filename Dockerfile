# ============================================
# 車行寶 CRM v5.1 - Dockerfile
# 北斗七星文創數位 × 織明
# ============================================

FROM python:3.11-slim

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 建立資料目錄
RUN mkdir -p /app/data /app/data/backups /app/data/uploads /app/logs

# 設定權限
RUN chmod +x deploy.sh

# 暴露埠號
EXPOSE 10000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/api/health || exit 1

# 啟動命令
CMD ["python", "main.py"]


# 📚 知識點
# -----------
# 1. FROM python:3.11-slim：
#    - 使用輕量版 Python 映像
#    - slim 比 full 小很多
#
# 2. ENV 環境變數：
#    - PYTHONDONTWRITEBYTECODE：不產生 .pyc
#    - PYTHONUNBUFFERED：即時輸出日誌
#
# 3. 多層快取：
#    - 先複製 requirements.txt
#    - 再安裝依賴
#    - 最後複製程式碼
#    - 程式碼變更時不重建依賴層
#
# 4. HEALTHCHECK：
#    - Docker 內建健康檢查
#    - 自動重啟不健康的容器
