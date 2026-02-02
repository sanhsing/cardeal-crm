"""
車行寶 CRM v5.1 - 安全中間件
北斗七星文創數位 × 織明

功能：
1. API 限流中間件
2. 安全響應頭
3. 請求審計日誌
4. IP 黑名單
5. SQL 注入檢測
"""
import json
import time
import threading
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from functools import wraps
from collections import defaultdict


# ============================================================
# 1. API 限流中間件（滑動窗口算法）
# ============================================================

class RateLimiter:
    """滑動窗口限流器"""
    
    def __init__(self) -> None:
        self._buckets = defaultdict(list)
        self._lock = threading.Lock()
        
        # 預設限流規則
        self.rules = {
            'default': (100, 60),      # 100 請求/分鐘
            'login': (5, 60),          # 5 次/分鐘
            'register': (3, 300),      # 3 次/5分鐘
            'upload': (10, 60),        # 10 次/分鐘
            'export': (5, 60),         # 5 次/分鐘
            'ai': (30, 60),            # 30 次/分鐘（AI API）
            'report': (20, 60),        # 20 次/分鐘（報表）
        }
    
    def add_rule(self, name: str, requests: int, window_seconds: int) -> None:
        """添加限流規則"""
        self.rules[name] = (requests, window_seconds)
    
    def check(self, key: str, rule_name: str = 'default') -> Tuple[bool, Dict]:
        """檢查是否允許請求
        
        Returns:
            (allowed, info)
            info = {'remaining': int, 'reset_after': int, 'limit': int}
        """
        max_requests, window_seconds = self.rules.get(rule_name, self.rules['default'])
        now = time.time()
        bucket_key = f"{rule_name}:{key}"
        
        with self._lock:
            # 清理過期記錄
            self._buckets[bucket_key] = [
                t for t in self._buckets[bucket_key]
                if now - t < window_seconds
            ]
            
            current_count = len(self._buckets[bucket_key])
            
            if current_count >= max_requests:
                # 超過限制
                oldest = self._buckets[bucket_key][0] if self._buckets[bucket_key] else now
                reset_after = int(window_seconds - (now - oldest))
                return False, {
                    'remaining': 0,
                    'reset_after': reset_after,
                    'limit': max_requests,
                    'rule': rule_name
                }
            
            # 記錄本次請求
            self._buckets[bucket_key].append(now)
            
            return True, {
                'remaining': max_requests - current_count - 1,
                'reset_after': window_seconds,
                'limit': max_requests,
                'rule': rule_name
            }
    
    def get_headers(self, info: Dict) -> Dict[str, str]:
        """生成限流響應頭"""
        return {
            'X-RateLimit-Limit': str(info['limit']),
            'X-RateLimit-Remaining': str(info['remaining']),
            'X-RateLimit-Reset': str(info['reset_after'])
        }
    
    def cleanup(self) -> None:
        """清理過期數據"""
        now = time.time()
        with self._lock:
            empty_keys = []
            for key, timestamps in self._buckets.items():
                rule_name = key.split(':')[0]
                _, window = self.rules.get(rule_name, self.rules['default'])
                self._buckets[key] = [t for t in timestamps if now - t < window]
                if not self._buckets[key]:
                    empty_keys.append(key)
            for key in empty_keys:
                del self._buckets[key]


# 全域限流器
rate_limiter = RateLimiter()


def rate_limit(rule_name: str = 'default', key_func: Callable = None):
    """限流裝飾器
    
    用法：
        @rate_limit('login', key_func=lambda req: req.client_ip)
        def handle_login(request) -> Dict[str, Any]:
            ...
    """
    def decorator(func) -> Any:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 取得限流鍵
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = 'global'
            
            allowed, info = rate_limiter.check(key, rule_name)
            
            if not allowed:
                return {
                    'success': False,
                    'error': '請求過於頻繁，請稍後再試',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'retry_after': info['reset_after'],
                    '_headers': rate_limiter.get_headers(info)
                }
            
            result = func(*args, **kwargs)
            
            # 添加限流頭到響應
            if isinstance(result, dict):
                result['_rate_limit'] = info
            
            return result
        
        return wrapper
    return decorator


# ============================================================
# 2. 安全響應頭
# ============================================================

