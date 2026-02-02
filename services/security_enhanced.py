"""
車行寶 CRM v5.1 - 安全加固服務
北斗七星文創數位 × 織明

功能：
1. AES 敏感數據加密
2. SQL 注入防護
3. 輸入驗證增強
4. 安全審計日誌
5. 密碼強度檢查
6. 安全響應頭
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Callable
from html import escape

logger = logging.getLogger(__name__)


# ============================================================
# 1. AES 加密（敏感數據）
# ============================================================

# 嘗試導入加密庫
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class DataEncryptor:
    """敏感數據加密器
    
    使用 Fernet（AES-128-CBC + HMAC）加密
    """
    
    def __init__(self, secret_key: str = None) -> None:
        """
        Args:
            secret_key: 加密金鑰，不提供則從環境變數讀取
        """
        if not HAS_CRYPTO:
            logger.warning("cryptography 未安裝，加密功能不可用")
            self.fernet = None
            return
        
        key = secret_key or os.environ.get('ENCRYPTION_KEY', 'default-dev-key-change-me')
        
        # 從密碼派生金鑰
        salt = b'cardeal_crm_salt'  # 生產環境應使用隨機 salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        self.fernet = Fernet(derived_key)
    
    def encrypt(self, data: str) -> str:
        """加密字串"""
        if not self.fernet:
            return data
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """解密字串"""
        if not self.fernet:
            return encrypted
        try:
            return self.fernet.decrypt(encrypted.encode()).decode()
        except Exception as e:
            logger.error(f"解密失敗: {e}")
            return encrypted
    
    def encrypt_dict(self, data: Dict, fields: List[str]) -> Dict:
        """加密字典中的指定欄位"""
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(str(result[field]))
        return result
    
    def decrypt_dict(self, data: Dict, fields: List[str]) -> Dict:
        """解密字典中的指定欄位"""
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.decrypt(str(result[field]))
        return result


# 全域加密器
_encryptor: Optional[DataEncryptor] = None


def get_encryptor() -> DataEncryptor:
    """取得加密器實例"""
    global _encryptor
    if _encryptor is None:
        _encryptor = DataEncryptor()
    return _encryptor


# 敏感欄位清單
SENSITIVE_FIELDS = [
    'id_number',      # 身份證號
    'phone',          # 電話
    'address',        # 地址
    'bank_account',   # 銀行帳號
    'credit_card',    # 信用卡號
    'password_hash',  # 密碼雜湊
]


# ============================================================
# 2. SQL 注入防護
# ============================================================

class SQLSanitizer:
    """SQL 注入防護"""
    
    # 危險關鍵字
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'TRUNCATE', 'INSERT', 'UPDATE',
        'ALTER', 'CREATE', 'EXEC', 'EXECUTE', 'UNION',
        '--', '/*', '*/', 'xp_', 'sp_'
    ]
    
    # 允許的運算符
    SAFE_OPERATORS = ['=', '!=', '<', '>', '<=', '>=', 'LIKE', 'IN', 'BETWEEN', 'IS']
    
    @classmethod
    def is_safe_identifier(cls, identifier: str) -> bool:
        """檢查識別符是否安全（表名、欄位名）"""
        # 只允許字母、數字、底線
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            return False
        
        # 檢查危險關鍵字
        upper = identifier.upper()
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in upper:
                return False
        
        return True
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """清理字串輸入"""
        if not isinstance(value, str):
            return str(value)
        
        # 截斷過長字串
        value = value[:max_length]
        
        # 移除危險字元
        value = value.replace('\x00', '')  # NULL byte
        value = value.replace('\r', '')     # Carriage return
        
        # 轉義單引號（SQLite）
        value = value.replace("'", "''")
        
        return value
    
    @classmethod
    def validate_query_params(cls, params: Dict) -> Tuple[bool, str]:
        """驗證查詢參數"""
        for key, value in params.items():
            # 檢查 key
            if not cls.is_safe_identifier(key):
                return False, f"不安全的參數名: {key}"
            
            # 檢查 value
            if isinstance(value, str):
                upper = value.upper()
                for keyword in cls.DANGEROUS_KEYWORDS:
                    if keyword in upper:
                        logger.warning(f"可能的 SQL 注入嘗試: {key}={value}")
                        return False, f"參數包含危險關鍵字: {keyword}"
        
        return True, "OK"
    
    @classmethod
    def build_safe_where(cls, conditions: Dict) -> Tuple[str, List]:
        """建立安全的 WHERE 子句
        
        Args:
            conditions: {column: value} 或 {column: (operator, value)}
        
        Returns:
            (WHERE 子句, 參數列表)
        """
        clauses = []
        params = []
        
        for column, value in conditions.items():
            if not cls.is_safe_identifier(column):
                continue
            
            if isinstance(value, tuple) and len(value) == 2:
                operator, val = value
                if operator.upper() not in cls.SAFE_OPERATORS:
                    continue
                clauses.append(f"{column} {operator} ?")
                params.append(val)
            elif value is None:
                clauses.append(f"{column} IS NULL")
            else:
                clauses.append(f"{column} = ?")
                params.append(value)
        
        where = ' AND '.join(clauses) if clauses else '1=1'
        return where, params


# ============================================================
# 3. 輸入驗證
# ============================================================

class InputValidator:
    """輸入驗證器"""
    
    # 常用正則
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone_tw': r'^09\d{8}$',
        'id_tw': r'^[A-Z][12]\d{8}$',
        'plate_tw': r'^[A-Z]{2,3}-?\d{4}$',
        'url': r'^https?://[^\s/$.?#].[^\s]*$',
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'username': r'^[a-zA-Z0-9_]{3,20}$',
    }
    
    @classmethod
    def validate(cls, value: Any, rules: Dict) -> Tuple[bool, str]:
        """驗證輸入
        
        Args:
            value: 要驗證的值
            rules: 驗證規則
                - required: bool
                - type: str/int/float/bool
                - min_length: int
                - max_length: int
                - min_value: number
                - max_value: number
                - pattern: regex pattern name or custom
                - choices: list of allowed values
        
        Returns:
            (is_valid, error_message)
        """
        # 必填檢查
        if rules.get('required') and (value is None or value == ''):
            return False, "此欄位為必填"
        
        if value is None or value == '':
            return True, "OK"
        
        # 類型檢查
        expected_type = rules.get('type')
        if expected_type:
            if expected_type == 'str' and not isinstance(value, str):
                return False, "必須為字串"
            elif expected_type == 'int':
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    return False, "必須為整數"
            elif expected_type == 'float':
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    return False, "必須為數字"
            elif expected_type == 'bool' and not isinstance(value, bool):
                return False, "必須為布林值"
        
        # 字串長度
        if isinstance(value, str):
            if rules.get('min_length') and len(value) < rules['min_length']:
                return False, f"長度不能少於 {rules['min_length']} 字元"
            if rules.get('max_length') and len(value) > rules['max_length']:
                return False, f"長度不能超過 {rules['max_length']} 字元"
        
        # 數值範圍
        if isinstance(value, (int, float)):
            if rules.get('min_value') is not None and value < rules['min_value']:
                return False, f"不能小於 {rules['min_value']}"
            if rules.get('max_value') is not None and value > rules['max_value']:
                return False, f"不能大於 {rules['max_value']}"
        
        # 正則驗證
        pattern = rules.get('pattern')
        if pattern and isinstance(value, str):
            regex = cls.PATTERNS.get(pattern, pattern)
            if not re.match(regex, value):
                return False, f"格式不正確"
        
        # 選項驗證
        choices = rules.get('choices')
        if choices and value not in choices:
            return False, f"必須是以下之一: {', '.join(map(str, choices))}"
        
        return True, "OK"
    
    @classmethod
    def validate_dict(cls, data: Dict, schema: Dict) -> Tuple[bool, Dict]:
        """驗證字典
        
        Args:
            data: 要驗證的資料
            schema: {field: rules}
        
        Returns:
            (is_valid, {field: error_message})
        """
        errors = {}
        
        for field, rules in schema.items():
            value = data.get(field)
            is_valid, error = cls.validate(value, rules)
            if not is_valid:
                errors[field] = error
        
        return len(errors) == 0, errors
    
    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """清理 HTML（防 XSS）"""
        return escape(text)
    
    @classmethod
    def strip_tags(cls, text: str) -> str:
        """移除 HTML 標籤"""
        return re.sub(r'<[^>]+>', '', text)


# ============================================================
# 4. 密碼安全
# ============================================================

class PasswordSecurity:
    """密碼安全工具"""
    
    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> Tuple[str, str]:
        """雜湊密碼
        
        Returns:
            (hash, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # PBKDF2 with SHA-256
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt,
            iterations=100000
        )
        
        return base64.b64encode(hash_bytes).decode(), base64.b64encode(salt).decode()
    
    @staticmethod
    def verify_password(password: str, hash_str: str, salt_str: str) -> bool:
        """驗證密碼"""
        salt = base64.b64decode(salt_str)
        expected_hash, _ = PasswordSecurity.hash_password(password, salt)
        return hmac.compare_digest(hash_str, expected_hash)
    
    @staticmethod
    def check_strength(password: str) -> Dict:
        """檢查密碼強度
        
        Returns:
            {score: 0-100, level: weak/medium/strong, issues: [...]}
        """
        issues = []
        score = 0
        
        # 長度
        length = len(password)
        if length < 8:
            issues.append("至少需要 8 個字元")
        elif length >= 12:
            score += 30
        elif length >= 8:
            score += 15
        
        # 大寫字母
        if re.search(r'[A-Z]', password):
            score += 15
        else:
            issues.append("建議包含大寫字母")
        
        # 小寫字母
        if re.search(r'[a-z]', password):
            score += 15
        else:
            issues.append("建議包含小寫字母")
        
        # 數字
        if re.search(r'\d', password):
            score += 15
        else:
            issues.append("建議包含數字")
        
        # 特殊字元
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 25
        else:
            issues.append("建議包含特殊字元")
        
        # 常見密碼檢查
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
        if password.lower() in common_passwords:
            score = 0
            issues.insert(0, "密碼過於常見")
        
        # 判斷等級
        if score >= 70:
            level = 'strong'
        elif score >= 40:
            level = 'medium'
        else:
            level = 'weak'
        
        return {
            'score': score,
            'level': level,
            'issues': issues
        }


