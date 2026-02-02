"""
車行寶 CRM v5.2 配置檔
（治理版 / Fail-Fast / 可部署）
"""
import os
from pathlib import Path

# ============================================================
# 應用程式資訊
# ============================================================
APP_NAME = "車行寶 CRM"
VERSION = "5.2.0"

# ============================================================
# 環境設定
# ============================================================
ENV = os.environ.get("ENV", "development")
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
PORT = int(os.environ.get("PORT", 10000))
HOST = os.environ.get("HOST", "0.0.0.0")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# ============================================================
# 目錄設定
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
BACKUP_DIR = DATA_DIR / "backups"
MASTER_DB = str(DATA_DIR / "cardeal.db")

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
ECPAY_API_URL = (
    "https://payment-stage.ecpay.com.tw"
    if ECPAY_TEST_MODE
    else "https://payment.ecpay.com.tw"
)

# ============================================================
# AI 設定
# ============================================================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ============================================================
# Telegram 設定
# ============================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ============================================================
# VAPID 推播設定
# ============================================================
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS_EMAIL = os.environ.get(
    "VAPID_CLAIMS_EMAIL", "admin@cardeal.tw"
)

# ============================================================
# 日誌設定
# ============================================================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================
# 安全設定
# ============================================================
SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT", 3600))
MAX_LOGIN_ATTEMPTS = int(os.environ.get("MAX_LOGIN_ATTEMPTS", 5))
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", 100))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", 60))

# ============================================================
# 資料庫設定
# ============================================================
DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"sqlite:///{MASTER_DB}"
)

# ============================================================
# 訂閱方案
# ============================================================
PLANS = {
    "free": {
        "name": "免費版",
        "price": 0,
        "max_vehicles": 50,
        "max_customers": 100,
        "max_users": 2,
        "features": ["基本功能", "手機版"],
    },
    "basic": {
        "name": "基本版",
        "price": 299,
        "max_vehicles": 200,
        "max_customers": 500,
        "max_users": 5,
        "features": ["基本功能", "手機版", "LINE 通知", "報表匯出"],
    },
    "pro": {
        "name": "專業版",
        "price": 599,
        "max_vehicles": -1,
        "max_customers": -1,
        "max_users": -1,
        "features": ["所有功能", "AI 助手", "API 存取", "優先支援"],
    },
}

# ============================================================
# 主題（Theme）定義
# template 僅能使用 THEME（dict），不得使用 THEME_NAME
# ============================================================
THEMES = {
    "default": {
        "primary": "#2563eb",
        "secondary": "#64748b",
        "background": "#ffffff",
        "text": "#0f172a",
        "muted": "#e5e7eb",
    },
    "dark": {
        "primary": "#38bdf8",
        "secondary": "#94a3b8",
        "background": "#020617",
        "text": "#e5e7eb",
        "muted": "#334155",
    },
}

# ============================================================
# 主題選擇（治理入口）
# ============================================================
THEME_NAME = os.environ.get("THEME", "default")

if not isinstance(THEME_NAME, str):
    raise RuntimeError("[CONFIG ERROR] THEME must be a string")

if THEME_NAME not in THEMES:
    raise RuntimeError(
        f"[CONFIG ERROR] Unknown THEME '{THEME_NAME}'. "
        f"Available themes: {', '.join(THEMES.keys())}"
    )

# ✅ template 唯一允許使用的主題物件
THEME = THEMES[THEME_NAME]

# ============================================================
# 啟動期治理檢查（Fail Fast）
# ============================================================
def _config_self_check():
    assert isinstance(THEME, dict), "THEME must be a dict"
    assert "primary" in THEME, "THEME.primary is required"
    assert isinstance(PORT, int), "PORT must be int"

    if ENV == "production" and SECRET_KEY.startswith("dev-"):
        raise RuntimeError(
            "SECRET_KEY must be set in production "
            "(set it in Render Environment Variables)"
        )

_config_self_check()

# ============================================================
# 確保目錄存在
# ============================================================
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