class SecurityHeaders:
    """安全響應頭管理"""
    
    # 預設安全頭
    DEFAULT_HEADERS = {
        # 防止點擊劫持
        'X-Frame-Options': 'DENY',
        # 防止 MIME 類型嗅探
        'X-Content-Type-Options': 'nosniff',
        # XSS 防護
        'X-XSS-Protection': '1; mode=block',
        # 引用來源政策
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        # 內容安全政策（根據需求調整）
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        # 強制 HTTPS（生產環境開啟）
        # 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        # 權限政策
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }
    
    def __init__(self, custom_headers: Dict = None) -> None:
        self.headers = self.DEFAULT_HEADERS.copy()
        if custom_headers:
            self.headers.update(custom_headers)
    
    def apply(self, response_headers: Dict) -> Dict:
        """套用安全頭到響應"""
        result = response_headers.copy()
        result.update(self.headers)
        return result
    
    def set(self, name: str, value: str):
        """設定單個頭"""
        self.headers[name] = value
    
    def remove(self, name: str):
        """移除頭"""
        if name in self.headers:
            del self.headers[name]
    
    def enable_hsts(self, max_age: int = 31536000):
        """啟用 HSTS"""
        self.headers['Strict-Transport-Security'] = f'max-age={max_age}; includeSubDomains'
    
    def set_cors(self, origins: List[str] = None, methods: List[str] = None) -> None:
        """設定 CORS"""
        if origins:
            self.headers['Access-Control-Allow-Origin'] = ', '.join(origins)
        if methods:
            self.headers['Access-Control-Allow-Methods'] = ', '.join(methods)
        self.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'


# 全域安全頭
security_headers = SecurityHeaders()


# ============================================================
# 3. 請求審計日誌
# ============================================================

class AuditLogger:
    """審計日誌記錄器"""
    
    def __init__(self, max_logs: int = 10000) -> None:
        self.logs = []
        self.max_logs = max_logs
        self._lock = threading.Lock()
        
        # 敏感操作列表
        self.sensitive_operations = [
            'login', 'logout', 'register',
            'password_change', 'password_reset',
            'user_create', 'user_delete', 'user_update',
            'role_change', 'permission_change',
            'export', 'import', 'backup',
            'payment', 'refund',
            'delete', 'bulk_delete'
        ]
    
    def log(self, event_type: str, user_id: int = None, 
            ip: str = None, details: Dict = None,
            success: bool = True, risk_level: str = 'low'):
        """記錄審計事件
        
        Args:
            event_type: 事件類型
            user_id: 用戶 ID
            ip: IP 地址
            details: 詳細資訊
            success: 是否成功
            risk_level: 風險等級 ('low', 'medium', 'high', 'critical')
        """
        # 自動判斷風險等級
        if event_type in self.sensitive_operations and risk_level == 'low':
            risk_level = 'medium'
        if not success and event_type in ['login', 'password_change']:
            risk_level = 'high'
        
        entry = {
            'id': len(self.logs) + 1,
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip': ip,
            'success': success,
            'risk_level': risk_level,
            'details': self._sanitize_details(details)
        }
        
        with self._lock:
            self.logs.append(entry)
            
            # 限制日誌數量
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
        
        # 高風險事件告警
        if risk_level in ('high', 'critical'):
            self._alert(entry)
    
    def _sanitize_details(self, details: Dict) -> Dict:
        """清理敏感資訊"""
        if not details:
            return {}
        
        sanitized = details.copy()
        sensitive_keys = ['password', 'token', 'secret', 'card', 'cvv', 'pin']
        
        for key in sanitized:
            if any(s in key.lower() for s in sensitive_keys):
                sanitized[key] = '***'
        
        return sanitized
    
    def _alert(self, entry: Dict) -> Any:
        """高風險事件告警"""
        # 這裡可以整合 Telegram 通知
        print(f"⚠️ 高風險事件: {entry['event_type']} from {entry['ip']}")
    
    def query(self, event_type: str = None, user_id: int = None,
              risk_level: str = None, limit: int = 100) -> List[Dict]:
        """查詢審計日誌"""
        with self._lock:
            results = self.logs.copy()
        
        if event_type:
            results = [r for r in results if r['event_type'] == event_type]
        if user_id:
            results = [r for r in results if r['user_id'] == user_id]
        if risk_level:
            results = [r for r in results if r['risk_level'] == risk_level]
        
        return list(reversed(results[-limit:]))
    
    def get_stats(self) -> Dict:
        """統計資訊"""
        with self._lock:
            total = len(self.logs)
            if not total:
                return {'total': 0}
            
            by_risk = defaultdict(int)
            by_type = defaultdict(int)
            failures = 0
            
            for log in self.logs:
                by_risk[log['risk_level']] += 1
                by_type[log['event_type']] += 1
                if not log['success']:
                    failures += 1
            
            return {
                'total': total,
                'failures': failures,
                'failure_rate': round(failures / total * 100, 2),
                'by_risk': dict(by_risk),
                'top_events': dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:10])
            }
    
    def export(self, format: str = 'json') -> str:
        """匯出日誌"""
        with self._lock:
            if format == 'json':
                return json.dumps(self.logs, ensure_ascii=False, indent=2)
            elif format == 'csv':
                lines = ['timestamp,event_type,user_id,ip,success,risk_level']
                for log in self.logs:
                    lines.append(f"{log['timestamp']},{log['event_type']},{log['user_id']},{log['ip']},{log['success']},{log['risk_level']}")
                return '\n'.join(lines)
        return ''