# ============================================================
# 5. 安全審計日誌
# ============================================================

class SecurityAudit:
    """安全審計日誌"""
    
    # 事件類型
    EVENT_LOGIN = 'login'
    EVENT_LOGOUT = 'logout'
    EVENT_LOGIN_FAILED = 'login_failed'
    EVENT_PASSWORD_CHANGE = 'password_change'
    EVENT_PERMISSION_DENIED = 'permission_denied'
    EVENT_DATA_ACCESS = 'data_access'
    EVENT_DATA_MODIFY = 'data_modify'
    EVENT_SUSPICIOUS = 'suspicious'
    
    def __init__(self, log_file: str = None) -> None:
        self.log_file = log_file
        self._logs: List[Dict] = []
        self._max_memory_logs = 1000
    
    def log(self, event_type: str, user_id: int = None, details: Dict = None,
            ip_address: str = None, severity: str = 'info'):
        """記錄安全事件"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'severity': severity,
            'details': details or {}
        }
        
        # 記憶體保留
        self._logs.append(entry)
        if len(self._logs) > self._max_memory_logs:
            self._logs.pop(0)
        
        # 檔案記錄
        if self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(entry) + '\n')
            except Exception as e:
                logger.error(f"寫入審計日誌失敗: {e}")
        
        # 高嚴重性事件
        if severity in ('warning', 'error', 'critical'):
            logger.warning(f"安全事件 [{event_type}]: {details}")
    
    def get_logs(self, event_type: str = None, user_id: int = None,
                 limit: int = 100) -> List[Dict]:
        """查詢審計日誌"""
        logs = self._logs
        
        if event_type:
            logs = [l for l in logs if l['event_type'] == event_type]
        if user_id:
            logs = [l for l in logs if l['user_id'] == user_id]
        
        return logs[-limit:]
    
    def get_suspicious_activities(self, hours: int = 24) -> List[Dict]:
        """取得可疑活動"""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        suspicious = []
        for log in self._logs:
            log_time = datetime.fromisoformat(log['timestamp']).timestamp()
            if log_time >= cutoff and log['severity'] in ('warning', 'error', 'critical'):
                suspicious.append(log)
        
        return suspicious


# 全域審計器
_audit = SecurityAudit()


def audit_log(event_type: str, **kwargs):
    """快捷審計記錄"""
    _audit.log(event_type, **kwargs)


# ============================================================
# 6. 安全響應頭
# ============================================================

def get_security_headers() -> Dict[str, str]:
    """取得安全響應頭"""
    return {
        # 防止 XSS
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        
        # 防止點擊劫持
        'X-Frame-Options': 'DENY',
        
        # 內容安全策略
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'",
        
        # 強制 HTTPS
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        
        # 防止 MIME 嗅探
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        
        # 權限策略
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }


# ============================================================
# 7. 安全裝飾器
# ============================================================

def require_auth(func: Callable) -> Callable:
    """需要認證裝飾器"""
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        # 檢查認證（假設 self 有 get_current_user 方法）
        user = getattr(self, 'get_current_user', lambda: None)()
        if not user:
            audit_log(SecurityAudit.EVENT_PERMISSION_DENIED,
                     details={'reason': 'no_auth', 'path': str(args)})
            return {'error': '需要登入', 'code': 401}
        return func(self, *args, **kwargs)
    return wrapper


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """速率限制裝飾器"""
    requests = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 取得識別鍵（IP 或 user_id）
            key = kwargs.get('ip', 'unknown')
            now = time.time()
            
            if key not in requests:
                requests[key] = []
            
            # 清理過期記錄
            requests[key] = [t for t in requests[key] if now - t < window_seconds]
            
            # 檢查是否超過限制
            if len(requests[key]) >= max_requests:
                audit_log(SecurityAudit.EVENT_SUSPICIOUS,
                         ip_address=key,
                         details={'reason': 'rate_limit_exceeded'},
                         severity='warning')
                return {'error': '請求過於頻繁', 'code': 429}
            
            requests[key].append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 📚 知識點
# -----------
# 1. Fernet 加密：
#    - AES-128-CBC + HMAC-SHA256
#    - 自帶完整性驗證
#    - 適合對稱加密場景
#
# 2. PBKDF2 金鑰派生：
#    - 從密碼派生安全金鑰
#    - iterations 增加暴力破解難度
#    - salt 防止彩虹表攻擊
#
# 3. SQL 注入防護：
#    - 參數化查詢是最佳實踐
#    - 白名單驗證識別符
#    - 永不信任用戶輸入
#
# 4. 安全響應頭：
#    - CSP 防止 XSS
#    - HSTS 強制 HTTPS
#    - X-Frame-Options 防點擊劫持
#
# 5. 審計日誌：
#    - 記錄安全相關事件
#    - 便於事後追查
#    - 檢測異常模式
