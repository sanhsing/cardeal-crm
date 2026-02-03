"""車行寶 CRM v5.2 配置檔

設計原則
- 單一入口：handlers/services/templates 一律 import config。
- 向後相容：保留舊版常用欄位，避免熱修造成執行期 AttributeError。
- 環境變數優先：敏感資訊以環境變數注入。
"""

from __future__ import annotations

import os
from pathlib import Path

# ============================================================
# 應用程式資訊
# ============================================================
APP_NAME = os.environ.get("APP_NAME", "車行寶 CRM")
VERSION = os.environ.get("APP_VERSION", "5.2.0")

# ============================================================
# 環境設定
# ============================================================
ENV = os.environ.get("ENV", "development")
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
PORT = int(os.environ.get("PORT", 10000))
HOST = os.environ.get("HOST", "0.0.0.0")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

def is_production() -> bool:
    return ENV == "production"

# ============================================================
# 目錄 / 路徑
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE_DIR / "data")))
UPLOAD_DIR = DATA_DIR / "uploads"
BACKUP_DIR = DATA_DIR / "backups"

# 主 DB（檔案路徑字串，供 sqlite 連線）
MASTER_DB = str(DATA_DIR / "cardeal.db")

# 相容欄位：部分程式會讀取 BASE_URL 或自行從 env 取得
BASE_URL = os.environ.get("BASE_URL", f"http://localhost:{PORT}")

# 確保目錄存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 備份設定
# ============================================================
AUTO_BACKUP_ENABLED = os.environ.get("AUTO_BACKUP_ENABLED", "true").lower() == "true"
BACKUP_RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", 30))
BACKUP_NOTIFY = os.environ.get("BACKUP_NOTIFY", "true").lower() == "true"

# ============================================================
# LINE 設定
# ============================================================
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_LOGIN_CHANNEL_ID = os.environ.get("LINE_LOGIN_CHANNEL_ID", "")

# ============================================================
# ECPay 設定
# ============================================================
ECPAY_MERCHANT_ID = os.environ.get("ECPAY_MERCHANT_ID", "3002607")
ECPAY_HASH_KEY = os.environ.get("ECPAY_HASH_KEY", "pwFHCqoQZGmho4w6")
ECPAY_HASH_IV = os.environ.get("ECPAY_HASH_IV", "EkRm7iFT261dpevs")
ECPAY_TEST_MODE = os.environ.get("ECPAY_TEST_MODE", "true").lower() == "true"
ECPAY_API_URL = "https://payment-stage.ecpay.com.tw" if ECPAY_TEST_MODE else "https://payment.ecpay.com.tw"

# ============================================================
# AI 設定
# ============================================================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# 相容欄位：舊版會讀 AI_PROVIDER / FEATURES
AI_PROVIDER = os.environ.get("AI_PROVIDER", "deepseek")

# ============================================================
# Telegram 設定
# ============================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ============================================================
# Web Push (VAPID) 設定
# ============================================================
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
# 新版採用 claims email；舊版採用 subject(mailto)
VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "admin@cardeal.tw")
VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", f"mailto:{VAPID_CLAIMS_EMAIL}")

# ============================================================
# 安全 / 速率限制
# ============================================================
SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT", 3600))
MAX_LOGIN_ATTEMPTS = int(os.environ.get("MAX_LOGIN_ATTEMPTS", 5))
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", 100))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", 60))

# 相容欄位：加密金鑰（security_enhanced.py 直接讀 env，但保留便於統一）
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")

# ============================================================
# 日誌
# ============================================================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = os.environ.get("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# ============================================================
# DB URL
# ============================================================
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{MASTER_DB}")

# ============================================================
# UI THEME / 訂閱方案
# - 優先採用 config_manager 的標準結構（避免 templates/models 期待不同 key）
# ============================================================
try:
    from config_manager import THEME as _THEME, PLANS as _PLANS  # type: ignore
    THEME = _THEME
    PLANS = _PLANS
except Exception:
    # 後備：最低可用值（避免 templates 直接爆炸）
    THEME = {
        "primary": "#1e3a5f",
        "primary_light": "#2d4a6f",
        "accent": "#ee6c4d",
        "accent_hover": "#ff7a5c",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "info": "#3b82f6",
        "background": "#f8fafc",
        "surface": "#ffffff",
        "text": "#1e293b",
        "text_secondary": "#64748b",
        "border": "#e2e8f0",
    }
    PLANS = {
        "free": {
            "name": "免費版",
            "price": 0,
            "features": ["basic"],
            "limits": {"customers": 100, "vehicles": 50, "users": 1},
        },
        "pro_monthly": {
            "name": "專業版（月付）",
            "price": 299,
            "period": "monthly",
            "features": ["basic", "pro"],
            "limits": {"customers": -1, "vehicles": -1, "users": 5},
        },
        "pro_yearly": {
            "name": "專業版（年付）",
            "price": 2990,
            "period": "yearly",
            "features": ["basic", "pro"],
            "limits": {"customers": -1, "vehicles": -1, "users": 10},
        },
    }

# ============================================================
# 功能開關（舊版相容）
# ============================================================
FEATURES = {
    "ai": bool(DEEPSEEK_API_KEY or OPENAI_API_KEY),
    "line": bool(LINE_CHANNEL_SECRET),
    "ecpay": True,
    "push": bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY),
    "telegram": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
    "auto_backup": bool(AUTO_BACKUP_ENABLED),
}

def get_config_status() -> dict:
    return {
        "env": ENV,
        "debug": DEBUG,
        "features": FEATURES,
        "ai_provider": AI_PROVIDER if FEATURES.get("ai") else None,
        "database": MASTER_DB,
    }

# 補齊 templates 需要但舊配置可能缺少的色票鍵
if isinstance(THEME, dict) and 'accent_hover' not in THEME:
    THEME['accent_hover'] = THEME.get('accent', '#ee6c4d')
