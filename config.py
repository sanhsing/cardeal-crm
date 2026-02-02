"""
車行寶 CRM v5.2 - 配置管理
北斗七星文創數位 × 織明
"""
import os
from pathlib import Path

# ===== 基本設定 =====
ENV = os.environ.get('ENV', 'development')
DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'
PORT = int(os.environ.get('PORT', 10000))
HOST = os.environ.get('HOST', '0.0.0.0')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# ===== 路徑設定 =====
BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.environ.get('DATA_DIR', BASE_DIR / 'data'))
UPLOAD_DIR = DATA_DIR / 'uploads'
BACKUP_DIR = DATA_DIR / 'backups'

# 確保目錄存在
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

# ===== 資料庫設定 =====
MASTER_DB = str(DATA_DIR / 'cardeal.db')

# ===== LINE 配置 =====
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_LOGIN_CHANNEL_ID = os.environ.get('LINE_LOGIN_CHANNEL_ID', '')

# ===== ECPay 綠界金流 =====
ECPAY_MERCHANT_ID = os.environ.get('ECPAY_MERCHANT_ID', '3002607')
ECPAY_HASH_KEY = os.environ.get('ECPAY_HASH_KEY', 'pwFHCqoQZGmho4w6')
ECPAY_HASH_IV = os.environ.get('ECPAY_HASH_IV', 'EkRm7iFT261dpevs')
ECPAY_TEST_MODE = os.environ.get('ECPAY_TEST_MODE', 'true').lower() == 'true'

# ===== AI 服務配置 =====
# DeepSeek API
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')

# OpenAI API（備用）
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'

# AI 提供者選擇
AI_PROVIDER = os.environ.get('AI_PROVIDER', 'deepseek')

# ===== Web Push (VAPID) =====
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_SUBJECT = os.environ.get('VAPID_SUBJECT', 'mailto:admin@cardeal.tw')

# ===== Telegram 通知 =====
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# ===== 加密配置 =====
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', '')

# ===== 日誌配置 =====
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# ===== URL 配置 =====
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:10000')


# ===== 功能開關 =====
FEATURES = {
    'ai': bool(DEEPSEEK_API_KEY or OPENAI_API_KEY),
    'line': bool(LINE_CHANNEL_SECRET),
    'ecpay': True,
    'push': bool(VAPID_PUBLIC_KEY),
    'telegram': bool(TELEGRAM_BOT_TOKEN),
}


def get_config_status() -> dict:
    """取得配置狀態（用於系統檢查）"""
    return {
        'env': ENV,
        'debug': DEBUG,
        'features': FEATURES,
        'ai_provider': AI_PROVIDER if FEATURES['ai'] else None,
        'database': MASTER_DB,
    }


def is_production() -> bool:
    """是否為生產環境"""
    return ENV == 'production'


# 📚 知識點
# -----------
# 1. 環境變數優先：
#    - 敏感資料不寫死
#    - 開發/生產環境分離
#
# 2. Path 物件：
#    - 跨平台路徑處理
#    - mkdir(exist_ok=True) 避免錯誤
#
# 3. 功能開關：
#    - 根據配置自動啟停功能
#    - 簡化運行時檢查
