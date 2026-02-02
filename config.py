"""
車行寶 CRM v5.2 配置檔
"""
import os
from pathlib import Path

# ===== 應用程式資訊 =====
APP_NAME = "車行寶 CRM"
VERSION = "5.2.0"

# ===== 環境設定 =====
ENV = os.environ.get('ENV', 'development')
DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'
PORT = int(os.environ.get('PORT', 10000))
HOST = os.environ.get('HOST', '0.0.0.0')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# ===== 目錄設定 =====
BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.environ.get('DATA_DIR', BASE_DIR / 'data'))
UPLOAD_DIR = DATA_DIR / 'uploads'
BACKUP_DIR = DATA_DIR / 'backups'
MASTER_DB = str(DATA_DIR / 'cardeal.db')

# ===== LINE 設定 =====
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_LOGIN_CHANNEL_ID = os.environ.get('LINE_LOGIN_CHANNEL_ID', '')

# ===== ECPay 設定 =====
ECPAY_MERCHANT_ID = os.environ.get('ECPAY_MERCHANT_ID', '3002607')
ECPAY_HASH_KEY = os.environ.get('ECPAY_HASH_KEY', 'pwFHCqoQZGmho4w6')
ECPAY_HASH_IV = os.environ.get('ECPAY_HASH_IV', 'EkRm7iFT261dpevs')
ECPAY_TEST_MODE = os.environ.get('ECPAY_TEST_MODE', 'true').lower() == 'true'

# ===== DeepSeek AI 設定 =====
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')

# ===== OpenAI 設定 =====
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# ===== Telegram 設定 =====
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# ===== VAPID 推播設定 =====
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_CLAIMS_EMAIL = os.environ.get('VAPID_CLAIMS_EMAIL', 'admin@cardeal.tw')

# ===== 日誌設定 =====
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ===== 安全設定 =====
SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 小時
MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', 100))
RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', 60))

# ===== 資料庫設定 =====
DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{MASTER_DB}')

# 確保目錄存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
