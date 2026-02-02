"""
車行寶 CRM v5.1 - AI Handler
北斗七星文創數位 × 織明

XTF任務鏈：D
"""
from typing import Dict, List, Any, Optional, Union, Callable

from handlers.base import BaseHandler
from services import deepseek_service
from services import ai_service
import config


class DeepAIHandler(BaseHandler):
    """DeepSeek AI API Handler"""
    
    def handle_request(self, method: str, path: str, params: dict = None):
        """處理請求"""
        params = params or {}
        
        # /api/ai/deep/price - 智能車價分析
        if path == '/api/ai/deep/price':
            return self._analyze_price(params)
        
        # /api/ai/deep/customer - 客戶深度分析
        if path == '/api/ai/deep/customer':
            return self._analyze_customer(params)
        
        # /api/ai/deep/script - 話術生成
        if path == '/api/ai/deep/script':
            return self._generate_script(params)
        
        # /api/ai/deep/market - 市場趨勢
        if path == '/api/ai/deep/market':
            return self._market_trend(params)
        
        # /api/ai/deep/ask - 快速問答
        if path == '/api/ai/deep/ask':
            return self._quick_ask(params)
        
        # /api/ai/deep/status - API 狀態
        if path == '/api/ai/deep/status':
            return self._check_status()
        
        return self.error_response(404, 'Not Found')
    
    def _analyze_price(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """智能車價分析"""
        vehicle = {
            'brand': params.get('brand', ''),
            'model': params.get('model', ''),
            'year': params.get('year', ''),
            'mileage': params.get('mileage', 0),
            'color': params.get('color', ''),
            'features': params.get('features', ''),
            'condition_note': params.get('condition', '')
        }
        
        result = deepseek_service.analyze_vehicle_price(vehicle)
        return self.json_response(result)
    
    def _analyze_customer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """客戶深度分析"""
        customer = {
            'name': params.get('name', ''),
            'level': params.get('level', 'normal'),
            'source': params.get('source', ''),
            'created_at': params.get('created_at', ''),
            'note': params.get('note', '')
        }
        
        # 互動記錄（簡化）
        interactions = params.get('interactions', [])
        
        result = deepseek_service.analyze_customer_deep(customer, interactions)
        return self.json_response(result)
    
    def _generate_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """話術生成"""
        vehicle = {
            'brand': params.get('brand', ''),
            'model': params.get('model', ''),
            'year': params.get('year', ''),
            'mileage': params.get('mileage', 0),
            'asking_price': params.get('price', 0)
        }
        
        scenario = params.get('scenario', 'general')
        
        result = deepseek_service.generate_sales_script(vehicle, scenario=scenario)
        return self.json_response(result)
    
    def _market_trend(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """市場趨勢"""
        brand = params.get('brand')
        segment = params.get('segment')
        
        result = deepseek_service.predict_market_trend(brand, segment)
        return self.json_response(result)
    
    def _quick_ask(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """快速問答"""
        question = params.get('question', params.get('q', ''))
        context = params.get('context', '')
        
        if not question:
            return self.error_response(400, '請提供問題')
        
        result = deepseek_service.quick_ask(question, context)
        return self.json_response(result)
    
    def _check_status(self) -> Dict[str, Any]:
        """API 狀態"""
        result = deepseek_service.check_api_status()
        return self.json_response(result)


def register_routes(router):
    """註冊路由"""
    handler = DeepAIHandler()
    
    routes = [
        ('POST', '/api/ai/deep/price'),
        ('POST', '/api/ai/deep/customer'),
        ('POST', '/api/ai/deep/script'),
        ('GET', '/api/ai/deep/market'),
        ('POST', '/api/ai/deep/ask'),
        ('GET', '/api/ai/deep/status'),
    ]
    
    for method, path in routes:
        router.add_route(method, path, handler.handle_request)
