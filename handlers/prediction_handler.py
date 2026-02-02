"""
車行寶 CRM v5.2 - AI 預測 Handler
PYLIB: L4-prediction-handler
Version: v1.0.0

API 端點：
- GET /api/predict/sales - 銷售預測
- GET /api/predict/customers - 客戶成交概率
- GET /api/predict/price/{vehicle_id} - 價格建議
- GET /api/predict/demand - 需求預測
"""
from typing import Dict, Any, Optional
from handlers.base import BaseHandler
from services import prediction_service


class PredictionHandler(BaseHandler):
    """AI 預測 Handler"""
    
    def handle_request(
        self, 
        method: str, 
        path: str, 
        params: Optional[Dict] = None,
        session: Any = None
    ) -> Dict[str, Any]:
        """處理請求"""
        params = params or {}
        
        # GET /api/predict/sales - 銷售預測
        if path == '/api/predict/sales' and method == 'GET':
            return self._sales_forecast(params)
        
        # GET /api/predict/customers - 客戶成交概率
        if path == '/api/predict/customers' and method == 'GET':
            return self._customer_probability(params)
        
        # GET /api/predict/price/{id} - 價格建議
        if path.startswith('/api/predict/price/') and method == 'GET':
            vehicle_id = int(path.split('/')[-1])
            return self._price_recommendation(vehicle_id)
        
        # GET /api/predict/demand - 需求預測
        if path == '/api/predict/demand' and method == 'GET':
            return self._demand_forecast(params)
        
        return self.error_response(404, 'Not Found')
    
    def _sales_forecast(self, params: Dict) -> Dict[str, Any]:
        """銷售預測"""
        try:
            horizon = params.get('horizon', 'month')
            method = params.get('method', 'exponential')
            data = prediction_service.forecast_sales(horizon, method)
            return self.success_response(data)
        except Exception as e:
            return self.error_response(500, f'預測失敗: {str(e)}')
    
    def _customer_probability(self, params: Dict) -> Dict[str, Any]:
        """客戶成交概率"""
        try:
            customer_id = params.get('customer_id')
            if customer_id:
                customer_id = int(customer_id)
            data = prediction_service.predict_customer(customer_id)
            return self.success_response(data)
        except Exception as e:
            return self.error_response(500, f'預測失敗: {str(e)}')
    
    def _price_recommendation(self, vehicle_id: int) -> Dict[str, Any]:
        """價格建議"""
        try:
            data = prediction_service.recommend_price(vehicle_id)
            if not data:
                return self.error_response(404, '找不到車輛')
            return self.success_response(data)
        except Exception as e:
            return self.error_response(500, f'預測失敗: {str(e)}')
    
    def _demand_forecast(self, params: Dict) -> Dict[str, Any]:
        """需求預測"""
        try:
            top_n = int(params.get('top_n', 10))
            data = prediction_service.forecast_demand(top_n)
            return self.success_response(data)
        except Exception as e:
            return self.error_response(500, f'預測失敗: {str(e)}')


def register_routes(router: Any) -> None:
    """註冊路由"""
    handler = PredictionHandler()
    
    routes = [
        ('GET', '/api/predict/sales'),
        ('GET', '/api/predict/customers'),
        ('GET', '/api/predict/price/<int:vehicle_id>'),
        ('GET', '/api/predict/demand'),
    ]
    
    for method, path in routes:
        router.add_route(method, path, handler.handle_request)
