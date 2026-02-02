"""
車行寶 CRM v5.2 - Push API Handler
北斗七星文創數位 × 織明

API 端點：
- GET  /api/push/vapid-key - 取得 VAPID 公鑰
- POST /api/push/subscribe - 訂閱推播
- POST /api/push/unsubscribe - 取消訂閱
- POST /api/push/send - 發送推播（管理員）
- POST /api/push/broadcast - 廣播推播（管理員）
"""
from typing import Dict, List, Any, Optional, Union, Callable

from handlers.base import BaseHandler
from services import push_service
import config


class PushHandler(BaseHandler):
    """Push API Handler"""
    
    def handle_request(self, method: str, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """處理請求"""
        params = params or {}
        
        # GET /api/push/vapid-key - 取得公鑰
        if path == '/api/push/vapid-key' and method == 'GET':
            return self._get_vapid_key()
        
        # POST /api/push/subscribe - 訂閱
        if path == '/api/push/subscribe' and method == 'POST':
            return self._subscribe(params)
        
        # POST /api/push/unsubscribe - 取消訂閱
        if path == '/api/push/unsubscribe' and method == 'POST':
            return self._unsubscribe(params)
        
        # POST /api/push/send - 發送給指定用戶
        if path == '/api/push/send' and method == 'POST':
            return self._send(params)
        
        # POST /api/push/broadcast - 廣播
        if path == '/api/push/broadcast' and method == 'POST':
            return self._broadcast(params)
        
        # GET /api/push/stats - 統計
        if path == '/api/push/stats' and method == 'GET':
            return self._stats()
        
        return self.error_response(404, 'Not Found')
    
    def _get_vapid_key(self) -> Dict[str, Any]:
        """取得 VAPID 公鑰"""
        result = push_service.get_vapid_public_key()
        return self.json_response(result)
    
    def _subscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """訂閱推播"""
        subscription = params.get('subscription', {})
        user_id = params.get('user_id')
        tenant_id = params.get('tenant_id')
        
        if not subscription.get('endpoint'):
            return self.error_response(400, '缺少訂閱資訊')
        
        result = push_service.subscribe(
            config.MASTER_DB,
            subscription,
            user_id,
            tenant_id
        )
        return self.json_response(result)
    
    def _unsubscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """取消訂閱"""
        endpoint = params.get('endpoint', '')
        
        if not endpoint:
            return self.error_response(400, '缺少 endpoint')
        
        result = push_service.unsubscribe(config.MASTER_DB, endpoint)
        return self.json_response(result)
    
    def _send(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """發送推播"""
        user_id = params.get('user_id')
        title = params.get('title', '車行寶通知')
        body = params.get('body', '')
        url = params.get('url')
        
        if not user_id:
            return self.error_response(400, '缺少 user_id')
        if not body:
            return self.error_response(400, '缺少訊息內容')
        
        result = push_service.send_push(
            config.MASTER_DB,
            user_id,
            title,
            body,
            url
        )
        return self.json_response(result)
    
    def _broadcast(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """廣播推播"""
        title = params.get('title', '車行寶公告')
        body = params.get('body', '')
        tenant_id = params.get('tenant_id')
        url = params.get('url')
        
        if not body:
            return self.error_response(400, '缺少訊息內容')
        
        result = push_service.broadcast_push(
            config.MASTER_DB,
            title,
            body,
            tenant_id,
            url
        )
        return self.json_response(result)
    
    def _stats(self) -> Dict[str, Any]:
        """訂閱統計"""
        manager = push_service.SubscriptionManager(config.MASTER_DB)
        count = manager.count()
        
        return self.json_response({
            'success': True,
            'subscriptions': count
        })


def register_routes(router: Any) -> None:
    """註冊路由"""
    handler = PushHandler()
    
    routes = [
        ('GET', '/api/push/vapid-key'),
        ('POST', '/api/push/subscribe'),
        ('POST', '/api/push/unsubscribe'),
        ('POST', '/api/push/send'),
        ('POST', '/api/push/broadcast'),
        ('GET', '/api/push/stats'),
    ]
    
    for method, path in routes:
        router.add_route(method, path, handler.handle_request)
