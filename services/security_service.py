"""
車行寶 CRM v5.1 - 安全服務模組
北斗七星文創數位 × 織明

功能：CSRF 防護、Rate Limit、輸入驗證、XSS 防護
"""
import hashlib
import hmac
import secrets
import time
import re
from functools import wraps
from html import escape

# ===== CSRF 防護 =====

# Token 存儲（生產環境應用 Redis）
_csrf_tokens = {}
CSRF_TOKEN_EXPIRY = 3600  # 1小時

def generate_csrf_token(session_id):
    """產生 CSRF Token"""
    token = secrets.token_hex(32)
    _csrf_tokens[token] = {
        'session_id': session_id,
        'created_at': time.time()
    }
    return token


def verify_csrf_token(token, session_id):
    """驗證 CSRF Token"""
    if not token or token not in _csrf_tokens:
        return False
    
    data = _csrf_tokens[token]
    
    # 檢查是否過期
    if time.time() - data['created_at'] > CSRF_TOKEN_EXPIRY:
        del _csrf_tokens[token]
        return False
    
    # 檢查 session 是否匹配
    if data['session_id'] != session_id:
        return False
    
    # 使用後刪除（一次性）
    del _csrf_tokens[token]
    return True


def cleanup_csrf_tokens():
    """清理過期的 CSRF Token"""
    now = time.time()
    expired = [k for k, v in _csrf_tokens.items() 
               if now - v['created_at'] > CSRF_TOKEN_EXPIRY]
    for k in expired:
        del _csrf_tokens[k]


# ===== Rate Limit =====

# 請求記錄（生產環境應用 Redis）
_rate_limits = {}

class RateLimitConfig:
    """Rate Limit 配置"""
    # 格式：(requests, seconds)
    LOGIN = (5, 60)        # 5次/分鐘
    REGISTER = (3, 300)    # 3次/5分鐘
    API = (100, 60)        # 100次/分鐘
    UPLOAD = (10, 60)      # 10次/分鐘


def check_rate_limit(key, limit_type='API'):
    """檢查是否超過速率限制
    
    Args:
        key: 識別鍵（如 IP 或 user_id）
        limit_type: 限制類型
    
    Returns:
        (allowed, remaining, reset_time)
    """
    config = getattr(RateLimitConfig, limit_type, RateLimitConfig.API)
    max_requests, window_seconds = config
    
    now = time.time()
    full_key = f"{limit_type}:{key}"
    
    if full_key not in _rate_limits:
        _rate_limits[full_key] = {'requests': [], 'window_start': now}
    
    data = _rate_limits[full_key]
    
    # 清理過期請求
    data['requests'] = [t for t in data['requests'] 
                        if now - t < window_seconds]
    
    # 檢查是否超過限制
    if len(data['requests']) >= max_requests:
        reset_time = data['requests'][0] + window_seconds
        return False, 0, int(reset_time - now)
    
    # 記錄本次請求
    data['requests'].append(now)
    remaining = max_requests - len(data['requests'])
    
    return True, remaining, window_seconds


def rate_limit_response():
    """返回 Rate Limit 錯誤回應"""
    return {
        'success': False,
        'error': '請求過於頻繁，請稍後再試',
        'code': 'RATE_LIMIT_EXCEEDED'
    }


# ===== 輸入驗證 =====

