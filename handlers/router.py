"""
車行寶 CRM v5.1 - 路由核心（重構版）
北斗七星文創數位 × 織明

職責：僅負責路由分發，具體邏輯委託給各 handler
"""
from typing import Dict, List, Any, Optional, Union, Callable

import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import config

# 匯入處理器
from .base import BaseHandler
from . import auth_handler
from . import customer_handler
from . import vehicle_handler
from . import deal_handler
from . import report_handler
from . import webhook_handler
from . import upload_handler
from . import batch_handler


class Router(BaseHTTPRequestHandler):
    """主路由處理器"""
    
    def log_message(self, format, *args):
        """控制日誌輸出"""
        if config.DEBUG:
            print(f"[{self.log_date_time_string()}] {args[0]}")
    
    def do_OPTIONS(self):
        """處理 CORS 預檢"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """處理 GET 請求"""
        path = urlparse(self.path).path
        
        # 靜態資源
        if path.startswith('/static/'):
            return self._serve_static(path)
        
        # 上傳的圖片
        if path.startswith('/uploads/'):
            return self._serve_uploads(path)
        
        # 頁面路由
        page_routes = {
            '/': self._page_landing,
            '/app': self._page_app,
            '/privacy': self._page_privacy,
            '/terms': self._page_terms,
            '/line/bind': self._page_line_bind,
        }
        
        if path in page_routes:
            return page_routes[path]()
        
        # API 路由
        if path.startswith('/api/'):
            return self._route_api_get(path)
        
        # 404
        BaseHandler.send_html(self, '<h1>404 Not Found</h1>', 404)
    
    def do_POST(self):
        """處理 POST 請求"""
        path = urlparse(self.path).path
        
        # 認證相關（不需登入）
        auth_routes = {
            '/api/login': auth_handler.handle_login,
            '/api/register': auth_handler.handle_register,
            '/api/logout': auth_handler.handle_logout,
        }
        
        if path in auth_routes:
            return auth_routes[path](self)
        
        # Webhook（不需登入）
        if path == '/line/webhook':
            return self._handle_line_webhook()
        
        if path == '/ecpay/notify':
            return self._handle_ecpay_notify()
        
        # API 路由（需登入）
        if path.startswith('/api/'):
            return self._route_api_post(path)
        
        BaseHandler.send_json(self, {'error': 'Not Found'}, 404)
    
    # ===== 頁面渲染 =====
    
    def _page_landing(self):
        from templates import landing
        BaseHandler.send_html(self, landing.render())
    
    def _page_app(self):
        from templates import app
        BaseHandler.send_html(self, app.render())
    
    def _page_privacy(self):
        from templates import privacy
        BaseHandler.send_html(self, privacy.render())
    
    def _page_terms(self):
        from templates import terms
        BaseHandler.send_html(self, terms.render())
    
    def _page_line_bind(self):
        query = parse_qs(urlparse(self.path).query)
        tenant = query.get('tenant', [''])[0]
        token = query.get('token', [''])[0]
        from templates import line_bind
        BaseHandler.send_html(self, line_bind.render(tenant, token))
    
    # ===== 靜態資源 =====
    
    def _serve_static(self, path):
        """提供靜態資源"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        file_path = os.path.join(base_dir, path[1:])  # 去掉開頭的 /
        
        if not os.path.exists(file_path):
            return BaseHandler.send_html(self, 'Not Found', 404)
        
        # MIME 類型對照
        mime_types = {
            '.css': 'text/css; charset=utf-8',
            '.js': 'application/javascript; charset=utf-8',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
        }
        
        ext = os.path.splitext(file_path)[1].lower()
        content_type = mime_types.get(ext, 'application/octet-stream')
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        BaseHandler.send_static(self, content, content_type)
    
    def _serve_uploads(self, path):
        """提供上傳的檔案"""
        # /uploads/{tenant}/{category}/{year}/{month}/{filename}
        # 映射到 data/uploads/...
        relative_path = path[9:]  # 去掉 /uploads/
        file_path = os.path.join(config.DATA_DIR, 'uploads', relative_path)
        
        # 安全檢查：防止路徑穿越
        real_path = os.path.realpath(file_path)
        uploads_dir = os.path.realpath(os.path.join(config.DATA_DIR, 'uploads'))
        if not real_path.startswith(uploads_dir):
            return BaseHandler.send_html(self, 'Forbidden', 403)
        
        if not os.path.exists(file_path):
            return BaseHandler.send_html(self, 'Not Found', 404)
        
        # MIME 類型
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        
        ext = os.path.splitext(file_path)[1].lower()
        content_type = mime_types.get(ext, 'application/octet-stream')
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # 設定快取（圖片可快取較長時間）
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(content))
        self.send_header('Cache-Control', 'public, max-age=86400')  # 1天
        self.end_headers()
        self.wfile.write(content)
    
    # ===== API 路由分發 =====
    
    def _route_api_get(self, path):
        """分發 GET API"""
        # 健康檢查（不需登入）
        if path == '/api/health':
            from services.monitor_service import get_health, get_status
            health = get_health()
            status = get_status()
            return BaseHandler.send_json(self, {
                'status': 'ok' if health['healthy'] else 'degraded',
                'version': config.VERSION,
                'app': config.APP_NAME,
                'checks': health['checks'],
                'env': status['app']['env']
            })
        
        # 效能指標（不需登入，但生產環境應限制）
        if path == '/api/metrics':
            from services.monitor_service import get_metrics
            return BaseHandler.send_json(self, get_metrics())
        
        # 需要登入的 API
        session = BaseHandler.require_auth(self)
        if not session:
            return
        
        # 取得常用參數
        db_path = session['data']['db_path']
        user_id = session['data']['user_id']
        user_name = session['data']['user_name']
        query = BaseHandler.get_query_params(self)
        
        # 路由對照表
        routes = {
            '/api/me': lambda: auth_handler.handle_me(self),
            '/api/stats': lambda: report_handler.get_stats(self, session),
            '/api/customers': lambda: customer_handler.get_customers(self, session),
            '/api/vehicles': lambda: vehicle_handler.get_vehicles(self, db_path, query),
            '/api/deals': lambda: deal_handler.get_deals(self, db_path, query),
            '/api/followups': lambda: deal_handler.get_followups(self, db_path, query),
            '/api/logs': lambda: report_handler.get_activity_logs(self, session),
            '/api/reports/sales': lambda: report_handler.get_sales_report(self, session),
            '/api/reports/inventory': lambda: report_handler.get_inventory_report(self, session),
            '/api/reports/customers': lambda: report_handler.get_customer_report(self, session),
            # 圖表數據 API
            '/api/charts/dashboard': lambda: self._get_dashboard_charts(db_path),
            '/api/charts/sales': lambda: self._get_sales_chart(db_path, query),
            '/api/charts/inventory': lambda: self._get_inventory_chart(db_path),
            '/api/charts/customers': lambda: self._get_customer_chart(db_path),
            # 提醒 API
            '/api/reminders': lambda: self._get_reminders(db_path),
        }
        
        if path in routes:
            return routes[path]()
        
        # 動態路由：/api/customers/{id}
        if path.startswith('/api/customers/') and path.count('/') == 3:
            customer_id = path.split('/')[3]
            if customer_id.isdigit():
                return customer_handler.get_customer(self, session, int(customer_id))
        
        # 動態路由：/api/vehicles/{id}
        if path.startswith('/api/vehicles/') and path.count('/') == 3:
            vehicle_id = path.split('/')[3]
            if vehicle_id.isdigit():
                return vehicle_handler.get_vehicle_by_id(self, db_path, int(vehicle_id))
        
        # 車輛圖片列表：/api/vehicles/{id}/images
        if path.startswith('/api/vehicles/') and path.endswith('/images'):
            parts = path.split('/')
            if len(parts) == 5 and parts[3].isdigit():
                return upload_handler.get_vehicle_images(self, session, int(parts[3]))
        
        BaseHandler.send_json(self, {'error': 'API Not Found'}, 404)
    
    def _route_api_post(self, path):
        """分發 POST API"""
        session = BaseHandler.require_auth(self)
        if not session:
            return
        
        # 取得常用參數
        db_path = session['data']['db_path']
        user_id = session['data']['user_id']
        user_name = session['data']['user_name']
        data = BaseHandler.get_json_body(self) or {}
        
        # 路由對照表
        routes = {
            '/api/customers': lambda: customer_handler.create_customer(self, session),
            '/api/vehicles': lambda: vehicle_handler.create_vehicle(self, db_path, data, user_id, user_name),
            '/api/deals': lambda: deal_handler.create_deal(self, db_path, data, user_id, user_name),
            '/api/followups': lambda: deal_handler.create_followup(self, db_path, data, user_id, user_name),
            '/api/upload': lambda: upload_handler.handle_upload(self, session),
            # 批量操作
            '/api/batch/customers/delete': lambda: batch_handler.batch_delete_customers(self, session),
            '/api/batch/customers/level': lambda: batch_handler.batch_update_customer_level(self, session),
            '/api/batch/vehicles/delete': lambda: batch_handler.batch_delete_vehicles(self, session),
            '/api/batch/vehicles/status': lambda: batch_handler.batch_update_vehicle_status(self, session),
            '/api/batch/vehicles/price': lambda: batch_handler.batch_update_vehicle_price(self, session),
            '/api/batch/followups': lambda: batch_handler.batch_create_followups(self, session),
        }
        
        if path in routes:
            return routes[path]()
        
        # 車輛圖片上傳：/api/vehicles/{id}/images
        if path.startswith('/api/vehicles/') and path.endswith('/images'):
            parts = path.split('/')
            if len(parts) == 5 and parts[3].isdigit():
                return upload_handler.handle_vehicle_image_upload(self, session, int(parts[3]))
        
        # 動態路由：/api/customers/{id}/update
        if '/update' in path:
            parts = path.split('/')
            if len(parts) >= 5 and parts[2] == 'customers':
                return customer_handler.update_customer(self, session, int(parts[3]))
            if len(parts) >= 5 and parts[2] == 'vehicles':
                return vehicle_handler.update_vehicle(self, db_path, int(parts[3]), data, user_id, user_name)
            if len(parts) >= 5 and parts[2] == 'deals':
                return deal_handler.update_deal(self, db_path, int(parts[3]), data, user_id, user_name)
        
        # 動態路由：/api/customers/{id}/delete
        if '/delete' in path:
            parts = path.split('/')
            if len(parts) >= 5 and parts[2] == 'customers':
                return customer_handler.delete_customer(self, session, int(parts[3]))
            if len(parts) >= 5 and parts[2] == 'vehicles':
                return vehicle_handler.delete_vehicle(self, db_path, int(parts[3]), user_id, user_name)
            if len(parts) >= 5 and parts[2] == 'deals':
                return deal_handler.cancel_deal(self, db_path, int(parts[3]), user_id, user_name)
        
        BaseHandler.send_json(self, {'error': 'API Not Found'}, 404)
    
    # ===== 圖表數據處理 =====
    
    def _get_dashboard_charts(self, db_path):
        """取得儀表板圖表數據"""
        from services.chart_service import get_dashboard_data
        data = get_dashboard_data(db_path)
        BaseHandler.send_json(self, {'success': True, 'charts': data})
    
    def _get_sales_chart(self, db_path, query):
        """取得銷售圖表"""
        from services.chart_service import get_sales_trend, get_monthly_comparison
        days = int(query.get('days', [30])[0])
        data = {
            'trend': get_sales_trend(db_path, days),
            'monthly': get_monthly_comparison(db_path, 6)
        }
        BaseHandler.send_json(self, {'success': True, 'charts': data})
    
    def _get_inventory_chart(self, db_path):
        """取得庫存圖表"""
        from services.chart_service import (
            get_inventory_by_brand, get_inventory_by_status, get_inventory_age
        )
        data = {
            'by_brand': get_inventory_by_brand(db_path),
            'by_status': get_inventory_by_status(db_path),
            'by_age': get_inventory_age(db_path)
        }
        BaseHandler.send_json(self, {'success': True, 'charts': data})
    
    def _get_customer_chart(self, db_path):
        """取得客戶圖表"""
        from services.chart_service import (
            get_customer_by_source, get_customer_by_level, get_customer_growth
        )
        data = {
            'by_source': get_customer_by_source(db_path),
            'by_level': get_customer_by_level(db_path),
            'growth': get_customer_growth(db_path, 6)
        }
        BaseHandler.send_json(self, {'success': True, 'charts': data})
    
    def _get_reminders(self, db_path):
        """取得待處理提醒"""
        from services.reminder_service import get_pending_reminders
        data = get_pending_reminders(db_path)
        BaseHandler.send_json(self, {'success': True, 'reminders': data})
    
    # ===== Webhook 處理 =====
    
    def _handle_line_webhook(self):
        """處理 LINE Webhook"""
        body = BaseHandler.get_body(self)
        signature = self.headers.get('X-Line-Signature', '')
        webhook_handler.handle_line(self, body, signature)
    
    def _handle_ecpay_notify(self):
        """處理 ECPay 回調"""
        from services import ecpay_service
        body = BaseHandler.get_body(self).decode('utf-8')
        params = dict(parse_qs(body, keep_blank_values=True))
        params = {k: v[0] for k, v in params.items()}
        
        result = ecpay_service.process_notify(params)
        
        self.send_response(200 if result['success'] else 400)
        self.end_headers()
        self.wfile.write(b'1|OK' if result['success'] else b'0|Error')


