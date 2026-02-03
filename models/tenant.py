"""
車行寶 CRM v5.1 - 租戶管理模組
北斗七星文創數位 × 織明
"""
from typing import Dict, List, Any, Optional, Union, Callable

import hashlib
import os
from datetime import datetime
import config
from pylib.units.tenant_rules import validate_tenant_code
from .database import get_connection

def get_tenant_by_code(code: str) -> Any:
    """根據代碼取得租戶"""
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM tenants WHERE code = ? AND status = "active"', (code,))
    tenant = c.fetchone()
    conn.close()
    return dict(tenant) if tenant else None


def get_tenant_by_id(tenant_id: int) -> Any:
    """根據 ID 取得租戶"""
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM tenants WHERE id = ?', (tenant_id,))
    tenant = c.fetchone()
    conn.close()
    return dict(tenant) if tenant else None


def get_all_tenants(status: str = 'active') -> List[Dict[str, Any]]:
    """取得所有租戶"""
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM tenants WHERE status = ? ORDER BY created_at DESC', (status,))
    tenants = [dict(row) for row in c.fetchall()]
    conn.close()
    return tenants


def create_tenant(code: str, name: str, admin_phone, admin_password, admin_name='管理員') -> Any:
    """建立新租戶"""
    from .schema import init_tenant_database
    
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    
    try:
        db_path = os.path.join(config.DATA_DIR, f'tenant_{code}.db')
        
        c.execute('''INSERT INTO tenants (code, name, db_path, owner_name, owner_phone) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (code, name, db_path, admin_name, admin_phone))
        tenant_id = c.lastrowid
        conn.commit()
        
        # 初始化租戶資料庫
        init_tenant_database(code, admin_phone, admin_password, admin_name)
        
        return {'success': True, 'tenant_id': tenant_id, 'code': code}
    except Exception as e:
        if 'UNIQUE constraint' in str(e):
            return {'success': False, 'error': '店家代碼已存在'}
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


def update_tenant(tenant_id, **kwargs) -> bool:
    """更新租戶資料"""
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    
    fields = []
    values = []
    
    allowed = ['name', 'plan', 'plan_expires', 'line_channel_secret', 
               'line_channel_access_token', 'status']
    
    for key, value in kwargs.items():
        if key in allowed:
            fields.append(f'{key} = ?')
            values.append(value)
    
    if not fields:
        conn.close()
        return {'success': False, 'error': '沒有可更新的欄位'}
    
    values.append(tenant_id)
    sql = f'UPDATE tenants SET {", ".join(fields)} WHERE id = ?'
    
    c.execute(sql, values)
    conn.commit()
    conn.close()
    
    return {'success': True}


def verify_login(code, phone, password) -> bool:
    """驗證登入"""
    tenant = get_tenant_by_code(code)
    if not tenant:
        return {'success': False, 'error': '店家代碼不存在'}
    
    # 驗證使用者
    conn = get_connection(tenant['db_path'])
    c = conn.cursor()
    
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    c.execute('''SELECT id, name, role, permissions FROM users 
                 WHERE phone = ? AND password = ? AND status = "active"''',
              (phone, pwd_hash))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return {'success': False, 'error': '帳號或密碼錯誤'}
    
    # 更新最後登入時間
    conn = get_connection(tenant['db_path'])
    c = conn.cursor()
    c.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
    conn.commit()
    conn.close()
    
    return {
        'success': True,
        'tenant_id': tenant['id'],
        'tenant_code': tenant['code'],
        'tenant_name': tenant['name'],
        'db_path': tenant['db_path'],
        'user_id': user['id'],
        'user_name': user['name'],
        'role': user['role'],
        'permissions': user['permissions'],
        'plan': tenant['plan'],
        'plan_expires': tenant['plan_expires']
    }


def check_plan_features(tenant_id, feature) -> bool:
    """檢查租戶是否有某功能權限"""
    tenant = get_tenant_by_id(tenant_id)
    if not tenant:
        return False
    
    plan = tenant.get('plan', 'free')
    plan_config = config.PLANS.get(f'{plan}_monthly', config.PLANS.get('free', {}))
    
    # 檢查是否過期
    if tenant.get('plan_expires'):
        expires = datetime.fromisoformat(tenant['plan_expires'])
        if datetime.now() > expires:
            return False
    
    return feature in plan_config.get('features', [])


# 📚 知識點
# -----------
# 1. **kwargs：關鍵字參數收集
#    - def func(**kwargs) 可接收任意數量的 key=value 參數
#    - 在函數內 kwargs 是一個字典
#    - 呼叫：update_tenant(1, name='新名稱', plan='pro')
#
# 2. hashlib.sha256()：密碼雜湊
#    - 單向加密，無法逆向解密
#    - .hexdigest() 轉成16進制字串
#    - 注意：實務上應加 salt（隨機字串）更安全
#
# 3. datetime.fromisoformat()：解析 ISO 格式日期
#    - '2026-02-02T10:30:00' → datetime 物件
#    - 可用於比較：datetime.now() > expires
#
# 4. UNIQUE constraint：資料庫唯一限制
#    - 違反時會拋出錯誤
#    - 用 try/except 捕捉並給予友善提示