class Validator:
    """輸入驗證器"""
    
    @staticmethod
    def phone(value):
        """驗證台灣手機號碼"""
        if not value:
            return False
        return bool(re.match(r'^09\d{8}$', value))
    
    @staticmethod
    def email(value):
        """驗證 Email"""
        if not value:
            return True  # Email 可選
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def password(value, min_length=4):
        """驗證密碼強度"""
        if not value or len(value) < min_length:
            return False
        return True
    
    @staticmethod
    def tenant_code(value):
        """驗證店家代碼"""
        if not value:
            return False
        return bool(re.match(r'^[a-z0-9_]{3,20}$', value))
    
    @staticmethod
    def plate(value):
        """驗證車牌號碼"""
        if not value:
            return True  # 車牌可選
        # 台灣車牌格式：ABC-1234 或 1234-AB
        patterns = [
            r'^[A-Z]{2,3}-\d{4}$',
            r'^\d{4}-[A-Z]{2}$',
            r'^[A-Z]{3}-\d{4}$',
        ]
        value = value.upper()
        return any(re.match(p, value) for p in patterns)
    
    @staticmethod
    def amount(value):
        """驗證金額"""
        try:
            val = int(value)
            return val >= 0
        except:
            return False
    
    @staticmethod
    def date(value):
        """驗證日期格式 YYYY-MM-DD"""
        if not value:
            return True
        return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', value))
    
    @staticmethod
    def safe_string(value, max_length=1000):
        """驗證安全字串（防 SQL 注入基礎檢查）"""
        if not value:
            return True
        if len(value) > max_length:
            return False
        # 檢查危險字元
        dangerous = ['--', ';--', '/*', '*/', 'xp_', 'UNION', 'SELECT', 'DROP', 'DELETE']
        value_upper = value.upper()
        return not any(d in value_upper for d in dangerous)


# ===== XSS 防護 =====

def sanitize_html(value):
    """清理 HTML（防 XSS）"""
    if not value:
        return value
    return escape(str(value))


def sanitize_dict(data, keys_to_sanitize=None):
    """清理字典中的值"""
    if not isinstance(data, dict):
        return data
    
    result = {}
    for key, value in data.items():
        if keys_to_sanitize and key not in keys_to_sanitize:
            result[key] = value
        elif isinstance(value, str):
            result[key] = sanitize_html(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, keys_to_sanitize)
        else:
            result[key] = value
    
    return result


# ===== 密碼安全 =====

def hash_password(password, salt=None):
    """密碼雜湊（含 salt）"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # 使用 PBKDF2（更安全）
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # 迭代次數
    ).hex()
    
    return f"{salt}${hashed}"


def verify_password(password, stored_hash):
    """驗證密碼"""
    if '$' not in stored_hash:
        # 舊格式（純 SHA256），向後相容
        return hashlib.sha256(password.encode()).hexdigest() == stored_hash
    
    salt, hashed = stored_hash.split('$', 1)
    check_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    
    # 使用 hmac.compare_digest 防止時序攻擊
    return hmac.compare_digest(hashed, check_hash)


# ===== IP 工具 =====

def get_client_ip(handler):
    """取得客戶端 IP"""
    # 檢查代理標頭
    forwarded = handler.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    
    real_ip = handler.headers.get('X-Real-IP', '')
    if real_ip:
        return real_ip
    
    # 直接連線
    return handler.client_address[0] if handler.client_address else 'unknown'


# ===== 日誌脫敏 =====

def mask_sensitive(data, fields=['password', 'token', 'secret', 'card']):
    """遮蔽敏感資訊"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if any(f in key.lower() for f in fields):
                result[key] = '***'
            elif isinstance(value, dict):
                result[key] = mask_sensitive(value, fields)
            else:
                result[key] = value
        return result
    return data


# 📚 知識點
# -----------
# 1. CSRF (Cross-Site Request Forgery)：
#    - 跨站請求偽造攻擊
#    - 用 Token 驗證請求來源
#    - Token 一次性使用更安全
#
# 2. Rate Limit（速率限制）：
#    - 防止暴力破解、DDoS
#    - 滑動視窗算法：記錄每次請求時間
#    - 生產環境用 Redis 存儲
#
# 3. PBKDF2（Password-Based Key Derivation Function 2）：
#    - 比單純 SHA256 更安全
#    - 加入 salt 防彩虹表攻擊
#    - 高迭代次數增加破解成本
#
# 4. hmac.compare_digest：
#    - 常數時間比較，防時序攻擊
#    - 普通 == 比較會提前返回
#    - 攻擊者可藉此推測密碼
#
# 5. XSS (Cross-Site Scripting)：
#    - 跨站腳本攻擊
#    - html.escape() 轉義特殊字元
#    - < → &lt;  > → &gt;
#
# 6. 時序攻擊（Timing Attack）：
#    - 藉由比較時間差推測資訊
#    - 密碼比對應用常數時間
