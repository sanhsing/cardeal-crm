# ============================================
# 車行寶 CRM v5.1 - Makefile
# 北斗七星文創數位 × 織明
# ============================================

.PHONY: help dev test lint clean docker-build docker-run docker-stop backup optimize

# 預設目標
help:
	@echo "車行寶 CRM v5.1 - 可用指令"
	@echo ""
	@echo "開發指令："
	@echo "  make dev          - 啟動開發伺服器"
	@echo "  make test         - 執行測試"
	@echo "  make lint         - 語法檢查"
	@echo "  make clean        - 清理暫存檔案"
	@echo ""
	@echo "Docker 指令："
	@echo "  make docker-build - 建置 Docker 映像"
	@echo "  make docker-run   - 啟動 Docker 容器"
	@echo "  make docker-stop  - 停止 Docker 容器"
	@echo ""
	@echo "維護指令："
	@echo "  make backup       - 備份資料庫"
	@echo "  make optimize     - 優化資料庫"
	@echo "  make health       - 健康檢查"

# 開發伺服器
dev:
	@echo "🚀 啟動開發伺服器..."
	DEBUG=true python main.py

# 執行測試
test:
	@echo "🧪 執行測試..."
	python -m pytest tests/ -v --tb=short

# 測試覆蓋率
test-cov:
	@echo "📊 執行測試並產生覆蓋率報告..."
	python -m pytest tests/ -v --cov=. --cov-report=html
	@echo "報告位於 htmlcov/index.html"

# 語法檢查
lint:
	@echo "🔍 語法檢查..."
	@find . -name "*.py" -type f -not -path "./__pycache__/*" -not -path "./venv/*" | \
		while read f; do python -m py_compile "$$f" || exit 1; done
	@echo "✅ 全部通過"

# 清理
clean:
	@echo "🧹 清理暫存檔案..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage .pytest_cache/ 2>/dev/null || true
	@echo "✅ 清理完成"

# Docker 建置
docker-build:
	@echo "🐳 建置 Docker 映像..."
	docker build -t cardeal-crm:latest .

# Docker 啟動
docker-run:
	@echo "🐳 啟動 Docker 容器..."
	docker-compose up -d
	@echo "✅ 容器已啟動"
	@echo "   存取 http://localhost:10000"

# Docker 停止
docker-stop:
	@echo "🐳 停止 Docker 容器..."
	docker-compose down
	@echo "✅ 容器已停止"

# Docker 日誌
docker-logs:
	docker-compose logs -f

# 備份
backup:
	@echo "💾 執行備份..."
	python -c "from services.backup_service import backup_all; print(backup_all())"

# 優化資料庫
optimize:
	@echo "⚡ 優化資料庫..."
	python scripts/optimize_db.py

# 健康檢查
health:
	@echo "🏥 健康檢查..."
	python scripts/health_check.py

# 安裝依賴
install:
	@echo "📦 安裝依賴..."
	pip install -r requirements.txt

# 初始化
init: install
	@echo "🔧 初始化系統..."
	mkdir -p data data/backups data/uploads logs
	@echo "✅ 初始化完成"


# 📚 知識點
# -----------
# 1. .PHONY：
#    - 宣告偽目標
#    - 避免與同名檔案衝突
#
# 2. @：
#    - 不顯示指令本身
#    - 只顯示輸出
#
# 3. ||：
#    - 前一指令失敗時執行
#    - || true 忽略錯誤
#
# 4. $$：
#    - Makefile 中的 $ 轉義
#    - 傳遞給 shell
