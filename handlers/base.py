"""
車行寶 CRM v5.2 - Handler 基礎工具
北斗七星文創數位 × 織明

類型提示完善版本
"""
import json
from urllib.parse import parse_qs, urlparse
from typing import Dict, List, Any, Optional, Union, TYPE_CHECKING
from http.server import BaseHTTPRequestHandler

if TYPE_CHECKING:
    from models.session import Session


class BaseHandler:
    """Handler 基礎工具類"""
    
    @staticmethod
    def send_json(handler: BaseHTTPRequestHandler, data: Dict[str, Any], status: int = 200) -> None:
        """發送 JSON 回應"""
        handler.send_response(status)
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    @staticmethod
    def send_html(handler: BaseHTTPRequestHandler, html: str, status: int = 200) -> None:
        """發送 HTML 回應"""
        handler.send_response(status)
        handler.send_header('Content-Type', 'text/html; charset=utf-8')
        handler.end_headers()
        handler.wfile.write(html.encode('utf-8'))
    
    @staticmethod
    def send_static(handler: BaseHTTPRequestHandler, content: Union[str, bytes], content_type: str) -> None:
        """發送靜態資源"""
        handler.send_response(200)
        handler.send_header('Content-Type', content_type)
        handler.send_header('Cache-Control', 'public, max-age=86400')
        handler.end_headers()
        if isinstance(content, str):
            handler.wfile.write(content.encode('utf-8'))
        else:
            handler.wfile.write(content)
    
    @staticmethod
    def get_body(handler: BaseHTTPRequestHandler) -> bytes:
        """取得請求內容"""
        content_length = int(handler.headers.get('Content-Length', 0))
        return handler.rfile.read(content_length) if content_length > 0 else b''
    
    @staticmethod
    def get_json_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
        """取得 JSON 請求內容"""
        try:
            body = BaseHandler.get_body(handler)
            return json.loads(body.decode('utf-8')) if body else {}
        except:
            return {}
    
    @staticmethod
    def get_query_params(handler: BaseHTTPRequestHandler) -> Dict[str, List[str]]:
        """取得 URL 查詢參數"""
        return parse_qs(urlparse(handler.path).query)
    
    @staticmethod
    def get_path(handler: BaseHTTPRequestHandler) -> str:
        """取得請求路徑"""
        return urlparse(handler.path).path
    
    @staticmethod
    def get_session(handler: BaseHTTPRequestHandler) -> Optional['Session']:
        """取得當前 Session"""
        from models import get_session
        
        # 從 Authorization Header 取得
        auth_header = handler.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            return get_session(token)
        
        # 從 Cookie 取得
        cookie = handler.headers.get('Cookie', '')
        for part in cookie.split(';'):
            if 'token=' in part:
                token = part.split('=')[1].strip()
                return get_session(token)
        
        return None
    
    # === 實例方法（用於子類） ===
    
    def json_response(self, data: Dict[str, Any], status: int = 200) -> Dict[str, Any]:
        """返回 JSON 格式響應數據"""
        return {'_status': status, '_data': data, **data}
    
    def success_response(self, data: Any = None, message: str = None) -> Dict[str, Any]:
        """成功響應"""
        response: Dict[str, Any] = {'success': True}
        if data is not None:
            response['data'] = data
        if message:
            response['message'] = message
        return response
    
    def error_response(self, code: int, message: str, details: Dict = None) -> Dict[str, Any]:
        """錯誤響應"""
        response: Dict[str, Any] = {
            'success': False,
            'error': message,
            'code': code
        }
        if details:
            response['details'] = details
        return response
    
    def paginated_response(
        self, 
        data: List[Any], 
        total: int, 
        page: int, 
        page_size: int
    ) -> Dict[str, Any]:
        """分頁響應"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return {
            'success': True,
            'data': data,
            'pagination': {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }
    
    def handle_request(
        self, 
        method: str, 
        path: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """處理請求（子類覆寫）"""
        return self.error_response(501, 'Not Implemented')


# 📚 知識點
# -----------
# 1. TYPE_CHECKING：僅在類型檢查時導入，避免循環導入
# 2. Union[str, bytes]：聯合類型，接受多種類型
# 3. Optional[X]：等同於 Union[X, None]
# 4. Dict[str, Any]：泛型字典類型
# 5. BaseHTTPRequestHandler：標準庫 HTTP Handler 類型