# 📚 知識點
# -----------
# 1. 路由分發模式：
#    - Router 只負責「分發」，不處理業務邏輯
#    - 具體邏輯委託給各 handler 模組
#    - 符合單一職責原則（SRP）
#
# 2. lambda 延遲執行：
#    - routes = {'/api/x': lambda: handler(self)}
#    - lambda 讓函數在被呼叫時才執行
#    - 避免在建立字典時就執行所有函數
#
# 3. 動態路由解析：
#    - path.split('/') 拆解路徑
#    - /api/customers/123 → ['', 'api', 'customers', '123']
#    - 取 parts[3] 就是 ID
#
# 4. MIME 類型：
#    - 告訴瀏覽器如何處理回應內容
#    - text/css：CSS 樣式
#    - application/javascript：JS 腳本
#    - image/png：PNG 圖片


# 文檔路由
def _register_docs_routes(router):
    """註冊文檔路由"""
    from handlers.docs_handler import DocsHandler
    handler = DocsHandler()
    router.add_route('GET', '/api/docs', handler.handle_request)
    router.add_route('GET', '/api/docs/redoc', handler.handle_request)
    router.add_route('GET', '/api/docs/openapi.yaml', handler.handle_request)
    router.add_route('GET', '/api/docs/openapi.json', handler.handle_request)
