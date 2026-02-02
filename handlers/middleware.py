"""
車行寶 CRM v5.1 - 中間件模組
北斗七星文創數位 × 織明

功能：請求/回應處理管道（壓縮、日誌、錯誤處理）
"""
from typing import Dict, List, Any, Optional, Union, Callable

import gzip
import json
import time
import traceback
from functools import wraps
from datetime import datetime
import config
from services import security_service

# ===== 請求日誌 =====

class RequestLogger:
    """請求日誌記錄器"""
    
    @staticmethod
    def log_request(handler, start_time, status_code, response_size=0):
        """記錄請求日誌"""
        duration = (time.time() - start_time) * 1000  # 毫秒
        
        client_ip = security_service.get_client_ip(handler)
        method = handler.command
        path = handler.path
        user_agent = handler.headers.get('User-Agent', '-')[:100]
        
        # 格式化日誌
        log_line = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{client_ip} {method} {path} "
            f"{status_code} {response_size}B {duration:.1f}ms"
        )
        
        if config.DEBUG:
            print(log_line)
        
        # 慢請求警告
        if duration > 1000:
            print(f"⚠️ 慢請求: {path} ({duration:.0f}ms)")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'ip': client_ip,
            'method': method,
            'path': path,
            'status': status_code,
            'size': response_size,
            'duration_ms': round(duration, 2),
            'user_agent': user_agent
        }


# ===== GZIP 壓縮 =====

class GzipMiddleware:
    """GZIP 壓縮中間件"""
    
    MIN_SIZE = 1024  # 最小壓縮大小（1KB）
    COMPRESSIBLE_TYPES = [
        'text/html', 'text/css', 'text/javascript',
        'application/json', 'application/javascript',
        'text/plain', 'text/xml', 'application/xml'
    ]
    
    @staticmethod
    def should_compress(handler, content_type, content_length):
        """判斷是否應該壓縮"""
        # 檢查大小
        if content_length < GzipMiddleware.MIN_SIZE:
            return False
        
        # 檢查類型
        if not any(t in content_type for t in GzipMiddleware.COMPRESSIBLE_TYPES):
            return False
        
        # 檢查客戶端是否支援
        accept_encoding = handler.headers.get('Accept-Encoding', '')
        return 'gzip' in accept_encoding
    
    @staticmethod
    def compress(data):
        """壓縮資料"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return gzip.compress(data)


# ===== 錯誤處理 =====

class ErrorHandler:
    """統一錯誤處理器"""
    
    @staticmethod
    def handle_exception(handler, exc, include_trace=False):
        """處理例外"""
        error_id = f"ERR-{int(time.time())}"
        
        # 記錄錯誤
        error_info = {
            'error_id': error_id,
            'type': type(exc).__name__,
            'message': str(exc),
            'path': handler.path,
            'method': handler.command,
            'timestamp': datetime.now().isoformat()
        }
        
        if include_trace or config.DEBUG:
            error_info['traceback'] = traceback.format_exc()
        
        # 輸出到控制台
        print(f"❌ Error [{error_id}]: {error_info['type']}: {error_info['message']}")
        if config.DEBUG:
            traceback.print_exc()
        
        # 返回給客戶端的訊息
        client_message = {
            'success': False,
            'error': '系統發生錯誤，請稍後再試',
            'error_id': error_id
        }
        
        if config.DEBUG:
            client_message['debug'] = {
                'type': error_info['type'],
                'message': error_info['message']
            }
        
        return client_message, error_info
    
    @staticmethod
    def http_error(status_code, message=None):
        """HTTP 錯誤回應"""
        messages = {
            400: '請求格式錯誤',
            401: '請先登入',
            403: '沒有權限',
            404: '找不到資源',
            405: '不支援的請求方法',
            429: '請求過於頻繁',
            500: '系統錯誤',
            502: '閘道錯誤',
            503: '服務暫時不可用'
        }
        
        return {
            'success': False,
            'error': message or messages.get(status_code, '未知錯誤'),
            'code': status_code
        }


# ===== CORS 處理 =====

class CORSMiddleware:
    """CORS 跨域處理"""
    
    DEFAULT_ORIGINS = ['*']
    DEFAULT_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    DEFAULT_HEADERS = ['Content-Type', 'Authorization', 'X-CSRF-Token']
    
    def __init__(self, origins=None, methods=None, headers=None, credentials=False):
        self.origins = origins or self.DEFAULT_ORIGINS
        self.methods = methods or self.DEFAULT_METHODS
        self.headers = headers or self.DEFAULT_HEADERS
        self.credentials = credentials
    
    def add_cors_headers(self, handler):
        """添加 CORS 標頭"""
        origin = handler.headers.get('Origin', '*')
        
        # 檢查來源是否允許
        if '*' in self.origins or origin in self.origins:
            handler.send_header('Access-Control-Allow-Origin', 
                              origin if self.credentials else self.origins[0])
        
        handler.send_header('Access-Control-Allow-Methods', 
                          ', '.join(self.methods))
        handler.send_header('Access-Control-Allow-Headers', 
                          ', '.join(self.headers))
        
        if self.credentials:
            handler.send_header('Access-Control-Allow-Credentials', 'true')
        
        handler.send_header('Access-Control-Max-Age', '86400')


# ===== 安全標頭 =====

class SecurityHeaders:
    """安全相關 HTTP 標頭"""
    
    HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:;",
    }
    
    @staticmethod
    def add_security_headers(handler):
        """添加安全標頭"""
        for key, value in SecurityHeaders.HEADERS.items():
            handler.send_header(key, value)


# ===== 請求計時裝飾器 =====

def timed(func):
    """計時裝飾器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = (time.time() - start) * 1000
        
        if duration > 100:  # 超過 100ms 記錄
            print(f"⏱️ {func.__name__}: {duration:.1f}ms")
        
        return result
    return wrapper


# ===== 請求上下文 =====

class RequestContext:
    """請求上下文（存儲請求相關資訊）"""
    
    def __init__(self, handler: Any) -> None:
        self.start_time = time.time()
        self.handler = handler
        self.ip = security_service.get_client_ip(handler)
        self.user_id = None
        self.tenant_id = None
        self.errors = []
    
    def set_user(self, user_id, tenant_id):
        """設定使用者資訊"""
        self.user_id = user_id
        self.tenant_id = tenant_id
    
    def add_error(self, error):
        """添加錯誤"""
        self.errors.append(error)
    
    @property
    def duration_ms(self):
        """請求耗時（毫秒）"""
        return (time.time() - self.start_time) * 1000


# 📚 知識點
# -----------
# 1. 中間件（Middleware）：
#    - 請求/回應處理管道
#    - 每個請求都會經過
#    - 可疊加多個中間件
#
# 2. GZIP 壓縮：
#    - gzip.compress()：壓縮資料
#    - 減少傳輸量 50-90%
#    - 只壓縮文字類型，圖片已壓縮
#
# 3. CORS (Cross-Origin Resource Sharing)：
#    - 跨域資源共享
#    - 瀏覽器安全機制
#    - 伺服器設定允許的來源
#
# 4. CSP (Content Security Policy)：
#    - 防止 XSS 攻擊
#    - 限制可載入的資源來源
#    - default-src 'self'：只允許同源
#
# 5. X-Frame-Options：
#    - 防止點擊劫持（Clickjacking）
#    - DENY：禁止在 iframe 中載入
#
# 6. traceback.format_exc()：
#    - 格式化例外堆疊追蹤
#    - 方便除錯
#    - 生產環境不應顯示給用戶
