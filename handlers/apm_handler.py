"""
車行寶 CRM v5.2 - APM API Handler
北斗七星文創數位 × 織明

API 端點：
- GET /api/apm/dashboard - APM 儀表板
- GET /api/apm/traces - 追蹤列表
- GET /api/apm/traces/{trace_id} - 單一追蹤
- GET /api/apm/metrics - 指標數據
- GET /api/apm/alerts - 告警列表
- POST /api/apm/alerts/check - 檢查告警
"""
from typing import Dict, Any, Optional
from handlers.base import BaseHandler
from services import apm_service


class APMHandler(BaseHandler):
    """APM API Handler"""
    
    def handle_request(
        self, 
        method: str, 
        path: str, 
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """處理請求"""
        params = params or {}
        
        # GET /api/apm/dashboard
        if path == '/api/apm/dashboard' and method == 'GET':
            return self._dashboard()
        
        # GET /api/apm/traces
        if path == '/api/apm/traces' and method == 'GET':
            return self._traces(params)
        
        # GET /api/apm/traces/{trace_id}
        if path.startswith('/api/apm/traces/') and method == 'GET':
            trace_id = path.split('/')[-1]
            return self._trace_detail(trace_id)
        
        # GET /api/apm/metrics
        if path == '/api/apm/metrics' and method == 'GET':
            return self._metrics()
        
        # GET /api/apm/alerts
        if path == '/api/apm/alerts' and method == 'GET':
            return self._alerts(params)
        
        # POST /api/apm/alerts/check
        if path == '/api/apm/alerts/check' and method == 'POST':
            return self._check_alerts()
        
        return self.error_response(404, 'Not Found')
    
    def _dashboard(self) -> Dict[str, Any]:
        """APM 儀表板"""
        dashboard = apm_service.get_apm_dashboard()
        return self.success_response(dashboard)
    
    def _traces(self, params: Dict) -> Dict[str, Any]:
        """追蹤列表"""
        limit = int(params.get('limit', 50))
        traces = apm_service.tracer.get_traces(limit)
        return self.success_response({
            'traces': traces,
            'count': len(traces)
        })
    
    def _trace_detail(self, trace_id: str) -> Dict[str, Any]:
        """追蹤詳情"""
        spans = apm_service.tracer.get_trace(trace_id)
        if not spans:
            return self.error_response(404, 'Trace not found')
        return self.success_response({
            'trace_id': trace_id,
            'spans': spans
        })
    
    def _metrics(self) -> Dict[str, Any]:
        """指標數據"""
        metrics_data = apm_service.metrics.get_all()
        return self.success_response(metrics_data)
    
    def _alerts(self, params: Dict) -> Dict[str, Any]:
        """告警列表"""
        limit = int(params.get('limit', 50))
        alerts_list = apm_service.alerts.get_alerts(limit)
        return self.success_response({
            'alerts': alerts_list,
            'rules_count': len(apm_service.alerts._rules)
        })
    
    def _check_alerts(self) -> Dict[str, Any]:
        """檢查告警"""
        metrics_data = apm_service.metrics.get_all()
        triggered = apm_service.alerts.check(metrics_data)
        return self.success_response({
            'triggered': triggered,
            'count': len(triggered)
        })


def register_routes(router: Any) -> None:
    """註冊路由"""
    handler = APMHandler()
    
    routes = [
        ('GET', '/api/apm/dashboard'),
        ('GET', '/api/apm/traces'),
        ('GET', '/api/apm/metrics'),
        ('GET', '/api/apm/alerts'),
        ('POST', '/api/apm/alerts/check'),
    ]
    
    for method, path in routes:
        router.add_route(method, path, handler.handle_request)


# 📚 知識點
# -----------
# 1. APM Dashboard：整合追蹤、指標、告警的統一視圖
# 2. Trace Detail：查看單一請求的完整調用鏈
# 3. Metrics Endpoint：Prometheus 風格的指標導出
# 4. Alert Check：手動觸發告警檢查
