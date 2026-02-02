"""
車行寶 CRM v5.1 - 認證處理器
北斗七星文創數位 × 織明
"""
from typing import Dict, List, Any, Optional, Union, Callable

import re
from .base import BaseHandler
from models import verify_login, create_session, create_tenant
from services import telegram_service

def handle_login(handler):
    """處理登入"""
    data = BaseHandler.get_json_body(handler)
    
    code = data.get('code', '').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()
    
    # 驗證必填
    if not all([code, phone, password]):
        return BaseHandler.send_json(handler, {
            'success': False, 
            'error': '請填寫完整資料'
        })
    
    # 驗證登入
    result = verify_login(code, phone, password)
    
    if result['success']:
        # 建立 Session
        token = create_session(
            result['user_id'],
            {
                'user_id': result['user_id'],
                'user_name': result['user_name'],
                'role': result['role'],
                'tenant_id': result['tenant_id'],
                'tenant_code': result['tenant_code'],
                'tenant_name': result['tenant_name'],
                'db_path': result['db_path'],
                'plan': result['plan'],
            },
            result['tenant_id']
        )
        result['token'] = token
    
    BaseHandler.send_json(handler, result)


def handle_register(handler):
    """處理註冊"""
    data = BaseHandler.get_json_body(handler)
    
    code = data.get('code', '').strip().lower()
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()
    
    # 驗證必填
    if not all([code, name, phone, password]):
        return BaseHandler.send_json(handler, {
            'success': False, 
            'error': '請填寫完整資料'
        })
    
    # 驗證店家代碼格式
    if not re.match(r'^[a-z0-9_]{3,20}$', code):
        return BaseHandler.send_json(handler, {
            'success': False, 
            'error': '店家代碼格式錯誤（小寫英數字及底線，3-20字元）'
        })
    
    # 驗證手機格式
    if not re.match(r'^09\d{8}$', phone):
        return BaseHandler.send_json(handler, {
            'success': False, 
            'error': '手機號碼格式錯誤'
        })
    
    # 驗證密碼長度
    if len(password) < 4:
        return BaseHandler.send_json(handler, {
            'success': False, 
            'error': '密碼至少需要4個字元'
        })
    
    # 建立租戶
    result = create_tenant(code, name, phone, password)
    
    if result['success']:
        # 發送通知
        telegram_service.notify_new_tenant(name, code)
    
    BaseHandler.send_json(handler, result)


def handle_logout(handler):
    """處理登出"""
    from models import delete_session
    
    session = BaseHandler.get_session(handler)
    if session:
        # 刪除 session（需要 token）
        auth_header = handler.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            delete_session(token)
    
    BaseHandler.send_json(handler, {'success': True})


def handle_me(handler):
    """取得當前使用者資訊"""
    session = BaseHandler.require_auth(handler)
    if not session:
        return
    
    BaseHandler.send_json(handler, {
        'success': True,
        'user': session['data']
    })


# 📚 知識點
# -----------
# 1. re.match：正則表達式匹配
#    - r'^[a-z0-9_]{3,20}$'
#    - ^：開頭
#    - [a-z0-9_]：小寫字母、數字、底線
#    - {3,20}：3到20個字元
#    - $：結尾
#
# 2. .strip()：去除頭尾空白
#    - "  hello  ".strip() → "hello"
#
# 3. .lower()：轉小寫
#    - "ABC".lower() → "abc"
#
# 4. all([a, b, c])：全部為真才返回 True
#    - 用於檢查多個必填欄位
