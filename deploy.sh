#!/bin/bash
# ============================================
# 車行寶 CRM v5.1 - 部署腳本
# 北斗七星文創數位 × 織明
# ============================================

set -e  # 遇到錯誤立即停止

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 版本資訊
VERSION="5.1.0"
APP_NAME="cardeal"

# 輸出函數
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ===== 環境檢查 =====

check_environment() {
    info "檢查環境..."
    
    # Python 版本
    if ! command -v python3 &> /dev/null; then
        error "Python3 未安裝"
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l) -eq 1 ]]; then
        error "需要 Python 3.8+，當前版本：$PYTHON_VERSION"
    fi
    success "Python $PYTHON_VERSION"
    
    # pip
    if ! command -v pip3 &> /dev/null; then
        warning "pip3 未安裝，嘗試安裝..."
        python3 -m ensurepip --upgrade
    fi
    success "pip3 已安裝"
}

# ===== 依賴安裝 =====

install_dependencies() {
    info "安裝依賴..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt --quiet
        success "依賴安裝完成"
    else
        warning "requirements.txt 不存在"
    fi
}

# ===== 資料目錄 =====

setup_directories() {
    info "設定目錄..."
    
    mkdir -p data
    mkdir -p data/backups
    mkdir -p logs
    
    success "目錄設定完成"
}

# ===== 環境變數 =====

check_env_vars() {
    info "檢查環境變數..."
    
    REQUIRED_VARS=()
    OPTIONAL_VARS=("LINE_CHANNEL_SECRET" "LINE_CHANNEL_ACCESS_TOKEN" "TELEGRAM_BOT_TOKEN" "TELEGRAM_CHAT_ID")
    
    # 檢查必要變數
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            error "缺少必要環境變數：$var"
        fi
    done
    
    # 檢查可選變數
    for var in "${OPTIONAL_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            warning "可選環境變數未設定：$var"
        fi
    done
    
    success "環境變數檢查完成"
}

# ===== 資料庫初始化 =====

init_database() {
    info "初始化資料庫..."
    
    python3 -c "
import sys
sys.path.insert(0, '.')
from models import init_master_db
init_master_db()
print('Master database initialized')
"
    
    success "資料庫初始化完成"
}

# ===== 語法檢查 =====

check_syntax() {
    info "檢查 Python 語法..."
    
    errors=0
    for f in $(find . -name "*.py" -not -path "./__pycache__/*" -not -path "./venv/*"); do
        if ! python3 -m py_compile "$f" 2>/dev/null; then
            error "語法錯誤：$f"
            errors=$((errors + 1))
        fi
    done
    
    if [ $errors -gt 0 ]; then
        error "發現 $errors 個語法錯誤"
    fi
    
    success "語法檢查通過"
}

# ===== 測試 =====

run_tests() {
    info "執行測試..."
    
    if [ -d "tests" ]; then
        python3 -m pytest tests/ -v --tb=short || warning "部分測試失敗"
    else
        warning "測試目錄不存在"
    fi
}

# ===== 啟動服務 =====

start_server() {
    info "啟動服務..."
    
    # 設定環境
    export ENV=${ENV:-production}
    export HOST=${HOST:-0.0.0.0}
    export PORT=${PORT:-10000}
    
    echo "=================================="
    echo " $APP_NAME v$VERSION"
    echo " ENV: $ENV"
    echo " HOST: $HOST:$PORT"
    echo "=================================="
    
    python3 main.py
}

# ===== 開發模式 =====

start_dev() {
    info "開發模式啟動..."
    
    export ENV=development
    export DEBUG=true
    export HOST=127.0.0.1
    export PORT=8000
    
    echo "=================================="
    echo " $APP_NAME v$VERSION (DEV)"
    echo " http://localhost:$PORT"
    echo "=================================="
    
    python3 main.py
}

# ===== 備份 =====

backup() {
    info "執行備份..."
    
    BACKUP_DIR="data/backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"
    
    tar -czf "$BACKUP_FILE" data/*.db 2>/dev/null || warning "無資料庫檔案"
    
    success "備份完成：$BACKUP_FILE"
}

# ===== 清理 =====

cleanup() {
    info "清理暫存檔..."
    
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    
    success "清理完成"
}

# ===== 健康檢查 =====

health_check() {
    info "健康檢查..."
    
    HOST=${HOST:-127.0.0.1}
    PORT=${PORT:-10000}
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://$HOST:$PORT/api/health" 2>/dev/null)
    
    if [ "$response" == "200" ]; then
        success "服務正常運行"
    else
        error "服務異常，HTTP 狀態碼：$response"
    fi
}

# ===== 主程式 =====

main() {
    case "${1:-}" in
        install)
            check_environment
            install_dependencies
            setup_directories
            init_database
            success "安裝完成！執行 ./deploy.sh start 啟動服務"
            ;;
        start)
            check_syntax
            start_server
            ;;
        dev)
            start_dev
            ;;
        test)
            run_tests
            ;;
        backup)
            backup
            ;;
        health)
            health_check
            ;;
        clean)
            cleanup
            ;;
        check)
            check_environment
            check_env_vars
            check_syntax
            ;;
        *)
            echo "車行寶 CRM v$VERSION 部署腳本"
            echo ""
            echo "用法: $0 <command>"
            echo ""
            echo "Commands:"
            echo "  install  - 安裝依賴並初始化"
            echo "  start    - 啟動生產環境服務"
            echo "  dev      - 啟動開發環境"
            echo "  test     - 執行測試"
            echo "  backup   - 備份資料庫"
            echo "  health   - 健康檢查"
            echo "  clean    - 清理暫存檔"
            echo "  check    - 檢查環境"
            ;;
    esac
}

main "$@"


# 📚 知識點
# -----------
# 1. set -e：
#    - 遇到錯誤立即停止
#    - 避免繼續執行造成更多問題
#
# 2. Bash 函數：
#    - function_name() { ... }
#    - 使用 $1, $2 取得參數
#
# 3. ANSI 顏色碼：
#    - \033[0;32m：綠色
#    - \033[0m：重設
#    - 美化終端輸出
#
# 4. case 語句：
#    - Bash 的 switch-case
#    - 模式匹配
#    - ;; 結束每個 case
#
# 5. ${VAR:-default}：
#    - 如果 VAR 未設定，使用 default
#    - 提供預設值
#
# 6. curl 健康檢查：
#    - -s：靜默模式
#    - -o /dev/null：丟棄輸出
#    - -w "%{http_code}"：只輸出狀態碼
