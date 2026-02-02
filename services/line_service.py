"""
車行寶 CRM v5.0 - LINE 服務模組
北斗七星文創數位 × 織明
"""
import json
import hmac
import hashlib
import base64
import urllib.request
import urllib.parse
import config
from models import get_connection, get_tenant_by_id

def verify_signature(body: bytes, signature: str) -> bool:
    """驗證 LINE Webhook 簽名"""
    if not config.LINE_CHANNEL_SECRET:
        return True
    
    hash_value = hmac.new(
        config.LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    
    expected = base64.b64encode(hash_value).decode('utf-8')
    return hmac.compare_digest(signature, expected)

def get_access_token(tenant_id=None):
    """取得 LINE Access Token"""
    if tenant_id:
        tenant = get_tenant_by_id(tenant_id)
        if tenant and tenant.get('line_channel_access_token'):
            return tenant['line_channel_access_token']
    return config.LINE_CHANNEL_ACCESS_TOKEN

def send_message(user_id: str, messages: list, tenant_id: str = None) -> dict:
    """發送 LINE 訊息"""
    access_token = get_access_token(tenant_id)
    if not access_token:
        return {'success': False, 'error': 'LINE 未設定'}
    
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    data = json.dumps({
        'to': user_id,
        'messages': messages
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {'success': True}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {'success': False, 'error': error_body}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def send_text(user_id: str, text: str, tenant_id: str = None) -> dict:
    """發送文字訊息"""
    return send_message(user_id, [{'type': 'text', 'text': text}], tenant_id)

def send_flex(user_id: str, alt_text: str, contents: dict, tenant_id: str = None) -> dict:
    """發送 Flex Message"""
    return send_message(user_id, [{
        'type': 'flex',
        'altText': alt_text,
        'contents': contents
    }], tenant_id)

def reply_message(reply_token: str, messages: list) -> dict:
    """回覆訊息"""
    if not config.LINE_CHANNEL_ACCESS_TOKEN:
        return {'success': False, 'error': 'LINE 未設定'}
    
    url = 'https://api.line.me/v2/bot/message/reply'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}'
    }
    
    data = json.dumps({
        'replyToken': reply_token,
        'messages': messages
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_profile(user_id: str) -> dict:
    """取得用戶資料"""
    if not config.LINE_CHANNEL_ACCESS_TOKEN:
        return None
    
    url = f'https://api.line.me/v2/bot/profile/{user_id}'
    headers = {
        'Authorization': f'Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except:
        return None

def generate_bind_url(tenant_id: str, customer_id: str, base_url: str) -> str:
    """產生綁定連結"""
    import secrets
    token = secrets.token_urlsafe(32)
    
    # 儲存 token（這裡簡化處理，實際應存入資料庫）
    return f"{base_url}/line/bind?tenant={tenant_id}&token={token}&cid={customer_id}"

def create_deal_flex(customer_name: str, vehicle_info: str, amount: int, deal_type: str) -> dict:
    """建立交易通知 Flex Message"""
    type_text = '售出' if deal_type == 'sell' else '收購'
    type_color = '#10b981' if deal_type == 'sell' else '#3b82f6'
    
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"🚗 車輛{type_text}通知",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff"
                }
            ],
            "backgroundColor": type_color,
            "paddingAll": "15px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": vehicle_info,
                    "weight": "bold",
                    "size": "md",
                    "wrap": True
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "客戶", "size": "sm", "color": "#888888", "flex": 1},
                        {"type": "text", "text": customer_name, "size": "sm", "flex": 2, "align": "end"}
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "sm",
                    "contents": [
                        {"type": "text", "text": "金額", "size": "sm", "color": "#888888", "flex": 1},
                        {"type": "text", "text": f"${amount:,}", "size": "sm", "weight": "bold", "color": type_color, "flex": 2, "align": "end"}
                    ]
                }
            ],
            "paddingAll": "15px"
        }
    }

def create_followup_flex(customer_name: str, last_contact: str, interest: str) -> dict:
    """建立跟進提醒 Flex Message"""
    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📋 跟進提醒",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff"
                }
            ],
            "backgroundColor": "#f59e0b",
            "paddingAll": "15px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": customer_name,
                    "weight": "bold",
                    "size": "md"
                },
                {
                    "type": "text",
                    "text": f"上次聯繫：{last_contact or '無記錄'}",
                    "size": "sm",
                    "color": "#888888",
                    "margin": "sm"
                },
                {
                    "type": "text",
                    "text": f"興趣：{interest or '未記錄'}",
                    "size": "sm",
                    "color": "#888888",
                    "margin": "sm",
                    "wrap": True
                }
            ],
            "paddingAll": "15px"
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "立即跟進",
                        "uri": "tel:0900000000"
                    },
                    "style": "primary",
                    "color": "#f59e0b"
                }
            ],
            "paddingAll": "10px"
        }
    }
