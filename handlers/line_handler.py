"""
車行寶 CRM v5.2 - LINE Webhook Handler
北斗七星文創數位 × 織明

功能：
1. 簽名驗證
2. 事件處理（訊息、追蹤、取消追蹤）
3. 自動回覆
"""
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

import os
import json
import hmac
import hashlib
import base64
from handlers.base import BaseHandler
from services import line_service
import config


# ===== 配置 =====
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')


class LineWebhookHandler(BaseHandler):
    """LINE Webhook Handler"""
    
    def handle_request(self, method: str, path: str, params: dict = None,
                       body: bytes = None, headers: dict = None):
        """處理 Webhook 請求"""
        
        # POST /api/webhook/line
        if method != 'POST':
            return self.error_response(405, 'Method Not Allowed')
        
        headers = headers or {}
        
        # 1. 驗證簽名
        signature = headers.get('X-Line-Signature', '')
        if not self._verify_signature(body, signature):
            return self.error_response(403, 'Invalid signature')
        
        # 2. 解析事件
        try:
            data = json.loads(body.decode('utf-8')) if body else {}
        except json.JSONDecodeError:
            return self.error_response(400, 'Invalid JSON')
        
        events = data.get('events', [])
        
        # 3. 處理每個事件
        results = []
        for event in events:
            result = self._handle_event(event)
            results.append(result)
        
        return self.json_response({
            'success': True,
            'processed': len(results)
        })
    
    def _verify_signature(self, body: bytes, signature: str) -> bool:
        """驗證 LINE 簽名
        
        使用 HMAC-SHA256 驗證請求來源
        """
        if not LINE_CHANNEL_SECRET:
            # 開發環境：跳過驗證
            if os.environ.get('ENV') == 'development':
                return True
            return False
        
        if not signature:
            return False
        
        # 計算 HMAC-SHA256
        hash_value = hmac.new(
            LINE_CHANNEL_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest()
        
        expected_signature = base64.b64encode(hash_value).decode('utf-8')
        
        # 常數時間比較，防止時序攻擊
        return hmac.compare_digest(signature, expected_signature)
    
    def _handle_event(self, event: dict) -> dict:
        """處理單一事件"""
        event_type = event.get('type', '')
        
        handlers = {
            'message': self._handle_message,
            'follow': self._handle_follow,
            'unfollow': self._handle_unfollow,
            'postback': self._handle_postback,
            'join': self._handle_join,
            'leave': self._handle_leave,
        }
        
        handler = handlers.get(event_type)
        if handler:
            return handler(event)
        
        return {'type': event_type, 'handled': False}
    
    def _handle_message(self, event: dict) -> dict:
        """處理訊息事件"""
        reply_token = event.get('replyToken', '')
        source = event.get('source', {})
        message = event.get('message', {})
        
        user_id = source.get('userId', '')
        msg_type = message.get('type', '')
        
        # 文字訊息
        if msg_type == 'text':
            text = message.get('text', '')
            response = self._process_text_message(text, user_id)
            
            if response and reply_token:
                line_service.reply_message(reply_token, response)
        
        return {
            'type': 'message',
            'msg_type': msg_type,
            'user_id': user_id,
            'handled': True
        }
    
    def _process_text_message(self, text: str, user_id: str) -> str:
        """處理文字訊息"""
        text = text.strip().lower()
        
        # 關鍵字回覆
        keywords = {
            '你好': '您好！歡迎使用車行寶 CRM 🚗',
            'hello': '您好！歡迎使用車行寶 CRM 🚗',
            'hi': '您好！歡迎使用車行寶 CRM 🚗',
            '幫助': '📋 可用指令：\n• 查詢 - 查詢車輛\n• 綁定 - 綁定帳號\n• 客服 - 聯繫客服',
            'help': '📋 可用指令：\n• 查詢 - 查詢車輛\n• 綁定 - 綁定帳號\n• 客服 - 聯繫客服',
            '查詢': '請輸入車牌號碼或車款名稱進行查詢',
            '綁定': f'請點擊以下連結綁定帳號：\n{os.environ.get("BASE_URL", "https://cardeal.tw")}/line-bind?uid={user_id}',
            '客服': '📞 客服電話：0800-XXX-XXX\n📧 客服信箱：service@cardeal.tw',
        }
        
        for keyword, response in keywords.items():
            if keyword in text:
                return response
        
        # 預設回覆
        return None  # 不回覆
    
    def _handle_follow(self, event: dict) -> dict:
        """處理追蹤事件"""
        reply_token = event.get('replyToken', '')
        source = event.get('source', {})
        user_id = source.get('userId', '')
        
        # 發送歡迎訊息
        welcome = """🎉 歡迎加入車行寶！

我是車行寶 CRM 小幫手，可以幫您：
• 📱 查詢車輛資訊
• 🔔 接收重要通知
• 💬 快速聯繫業務

輸入「幫助」查看更多功能！"""
        
        if reply_token:
            line_service.reply_message(reply_token, welcome)
        
        # 記錄新追蹤
        self._log_follow(user_id)
        
        return {'type': 'follow', 'user_id': user_id, 'handled': True}
    
    def _handle_unfollow(self, event: dict) -> dict:
        """處理取消追蹤事件"""
        source = event.get('source', {})
        user_id = source.get('userId', '')
        
        # 記錄取消追蹤
        self._log_unfollow(user_id)
        
        return {'type': 'unfollow', 'user_id': user_id, 'handled': True}
    
    def _handle_postback(self, event: dict) -> dict:
        """處理 Postback 事件"""
        reply_token = event.get('replyToken', '')
        postback = event.get('postback', {})
        data = postback.get('data', '')
        
        # 解析 postback data
        params = dict(x.split('=') for x in data.split('&') if '=' in x)
        action = params.get('action', '')
        
        # 根據 action 處理
        if action == 'view_vehicle':
            vehicle_id = params.get('id', '')
            # TODO: 查詢車輛並回覆
        
        return {'type': 'postback', 'action': action, 'handled': True}
    
    def _handle_join(self, event: dict) -> dict:
        """處理加入群組事件"""
        reply_token = event.get('replyToken', '')
        
        if reply_token:
            line_service.reply_message(
                reply_token,
                '大家好！我是車行寶小幫手，有任何問題歡迎詢問 🚗'
            )
        
        return {'type': 'join', 'handled': True}
    
    def _handle_leave(self, event: dict) -> dict:
        """處理離開群組事件"""
        return {'type': 'leave', 'handled': True}
    
    def _log_follow(self, user_id: str):
        """記錄追蹤"""
        # TODO: 儲存到資料庫
        pass
    
    def _log_unfollow(self, user_id: str):
        """記錄取消追蹤"""
        # TODO: 更新資料庫
        pass


def register_routes(router):
    """註冊路由"""
    handler = LineWebhookHandler()
    router.add_route('POST', '/api/webhook/line', handler.handle_request)


# 📚 知識點
# -----------
# 1. LINE Webhook 簽名驗證：
#    - 使用 Channel Secret 做 HMAC-SHA256
#    - 簽名在 X-Line-Signature Header
#    - 驗證失敗應返回 403
#
# 2. 事件類型：
#    - message: 訊息
#    - follow: 追蹤
#    - unfollow: 取消追蹤
#    - postback: 按鈕回調
#    - join/leave: 加入/離開群組
#
# 3. 回覆訊息：
#    - 使用 replyToken（有效期 30 秒）
#    - 或使用 Push API（需用戶同意）
#
# 4. hmac.compare_digest：
#    - 常數時間比較
#    - 防止時序攻擊