# 全域審計日誌
audit_logger = AuditLogger()


def audit(event_type: str, risk_level: str = 'low'):
    """審計裝飾器"""
    def decorator(func) -> Any:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 嘗試從參數取得資訊
            user_id = kwargs.get('user_id')
            ip = kwargs.get('ip', 'unknown')
            
            try:
                result = func(*args, **kwargs)
                success = result.get('success', True) if isinstance(result, dict) else True
                audit_logger.log(event_type, user_id, ip, 
                                {'args': str(args)[:100]}, success, risk_level)
                return result
            except Exception as e:
                audit_logger.log(event_type, user_id, ip,
                                {'error': str(e)}, False, 'high')
                raise
        return wrapper
    return decorator


# ============================================================
# 4. IP 黑名單
# ============================================================

class IPBlacklist:
    """IP 黑名單管理"""
    
    def __init__(self) -> None:
        self.blacklist = set()
        self.whitelist = set()
        self.temp_blocks = {}  # {ip: unblock_time}
        self._lock = threading.Lock()
        
        # 自動封鎖閾值
        self.auto_block_threshold = 10  # 失敗次數
        self.auto_block_window = 300    # 時間窗口（秒）
        self.auto_block_duration = 3600 # 封鎖時長（秒）
        
        self._failures = defaultdict(list)
    
    def add_to_blacklist(self, ip: str) -> None:
        """永久封鎖 IP"""
        with self._lock:
            self.blacklist.add(ip)
    
    def remove_from_blacklist(self, ip: str) -> bool:
        """解除永久封鎖"""
        with self._lock:
            self.blacklist.discard(ip)
    
    def add_to_whitelist(self, ip: str) -> None:
        """加入白名單"""
        with self._lock:
            self.whitelist.add(ip)
    
    def is_blocked(self, ip: str) -> Tuple[bool, str]:
        """檢查 IP 是否被封鎖
        
        Returns:
            (blocked, reason)
        """
        with self._lock:
            # 白名單優先
            if ip in self.whitelist:
                return False, ''
            
            # 永久封鎖
            if ip in self.blacklist:
                return True, 'permanent'
            
            # 臨時封鎖
            if ip in self.temp_blocks:
                if time.time() < self.temp_blocks[ip]:
                    return True, 'temporary'
                else:
                    del self.temp_blocks[ip]
            
            return False, ''
    
    def record_failure(self, ip: str) -> bool:
        """記錄失敗請求，返回是否觸發自動封鎖"""
        now = time.time()
        
        with self._lock:
            # 清理過期記錄
            self._failures[ip] = [
                t for t in self._failures[ip]
                if now - t < self.auto_block_window
            ]
            
            # 記錄本次失敗
            self._failures[ip].append(now)
            
            # 檢查是否超過閾值
            if len(self._failures[ip]) >= self.auto_block_threshold:
                self.temp_blocks[ip] = now + self.auto_block_duration
                self._failures[ip] = []
                return True
            
            return False
    
    def get_blocked_list(self) -> Dict:
        """取得封鎖清單"""
        with self._lock:
            return {
                'permanent': list(self.blacklist),
                'temporary': {ip: datetime.fromtimestamp(t).isoformat() 
                             for ip, t in self.temp_blocks.items()
                             if time.time() < t}
            }


# 全域 IP 黑名單
ip_blacklist = IPBlacklist()


# ============================================================
# 5. SQL 注入檢測
# ============================================================

