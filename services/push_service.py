"""
車行寶 CRM v5.2 - Web Push 推播服務
北斗七星文創數位 × 織明

功能：
1. VAPID 金鑰管理
2. 訂閱管理（儲存/刪除）
3. 推播發送
4. 批量推播
"""
import os
import json
import time
import base64
import hashlib
import hmac
import urllib.request
import urllib.error
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any

# 嘗試導入加密庫
try:
    from cryptography.hazmat.primitives.asymmetric import ec, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
    import jwt
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


# ===== 配置 =====

VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_SUBJECT = os.environ.get('VAPID_SUBJECT', 'mailto:admin@cardeal.tw')


# ============================================================
# 1. VAPID 金鑰管理
# ============================================================

class VAPIDManager:
    """VAPID 金鑰管理"""
    
    def __init__(self, public_key: str = None, private_key: str = None, subject: str = None):
        self.public_key = public_key or VAPID_PUBLIC_KEY
        self.private_key = private_key or VAPID_PRIVATE_KEY
        self.subject = subject or VAPID_SUBJECT
    
    def is_configured(self) -> bool:
        """檢查是否已配置"""
        return bool(self.public_key and self.private_key)
    
    def get_public_key(self) -> str:
        """取得公鑰（給前端用）"""
        return self.public_key
    
    def generate_jwt(self, audience: str, expiration: int = 86400) -> str:
        """生成 JWT Token
        
        Args:
            audience: 推播服務 URL（如 https://fcm.googleapis.com）
            expiration: 過期時間（秒）
        """
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography 或 PyJWT 未安裝")
        
        now = int(time.time())
        payload = {
            'aud': audience,
            'exp': now + expiration,
            'sub': self.subject
        }
        
        # Base64 URL decode 私鑰
        private_bytes = base64.urlsafe_b64decode(self.private_key + '==')
        
        # 重建 EC 私鑰
        private_key = ec.derive_private_key(
            int.from_bytes(private_bytes, 'big'),
            ec.SECP256R1(),
            default_backend()
        )
        
        # 簽名 JWT
        token = jwt.encode(payload, private_key, algorithm='ES256')
        
        return token


# 全域 VAPID 管理器
vapid = VAPIDManager()


# ============================================================
# 2. 訂閱管理
# ============================================================

class SubscriptionManager:
    """推播訂閱管理"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_table()
    
    def _ensure_table(self):
        """確保訂閱表存在"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tenant_id INTEGER,
                endpoint TEXT UNIQUE NOT NULL,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                user_agent TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used_at TEXT
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_push_user ON push_subscriptions(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_push_tenant ON push_subscriptions(tenant_id)')
        conn.commit()
        conn.close()
    
    def save(self, subscription: Dict, user_id: int = None, tenant_id: int = None) -> Dict:
        """儲存訂閱
        
        Args:
            subscription: {
                'endpoint': str,
                'keys': {'p256dh': str, 'auth': str}
            }
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute('''
                INSERT OR REPLACE INTO push_subscriptions 
                (user_id, tenant_id, endpoint, p256dh, auth, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                tenant_id,
                subscription['endpoint'],
                subscription['keys']['p256dh'],
                subscription['keys']['auth'],
                datetime.now().isoformat()
            ))
            conn.commit()
            return {'success': True, 'message': '訂閱已儲存'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def delete(self, endpoint: str) -> Dict:
        """刪除訂閱"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                'DELETE FROM push_subscriptions WHERE endpoint = ?',
                (endpoint,)
            )
            conn.commit()
            if cursor.rowcount > 0:
                return {'success': True, 'message': '訂閱已刪除'}
            return {'success': False, 'error': '訂閱不存在'}
        finally:
            conn.close()
    
    def get_by_user(self, user_id: int) -> List[Dict]:
        """取得用戶的所有訂閱"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            'SELECT * FROM push_subscriptions WHERE user_id = ?',
            (user_id,)
        )
        subscriptions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return subscriptions
    
    def get_by_tenant(self, tenant_id: int) -> List[Dict]:
        """取得店家的所有訂閱"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            'SELECT * FROM push_subscriptions WHERE tenant_id = ?',
            (tenant_id,)
        )
        subscriptions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return subscriptions
    
    def get_all(self) -> List[Dict]:
        """取得所有訂閱"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM push_subscriptions')
        subscriptions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return subscriptions
    
    def count(self) -> int:
        """訂閱數量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT COUNT(*) FROM push_subscriptions')
        count = cursor.fetchone()[0]
        conn.close()
        return count


# ============================================================
# 3. 推播發送
# ============================================================

