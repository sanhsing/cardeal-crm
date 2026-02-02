"""
車行寶 CRM v5.0 - Webhook 處理模組
北斗七星文創數位 × 織明
"""
from typing import Dict, List, Any, Optional, Union, Callable

import json
from services import line_service
from models import get_connection

def handle_line(router, body, signature):
    """處理 LINE Webhook"""
    # 驗證簽名
    if not line_service.verify_signature(body, signature):
        router.send_json({'error': 'Invalid signature'}, 403)
        return
    
    try:
        data = json.loads(body.decode('utf-8'))
        events = data.get('events', [])
        
        for event in events:
            process_line_event(event)
        
        router.send_json({'success': True})
    except Exception as e:
        print(f"Webhook error: {e}")
        router.send_json({'error': str(e)}, 500)

def process_line_event(event):
    """處理單個 LINE 事件"""
    event_type = event.get('type')
    
    if event_type == 'message':
        handle_message(event)
    elif event_type == 'follow':
        handle_follow(event)
    elif event_type == 'unfollow':
        handle_unfollow(event)

def handle_message(event):
    """處理訊息事件"""
    reply_token = event.get('replyToken')
    user_id = event['source'].get('userId')
    message = event.get('message', {})
    
    if message.get('type') == 'text':
        text = message.get('text', '')
        
        # 簡單的自動回覆
        if '查詢' in text or '詢問' in text:
            line_service.reply_message(reply_token, [
                {'type': 'text', 'text': '感謝您的詢問！我們的業務人員會盡快與您聯繫。'}
            ])
        elif '營業時間' in text:
            line_service.reply_message(reply_token, [
                {'type': 'text', 'text': '營業時間：週一至週六 9:00-21:00，週日 10:00-18:00'}
            ])

def handle_follow(event):
    """處理加入好友事件"""
    user_id = event['source'].get('userId')
    
    # 取得用戶資料
    profile = line_service.get_profile(user_id)
    
    if profile:
        # 發送歡迎訊息
        welcome_flex = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"歡迎 {profile.get('displayName', '您')}！",
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "text",
                        "text": "感謝您加入我們的 LINE 好友！有任何問題歡迎隨時詢問。",
                        "wrap": True,
                        "margin": "md",
                        "size": "sm",
                        "color": "#666666"
                    }
                ]
            }
        }
        
        line_service.send_flex(user_id, "歡迎加入", welcome_flex)

def handle_unfollow(event):
    """處理取消好友事件"""
    user_id = event['source'].get('userId')
    # 可以記錄或做其他處理
    print(f"User unfollowed: {user_id}")
