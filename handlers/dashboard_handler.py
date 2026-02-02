"""
車行寶 CRM v5.2 - 數據分析儀表板 Handler
北斗七星文創數位 × 織明

API 端點：
- GET /api/analytics/dashboard - 綜合儀表板
- GET /api/analytics/kpi - KPI 摘要
- GET /api/analytics/sales - 銷售趨勢
- GET /api/analytics/funnel - 客戶漏斗
- GET /api/analytics/inventory - 庫存分析
- GET /api/analytics/ranking - 業績排行
"""
from typing import Dict, Any, Optional
from handlers.base import BaseHandler
from services import analytics_service
import config


class DashboardHandler(BaseHandler):
    """數據分析儀表板 Handler"""
    
    def handle_request(
        self, 
        method: str, 
        path: str, 
        params: Optional[Dict] = None,
        session: Any = None
    ) -> Dict[str, Any]:
        """處理請求"""
        params = params or {}
        
        # 獲取租戶資料庫路徑
        db_path = self._get_db_path(session)
        if not db_path:
            return self.error_response(401, '請先登入')
        
        # GET /api/analytics/dashboard - 綜合儀表板
        if path == '/api/analytics/dashboard' and method == 'GET':
            return self._dashboard(db_path)
        
        # GET /api/analytics/kpi - KPI 摘要
        if path == '/api/analytics/kpi' and method == 'GET':
            return self._kpi(db_path)
        
        # GET /api/analytics/sales - 銷售趨勢
        if path == '/api/analytics/sales' and method == 'GET':
            return self._sales(db_path, params)
        
        # GET /api/analytics/funnel - 客戶漏斗
        if path == '/api/analytics/funnel' and method == 'GET':
            return self._funnel(db_path)
        
        # GET /api/analytics/inventory - 庫存分析
        if path == '/api/analytics/inventory' and method == 'GET':
            return self._inventory(db_path)
        
        # GET /api/analytics/ranking - 業績排行
        if path == '/api/analytics/ranking' and method == 'GET':
            return self._ranking(db_path, params)
        
        return self.error_response(404, 'Not Found')
    
    def _get_db_path(self, session: Any) -> Optional[str]:
        """獲取資料庫路徑"""
        if session and hasattr(session, 'tenant_id'):
            from models.database import get_tenant_db_path
            return get_tenant_db_path(session.tenant_id)
        # 開發模式使用預設路徑
        return config.MASTER_DB
    
    def _dashboard(self, db_path: str) -> Dict[str, Any]:
        """綜合儀表板"""
        try:
            data = analytics_service.get_dashboard_data(db_path)
            return self.success_response(data)
        except Exception as e:
            return self.error_response(500, f'獲取儀表板失敗: {str(e)}')
    
    def _kpi(self, db_path: str) -> Dict[str, Any]:
        """KPI 摘要"""
        try:
            data = analytics_service.get_kpi_summary(db_path)
            return self.success_response(data)
        except Exception as e:
            return self.error_response(500, f'獲取 KPI 失敗: {str(e)}')
    
    def _sales(self, db_path: str, params: Dict) -> Dict[str, Any]:
        """銷售趨勢"""
        try:
            days = int(params.get('days', 30))
            trend = analytics_service.get_sales_trend(db_path, days)
            by_brand = analytics_service.get_sales_by_brand(db_path, days)
            return self.success_response({
                'trend': trend,
                'by_brand': by_brand
            })
        except Exception as e:
            return self.error_response(500, f'獲取銷售數據失敗: {str(e)}')
    
    def _funnel(self, db_path: str) -> Dict[str, Any]:
        """客戶漏斗"""
        try:
            funnel = analytics_service.get_customer_funnel(db_path)
            sources = analytics_service.get_customer_sources(db_path)
            return self.success_response({
                'funnel': funnel,
                'sources': sources
            })
        except Exception as e:
            return self.error_response(500, f'獲取漏斗數據失敗: {str(e)}')
    
    def _inventory(self, db_path: str) -> Dict[str, Any]:
        """庫存分析"""
        try:
            stats = analytics_service.get_inventory_stats(db_path)
            turnover = analytics_service.get_inventory_turnover(db_path)
            return self.success_response({
                'stats': stats,
                'turnover': turnover
            })
        except Exception as e:
            return self.error_response(500, f'獲取庫存數據失敗: {str(e)}')
    
    def _ranking(self, db_path: str, params: Dict) -> Dict[str, Any]:
        """業績排行"""
        try:
            days = int(params.get('days', 30))
            data = analytics_service.get_performance_ranking(db_path, days)
            return self.success_response(data)
        except Exception as e:
            return self.error_response(500, f'獲取排行數據失敗: {str(e)}')


def register_routes(router: Any) -> None:
    """註冊路由"""
    handler = DashboardHandler()
    
    routes = [
        ('GET', '/api/analytics/dashboard'),
        ('GET', '/api/analytics/kpi'),
        ('GET', '/api/analytics/sales'),
        ('GET', '/api/analytics/funnel'),
        ('GET', '/api/analytics/inventory'),
        ('GET', '/api/analytics/ranking'),
    ]
    
    for method, path in routes:
        router.add_route(method, path, handler.handle_request)


# 📚 知識點
# -----------
# 1. 分析 API：提供數據視覺化所需的結構化數據
# 2. 參數驗證：將字串參數轉換為整數
# 3. 錯誤處理：捕獲異常並返回友好錯誤訊息
# 4. Session 驗證：確保用戶已登入才能存取數據