class SQLInjectionDetector:
    """SQL 注入檢測器"""
    
    # 危險模式
    PATTERNS = [
        r"(\s|^)(OR|AND)\s+\d+\s*=\s*\d+",  # OR 1=1
        r"(\s|^)(OR|AND)\s+['\"].*['\"]\s*=\s*['\"]",  # OR 'a'='a'
        r";\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE)",  # SQL 命令
        r"--\s*$",  # SQL 註解
        r"/\*.*\*/",  # 多行註解
        r"UNION\s+(ALL\s+)?SELECT",  # UNION 注入
        r"SLEEP\s*\(",  # 時間盲注
        r"BENCHMARK\s*\(",  # 性能盲注
        r"LOAD_FILE\s*\(",  # 檔案讀取
        r"INTO\s+OUTFILE",  # 檔案寫入
        r"xp_cmdshell",  # SQL Server 命令執行
    ]
    
    def __init__(self) -> None:
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.PATTERNS]
        self.detected_attacks = []
        self._lock = threading.Lock()
    
    def check(self, value: str) -> Tuple[bool, Optional[str]]:
        """檢查是否含有 SQL 注入
        
        Returns:
            (is_safe, detected_pattern)
        """
        if not value:
            return True, None
        
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(value):
                # 記錄攻擊
                with self._lock:
                    self.detected_attacks.append({
                        'timestamp': datetime.now().isoformat(),
                        'pattern': self.PATTERNS[i],
                        'value': value[:100]
                    })
                return False, self.PATTERNS[i]
        
        return True, None
    
    def check_dict(self, data: Dict) -> Tuple[bool, Optional[str]]:
        """檢查字典中的所有值"""
        for key, value in data.items():
            if isinstance(value, str):
                is_safe, pattern = self.check(value)
                if not is_safe:
                    return False, f"{key}: {pattern}"
            elif isinstance(value, dict):
                is_safe, pattern = self.check_dict(value)
                if not is_safe:
                    return False, pattern
        return True, None
    
    def sanitize(self, value: str) -> str:
        """清理危險字元"""
        if not value:
            return value
        
        # 轉義單引號
        value = value.replace("'", "''")
        # 移除 SQL 註解
        value = re.sub(r'--.*$', '', value)
        value = re.sub(r'/\*.*?\*/', '', value)
        
        return value
    
    def get_attack_logs(self, limit: int = 50) -> List[Dict]:
        """取得攻擊日誌"""
        with self._lock:
            return list(reversed(self.detected_attacks[-limit:]))


# 全域 SQL 注入檢測器
sql_injection_detector = SQLInjectionDetector()


# ============================================================
# 6. 整合中間件
# ============================================================

class SecurityMiddleware:
    """整合安全中間件"""
    
    def __init__(self) -> None:
        self.rate_limiter = rate_limiter
        self.security_headers = security_headers
        self.audit_logger = audit_logger
        self.ip_blacklist = ip_blacklist
        self.sql_detector = sql_injection_detector
    
    def process_request(self, request: Dict) -> Tuple[bool, Optional[Dict]]:
        """處理請求
        
        Returns:
            (allowed, error_response)
        """
        ip = request.get('ip', 'unknown')
        path = request.get('path', '')
        method = request.get('method', 'GET')
        body = request.get('body', {})
        
        # 1. IP 黑名單檢查
        blocked, reason = self.ip_blacklist.is_blocked(ip)
        if blocked:
            self.audit_logger.log('blocked_request', ip=ip, 
                                 details={'reason': reason}, 
                                 success=False, risk_level='high')
            return False, {
                'success': False,
                'error': '您的 IP 已被封鎖',
                'code': 'IP_BLOCKED'
            }
        
        # 2. SQL 注入檢測
        if body:
            is_safe, pattern = self.sql_detector.check_dict(body)
            if not is_safe:
                self.audit_logger.log('sql_injection_attempt', ip=ip,
                                     details={'pattern': pattern},
                                     success=False, risk_level='critical')
                self.ip_blacklist.record_failure(ip)
                return False, {
                    'success': False,
                    'error': '請求包含非法字元',
                    'code': 'INVALID_INPUT'
                }
        
        # 3. 限流檢查
        rule_name = self._get_rule_name(path)
        allowed, info = self.rate_limiter.check(ip, rule_name)
        if not allowed:
            return False, {
                'success': False,
                'error': '請求過於頻繁',
                'code': 'RATE_LIMIT_EXCEEDED',
                'retry_after': info['reset_after'],
                '_headers': self.rate_limiter.get_headers(info)
            }
        
        return True, None
    
    def process_response(self, response: Dict) -> Dict:
        """處理響應"""
        headers = response.get('headers', {})
        response['headers'] = self.security_headers.apply(headers)
        return response
    
    def _get_rule_name(self, path: str) -> str:
        """根據路徑決定限流規則"""
        if '/login' in path:
            return 'login'
        if '/register' in path:
            return 'register'
        if '/upload' in path:
            return 'upload'
        if '/export' in path:
            return 'export'
        if '/ai/' in path:
            return 'ai'
        if '/report' in path:
            return 'report'
        return 'default'


# 全域安全中間件
security_middleware = SecurityMiddleware()


# 📚 知識點
# -----------
# 1. 滑動窗口限流：
#    - 記錄每個請求的時間戳
#    - 只計算時間窗口內的請求數
#    - 比固定窗口更平滑
#
# 2. 安全響應頭：
#    - X-Frame-Options: 防止點擊劫持
#    - CSP: 限制資源載入來源
#    - HSTS: 強制使用 HTTPS
#
# 3. 審計日誌：
#    - 記錄敏感操作
#    - 風險等級分類
#    - 自動告警機制
#
# 4. SQL 注入檢測：
#    - 正則表達式匹配危險模式
#    - 檢測常見攻擊手法
#    - 自動封鎖惡意 IP
#
# 5. IP 黑名單：
#    - 永久封鎖 + 臨時封鎖
#    - 自動封鎖（失敗次數閾值）
#    - 白名單優先
