"""
車行寶 CRM v5.2 - 監控 API Handler
北斗七星文創數位 × 織明

API 端點：
- GET /api/monitoring/dashboard - 監控儀表板
- GET /api/monitoring/health - 健康檢查
- GET /api/monitoring/metrics - 指標數據
- GET /api/monitoring/requests - 請求追蹤
"""
from typing import Dict, List, Any, Optional, Union, Callable

from handlers.base import BaseHandler
from services import monitoring_service
import config


class MonitoringHandler(BaseHandler):
    """監控 API Handler"""
    
    def handle_request(self, method: str, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """處理請求"""
        params = params or {}
        
        # GET /api/monitoring/dashboard - 儀表板
        if path == '/api/monitoring/dashboard' and method == 'GET':
            return self._dashboard()
        
        # GET /api/monitoring/health - 健康檢查
        if path == '/api/monitoring/health' and method == 'GET':
            return self._health()
        
        # GET /api/monitoring/metrics - 指標
        if path == '/api/monitoring/metrics' and method == 'GET':
            return self._metrics(params)
        
        # GET /api/monitoring/requests - 請求追蹤
        if path == '/api/monitoring/requests' and method == 'GET':
            return self._requests(params)
        
        # GET /api/monitoring/slow - 慢請求
        if path == '/api/monitoring/slow' and method == 'GET':
            return self._slow_requests(params)
        
        return self.error_response(404, 'Not Found')
    
    def _dashboard(self) -> Dict[str, Any]:
        """監控儀表板"""
        dashboard = monitoring_service.get_dashboard(config.MASTER_DB)
        return self.json_response({
            'success': True,
            'data': dashboard
        })
    
    def _health(self) -> Dict[str, Any]:
        """健康檢查"""
        health = monitoring_service.get_health_check(config.MASTER_DB)
        status_code = 200 if health['status'] == 'healthy' else 503
        return self.json_response(health, status_code)
    
    def _metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """指標數據"""
        name = params.get('name')
        limit = int(params.get('limit', 100))
        
        if name:
            data = monitoring_service.metrics.get_metrics(name, limit)
        else:
            data = monitoring_service.metrics.get_all_summaries()
        
        return self.json_response({
            'success': True,
            'data': data
        })
    
    def _requests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """請求追蹤"""
        limit = int(params.get('limit', 50))
        data = monitoring_service.tracer.get_recent(limit)
        stats = monitoring_service.tracer.get_stats()
        
        return self.json_response({
            'success': True,
            'stats': stats,
            'data': data
        })
    
    def _slow_requests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """慢請求"""
        threshold = float(params.get('threshold', 500))
        limit = int(params.get('limit', 20))
        
        data = monitoring_service.tracer.get_slow_requests(threshold, limit)
        
        return self.json_response({
            'success': True,
            'threshold_ms': threshold,
            'data': data
        })


def register_routes(router: Any) -> None:
    """註冊路由"""
    handler = MonitoringHandler()
    
    routes = [
        ('GET', '/api/monitoring/dashboard'),
        ('GET', '/api/monitoring/health'),
        ('GET', '/api/monitoring/metrics'),
        ('GET', '/api/monitoring/requests'),
        ('GET', '/api/monitoring/slow'),
    ]
    
    for method, path in routes:
        router.add_route(method, path, handler.handle_request)
