"""
車行寶 CRM v5.0 - Session 管理模組
北斗七星文創數位 × 織明
"""
import secrets
import sqlite3
from datetime import datetime, timedelta

# 記憶體 Session 存儲
_sessions = {}

def create_session(user_id, data, tenant_id, expires_hours=24):
    """建立 Session"""
    token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(hours=expires_hours)
    
    _sessions[token] = {
        'user_id': user_id,
        'tenant_id': tenant_id,
        'data': data,
        'created_at': datetime.now().isoformat(),
        'expires_at': expires_at.isoformat()
    }
    
    return token

def get_session(token):
    """取得 Session"""
    if not token or token not in _sessions:
        return None
    
    session = _sessions[token]
    
    # 檢查過期
    expires_at = datetime.fromisoformat(session['expires_at'])
    if datetime.now() > expires_at:
        del _sessions[token]
        return None
    
    return session

def delete_session(token):
    """刪除 Session"""
    if token in _sessions:
        del _sessions[token]
        return True
    return False

def extend_session(token, hours=24):
    """延長 Session"""
    if token in _sessions:
        _sessions[token]['expires_at'] = (datetime.now() + timedelta(hours=hours)).isoformat()
        return True
    return False

def cleanup_sessions():
    """清理過期 Session"""
    now = datetime.now()
    expired = [
        token for token, session in _sessions.items()
        if datetime.fromisoformat(session['expires_at']) < now
    ]
    for token in expired:
        del _sessions[token]
    return len(expired)

def log_activity(db_path, user_id, user_name, action, target_type=None, target_id=None, target_name=None, details=''):
    """記錄活動日誌"""
    if not db_path:
        return
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO activity_logs 
                     (user_id, user_name, action, target_type, target_id, target_name, details)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, user_name, action, target_type, target_id, target_name, details))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Log activity error: {e}")
