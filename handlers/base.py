"""
車行寶 CRM v5.1 - Handler 基礎工具
北斗七星文創數位 × 織明
"""
import json
from urllib.parse import parse_qs, urlparse

class BaseHandler:
    """Handler 基礎工具類"""
    
    @staticmethod
    def send_json(handler, data, status=200):
        """發送 JSON 回應"""
        handler.send_response(status)
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.end_headers()
        handler.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    @staticmethod
    def send_html(handler, html, status=200):
        """發送 HTML 回應"""
        handler.send_response(status)
        handler.send_header('Content-Type', 'text/html; charset=utf-8')
        handler.end_headers()
        handler.wfile.write(html.encode('utf-8'))
    
    @staticmethod
    def send_static(handler, content, content_type):
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
    def get_body(handler):
        """取得請求內容"""
        content_length = int(handler.headers.get('Content-Length', 0))
        return handler.rfile.read(content_length) if content_length > 0 else b''
    
    @staticmethod
    def get_json_body(handler):
        """取得 JSON 請求內容"""
        try:
            body = BaseHandler.get_body(handler)
            return json.loads(body.decode('utf-8')) if body else {}
        except:
            return {}
    
    @staticmethod
    def get_query_params(handler):
        """取得 URL 查詢參數"""
        return parse_qs(urlparse(handler.path).query)
    
    @staticmethod
    def get_path(handler):
        """取得請求路徑"""
        return urlparse(handler.path).path
    
    @staticmethod
    def get_session(handler):
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
    
    @staticmethod
    def require_auth(handler):
        """要求認證，返回 session 或 None"""
        session = BaseHandler.get_session(handler)
        if not session:
            BaseHandler.send_json(handler, {
                'success': False, 
                'error': '請先登入'
            }, 401)
            return None
        return session
    
    @staticmethod
    def get_db_path(session):
        """從 session 取得資料庫路徑"""
        return session['data']['db_path'] if session else None
    
    @staticmethod
    def get_user_info(session):
        """從 session 取得使用者資訊"""
        if not session:
            return None, None
        return session['data']['user_id'], session['data']['user_name']


# 📚 知識點
# -----------
# 1. @staticmethod：靜態方法，不需要 self，可直接用類名呼叫
#    - 用法：BaseHandler.send_json(handler, data)
#    - 好處：不需實例化，當工具函數用
#
# 2. parse_qs：解析 URL 查詢字串
#    - "?name=john&age=30" → {'name': ['john'], 'age': ['30']}
#    - 注意：值是 list，因為同一個 key 可能有多個值
#
# 3. urlparse：拆解 URL
#    - urlparse("/api/customers?status=active")
#    - .path = "/api/customers"
#    - .query = "status=active"
