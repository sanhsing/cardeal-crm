"""
車行寶 CRM v5.1 - 配置管理器
北斗七星文創數位 × 織明

功能：環境變數管理、動態配置、敏感資訊處理
"""
import os
import json
from functools import lru_cache

# ===== 環境變數載入 =====

def get_env(key, default=None, cast=str):
    """取得環境變數
    
    Args:
        key: 環境變數名稱
        default: 預設值
        cast: 類型轉換函數
    
    Returns:
        轉換後的值
    """
    value = os.environ.get(key)
    
    if value is None:
        return default
    
    if cast == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    
    try:
        return cast(value)
    except (ValueError, TypeError):
        return default


def get_env_list(key, default=None, separator=','):
    """取得環境變數列表"""
    value = os.environ.get(key)
    if value is None:
        return default or []
    return [v.strip() for v in value.split(separator) if v.strip()]


def get_env_json(key, default=None):
    """取得 JSON 格式環境變數"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


# ===== 配置類 =====

class Config:
    """應用配置"""
    
    # 基本資訊
    APP_NAME = 'CarDeal CRM'
    VERSION = '5.1.0'
    BUILD = '20260202'
    
    # 環境
    ENV = get_env('ENV', 'development')
    DEBUG = get_env('DEBUG', ENV != 'production', bool)
    
    # 伺服器
    HOST = get_env('HOST', '0.0.0.0')
    PORT = get_env('PORT', 10000, int)
    
    # 資料庫
    DATA_DIR = get_env('DATA_DIR', './data')
    MASTER_DB = os.path.join(DATA_DIR, 'master.db')
    BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
    
    # LINE
    LINE_CHANNEL_SECRET = get_env('LINE_CHANNEL_SECRET', '')
    LINE_CHANNEL_ACCESS_TOKEN = get_env('LINE_CHANNEL_ACCESS_TOKEN', '')
    LINE_LOGIN_CHANNEL_ID = get_env('LINE_LOGIN_CHANNEL_ID', '')
    
    # ECPay
    ECPAY_MERCHANT_ID = get_env('ECPAY_MERCHANT_ID', '2000132')
    ECPAY_HASH_KEY = get_env('ECPAY_HASH_KEY', '5294y06JbISpM5x9')
    ECPAY_HASH_IV = get_env('ECPAY_HASH_IV', 'v77hoKGq4kWxNNIS')
    ECPAY_TEST_MODE = get_env('ECPAY_TEST_MODE', True, bool)
    
    # Telegram
    TELEGRAM_BOT_TOKEN = get_env('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = get_env('TELEGRAM_CHAT_ID', '')
    
    # 安全
    SECRET_KEY = get_env('SECRET_KEY', 'change-me-in-production')
    SESSION_TIMEOUT = get_env('SESSION_TIMEOUT', 24, int)  # 小時
    CSRF_ENABLED = get_env('CSRF_ENABLED', True, bool)
    
    # 快取
    CACHE_ENABLED = get_env('CACHE_ENABLED', True, bool)
    CACHE_DEFAULT_TTL = get_env('CACHE_DEFAULT_TTL', 300, int)
    
    # 備份
    BACKUP_RETENTION_DAYS = get_env('BACKUP_RETENTION_DAYS', 30, int)
    AUTO_BACKUP_ENABLED = get_env('AUTO_BACKUP_ENABLED', True, bool)
    
    # 日誌
    LOG_LEVEL = get_env('LOG_LEVEL', 'INFO')
    LOG_FORMAT = get_env('LOG_FORMAT', '%(asctime)s [%(levelname)s] %(message)s')
    
    # 限制
    MAX_UPLOAD_SIZE = get_env('MAX_UPLOAD_SIZE', 10 * 1024 * 1024, int)  # 10MB
    RATE_LIMIT_ENABLED = get_env('RATE_LIMIT_ENABLED', True, bool)
    
    @classmethod
    def is_production(cls):
        """是否為生產環境"""
        return cls.ENV == 'production'
    
    @classmethod
    def is_development(cls):
        """是否為開發環境"""
        return cls.ENV == 'development'
    
    @classmethod
    def validate(cls):
        """驗證必要配置"""
        errors = []
        
        if cls.is_production():
            if cls.SECRET_KEY == 'change-me-in-production':
                errors.append('SECRET_KEY 未設定')
            
            if not cls.LINE_CHANNEL_SECRET:
                errors.append('LINE_CHANNEL_SECRET 未設定')
            
            if not cls.TELEGRAM_BOT_TOKEN:
                errors.append('TELEGRAM_BOT_TOKEN 未設定')
        
        return errors
    
    @classmethod
    def to_dict(cls, include_secrets=False):
        """轉為字典（用於顯示/日誌）"""
        result = {}
        
        secret_keys = ['SECRET_KEY', 'LINE_CHANNEL_SECRET', 'LINE_CHANNEL_ACCESS_TOKEN',
                       'ECPAY_HASH_KEY', 'ECPAY_HASH_IV', 'TELEGRAM_BOT_TOKEN']
        
        for key in dir(cls):
            if key.isupper() and not key.startswith('_'):
                value = getattr(cls, key)
                if not callable(value):
                    if not include_secrets and key in secret_keys:
                        value = '***' if value else '(未設定)'
                    result[key] = value
        
        return result


# ===== 訂閱方案配置 =====

PLANS = {
    'free': {
        'name': '免費版',
        'price': 0,
        'features': ['basic', 'customers_100', 'vehicles_50'],
        'limits': {
            'customers': 100,
            'vehicles': 50,
            'users': 1
        }
    },
    'pro_monthly': {
        'name': '專業版（月付）',
        'price': 299,
        'period': 'monthly',
        'features': ['basic', 'pro', 'unlimited', 'line', 'reports', 'export'],
        'limits': {
            'customers': -1,  # 無限
            'vehicles': -1,
            'users': 5
        }
    },
    'pro_yearly': {
        'name': '專業版（年付）',
        'price': 2990,
        'period': 'yearly',
        'features': ['basic', 'pro', 'unlimited', 'line', 'reports', 'export'],
        'limits': {
            'customers': -1,
            'vehicles': -1,
            'users': 10
        }
    }
}


# ===== 狀態/來源/等級配置 =====

VEHICLE_STATUS = {
    'in_stock': {'name': '在庫', 'color': 'success'},
    'reserved': {'name': '已預訂', 'color': 'warning'},
    'sold': {'name': '已售出', 'color': 'default'},
    'maintenance': {'name': '整備中', 'color': 'info'}
}

CUSTOMER_SOURCE = {
    'walk_in': '現場來店',
    'phone': '電話詢問',
    'line': 'LINE',
    'facebook': 'Facebook',
    'referral': '朋友介紹',
    'web': '網站',
    'other': '其他'
}

CUSTOMER_LEVEL = {
    'vip': {'name': 'VIP', 'color': 'warning'},
    'normal': {'name': '一般', 'color': 'default'},
    'potential': {'name': '潛在', 'color': 'info'},
    'cold': {'name': '冷淡', 'color': 'default'}
}

DEAL_TYPE = {
    'buy': {'name': '收購', 'color': 'info'},
    'sell': {'name': '售出', 'color': 'success'}
}


# ===== UI 主題配置 =====

THEME = {
    'primary': '#1e3a5f',
    'primary_light': '#2d4a6f',
    'accent': '#ee6c4d',
    'accent_hover': '#ff7a5c',
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'info': '#3b82f6',
    'background': '#f8fafc',
    'surface': '#ffffff',
    'text': '#1e293b',
    'text_secondary': '#64748b',
    'border': '#e2e8f0'
}


# ===== 功能開關 =====

FEATURES = {
    'line_integration': get_env('FEATURE_LINE', True, bool),
    'ecpay_payment': get_env('FEATURE_ECPAY', True, bool),
    'excel_export': get_env('FEATURE_EXCEL', True, bool),
    'price_estimation': get_env('FEATURE_PRICE', True, bool),
    'auto_backup': get_env('FEATURE_BACKUP', True, bool),
}


def is_feature_enabled(feature):
    """檢查功能是否啟用"""
    return FEATURES.get(feature, False)


# 📚 知識點
# -----------
# 1. 環境變數 (Environment Variables)：
#    - os.environ.get(key)：取得環境變數
#    - 敏感資訊不寫在程式碼中
#    - 不同環境可有不同配置
#
# 2. 類型轉換：
#    - cast=int：轉為整數
#    - cast=bool：轉為布林值
#    - 預設值處理
#
# 3. 配置驗證：
#    - 生產環境必須設定某些值
#    - 啟動時檢查，及早發現問題
#
# 4. 功能開關 (Feature Flags)：
#    - 動態啟用/停用功能
#    - 漸進式發布
#    - A/B 測試
#
# 5. 敏感資訊處理：
#    - 日誌中遮蔽密碼/金鑰
#    - 避免敏感資訊外洩
#
# 6. @classmethod：
#    - 類別方法，用 cls 而非 self
#    - 可在不建立實例時呼叫
#    - Config.is_production()