class PushSender:
    """推播發送器"""
    
    def __init__(self, vapid_manager: VAPIDManager = None):
        self.vapid = vapid_manager or vapid
    
    def send(self, subscription: Dict, payload: Dict, ttl: int = 86400) -> Dict:
        """發送單一推播
        
        Args:
            subscription: 訂閱資訊
            payload: 推播內容 {'title': str, 'body': str, 'url': str, ...}
            ttl: 存活時間（秒）
        """
        if not self.vapid.is_configured():
            return {'success': False, 'error': 'VAPID 未配置'}
        
        endpoint = subscription.get('endpoint', '')
        
        # 解析推播服務
        from urllib.parse import urlparse
        parsed = urlparse(endpoint)
        audience = f"{parsed.scheme}://{parsed.netloc}"
        
        try:
            # 生成 VAPID JWT
            jwt_token = self.vapid.generate_jwt(audience)
            
            # 準備請求
            headers = {
                'Content-Type': 'application/json',
                'TTL': str(ttl),
                'Authorization': f'vapid t={jwt_token},k={self.vapid.public_key}',
            }
            
            data = json.dumps(payload).encode('utf-8')
            
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return {
                    'success': True,
                    'status': response.status,
                    'endpoint': endpoint[:50] + '...'
                }
                
        except urllib.error.HTTPError as e:
            if e.code == 410:  # Gone - 訂閱已失效
                return {'success': False, 'error': 'subscription_expired', 'code': 410}
            return {'success': False, 'error': f'HTTP {e.code}', 'code': e.code}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_to_user(self, db_path: str, user_id: int, payload: Dict) -> Dict:
        """發送給指定用戶的所有裝置"""
        manager = SubscriptionManager(db_path)
        subscriptions = manager.get_by_user(user_id)
        
        results = []
        success_count = 0
        
        for sub in subscriptions:
            subscription = {
                'endpoint': sub['endpoint'],
                'keys': {
                    'p256dh': sub['p256dh'],
                    'auth': sub['auth']
                }
            }
            result = self.send(subscription, payload)
            results.append(result)
            
            if result['success']:
                success_count += 1
            elif result.get('code') == 410:
                # 清理失效訂閱
                manager.delete(sub['endpoint'])
        
        return {
            'success': success_count > 0,
            'total': len(subscriptions),
            'sent': success_count,
            'results': results
        }
    
    def broadcast(self, db_path: str, payload: Dict, tenant_id: int = None) -> Dict:
        """廣播推播
        
        Args:
            tenant_id: 指定店家，None 表示全部
        """
        manager = SubscriptionManager(db_path)
        
        if tenant_id:
            subscriptions = manager.get_by_tenant(tenant_id)
        else:
            subscriptions = manager.get_all()
        
        results = []
        success_count = 0
        
        for sub in subscriptions:
            subscription = {
                'endpoint': sub['endpoint'],
                'keys': {
                    'p256dh': sub['p256dh'],
                    'auth': sub['auth']
                }
            }
            result = self.send(subscription, payload)
            results.append(result)
            
            if result['success']:
                success_count += 1
            elif result.get('code') == 410:
                manager.delete(sub['endpoint'])
        
        return {
            'success': success_count > 0,
            'total': len(subscriptions),
            'sent': success_count
        }


# ============================================================
# 4. 便捷函數
# ============================================================

def get_vapid_public_key() -> Dict:
    """取得 VAPID 公鑰（API 端點用）"""
    if not vapid.is_configured():
        return {
            'success': False,
            'error': 'VAPID 未配置，請先生成金鑰'
        }
    
    return {
        'success': True,
        'publicKey': vapid.get_public_key()
    }


def subscribe(db_path: str, subscription: Dict, 
              user_id: int = None, tenant_id: int = None) -> Dict:
    """訂閱推播"""
    manager = SubscriptionManager(db_path)
    return manager.save(subscription, user_id, tenant_id)


def unsubscribe(db_path: str, endpoint: str) -> Dict:
    """取消訂閱"""
    manager = SubscriptionManager(db_path)
    return manager.delete(endpoint)


def send_push(db_path: str, user_id: int, title: str, body: str, 
              url: str = None, icon: str = None) -> Dict:
    """發送推播給用戶"""
    payload = {
        'title': title,
        'body': body,
        'icon': icon or '/static/icons/icon-192.png',
        'url': url or '/'
    }
    
    sender = PushSender()
    return sender.send_to_user(db_path, user_id, payload)


def broadcast_push(db_path: str, title: str, body: str,
                   tenant_id: int = None, url: str = None) -> Dict:
    """廣播推播"""
    payload = {
        'title': title,
        'body': body,
        'icon': '/static/icons/icon-192.png',
        'url': url or '/'
    }
    
    sender = PushSender()
    return sender.broadcast(db_path, payload, tenant_id)


# 📚 知識點
# -----------
# 1. VAPID (Voluntary Application Server Identification)：
#    - Web Push 的伺服器身份驗證標準
#    - 使用 ECDSA P-256 曲線
#    - JWT Token 包含 aud, exp, sub
#
# 2. 訂閱資訊結構：
#    - endpoint: 推播服務 URL
#    - p256dh: 公鑰（加密用）
#    - auth: 認證密鑰
#
# 3. HTTP 狀態碼：
#    - 201: 推播成功
#    - 410: 訂閱已失效（應刪除）
#    - 429: 請求過多
#
# 4. TTL (Time To Live)：
#    - 推播訊息的存活時間
#    - 超過時間未送達則丟棄
