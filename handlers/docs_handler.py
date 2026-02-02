"""
車行寶 CRM v5.2 - API 文檔 Handler
北斗七星文創數位 × 織明

API 端點：
- GET /api/docs - Swagger UI
- GET /api/docs/redoc - ReDoc UI
- GET /api/docs/openapi.yaml - OpenAPI 規範
- GET /api/docs/openapi.json - OpenAPI JSON
"""
import os
import json
from typing import Dict, Any, Optional
from handlers.base import BaseHandler


class DocsHandler(BaseHandler):
    """API 文檔 Handler"""
    
    def __init__(self) -> None:
        self.openapi_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'docs', 
            'openapi.yaml'
        )
    
    def handle_request(
        self, 
        method: str, 
        path: str, 
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """處理請求"""
        
        # GET /api/docs - Swagger UI
        if path == '/api/docs' and method == 'GET':
            return self._swagger_ui()
        
        # GET /api/docs/redoc - ReDoc UI
        if path == '/api/docs/redoc' and method == 'GET':
            return self._redoc_ui()
        
        # GET /api/docs/openapi.yaml - YAML 規範
        if path == '/api/docs/openapi.yaml' and method == 'GET':
            return self._openapi_yaml()
        
        # GET /api/docs/openapi.json - JSON 規範
        if path == '/api/docs/openapi.json' and method == 'GET':
            return self._openapi_json()
        
        return self.error_response(404, 'Not Found')
    
    def _swagger_ui(self) -> Dict[str, Any]:
        """返回 Swagger UI"""
        from templates.swagger import get_swagger_html
        return {
            '_html': get_swagger_html(),
            '_content_type': 'text/html'
        }
    
    def _redoc_ui(self) -> Dict[str, Any]:
        """返回 ReDoc UI"""
        from templates.swagger import get_redoc_html
        return {
            '_html': get_redoc_html(),
            '_content_type': 'text/html'
        }
    
    def _openapi_yaml(self) -> Dict[str, Any]:
        """返回 OpenAPI YAML"""
        try:
            with open(self.openapi_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                '_raw': content,
                '_content_type': 'application/x-yaml'
            }
        except FileNotFoundError:
            return self.error_response(404, 'OpenAPI spec not found')
    
    def _openapi_json(self) -> Dict[str, Any]:
        """返回 OpenAPI JSON"""
        try:
            import yaml
            with open(self.openapi_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)
            return {
                '_raw': json.dumps(spec, ensure_ascii=False, indent=2),
                '_content_type': 'application/json'
            }
        except ImportError:
            # 沒有 PyYAML，返回簡化版
            return self._generate_basic_spec()
        except FileNotFoundError:
            return self.error_response(404, 'OpenAPI spec not found')
    
    def _generate_basic_spec(self) -> Dict[str, Any]:
        """生成基本 API 規範"""
        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "車行寶 CRM API",
                "version": "5.2.0",
                "description": "中古車行客戶關係管理系統"
            },
            "servers": [{"url": "/"}],
            "paths": {
                "/api/auth/login": {
                    "post": {"summary": "用戶登入", "tags": ["auth"]}
                },
                "/api/customers": {
                    "get": {"summary": "客戶列表", "tags": ["customers"]},
                    "post": {"summary": "創建客戶", "tags": ["customers"]}
                },
                "/api/vehicles": {
                    "get": {"summary": "車輛列表", "tags": ["vehicles"]},
                    "post": {"summary": "創建車輛", "tags": ["vehicles"]}
                },
                "/api/deals": {
                    "get": {"summary": "交易列表", "tags": ["deals"]},
                    "post": {"summary": "創建交易", "tags": ["deals"]}
                },
                "/api/system/health": {
                    "get": {"summary": "健康檢查", "tags": ["system"]}
                }
            }
        }
        return {
            '_raw': json.dumps(spec, ensure_ascii=False, indent=2),
            '_content_type': 'application/json'
        }


def register_routes(router: Any) -> None:
    """註冊路由"""
    handler = DocsHandler()
    
    routes = [
        ('GET', '/api/docs'),
        ('GET', '/api/docs/redoc'),
        ('GET', '/api/docs/openapi.yaml'),
        ('GET', '/api/docs/openapi.json'),
    ]
    
    for method, path in routes:
        router.add_route(method, path, handler.handle_request)


# 📚 知識點
# -----------
# 1. Swagger UI：互動式 API 文檔工具
# 2. ReDoc：另一種 API 文檔渲染方案
# 3. OpenAPI 3.0：REST API 標準規範
# 4. CDN 載入：使用 CDN 加速前端資源
# 5. Try It Out：Swagger 提供的 API 測試功能
