"""
車行寶 CRM v5.1 - AI 與報表 API Handler
北斗七星文創數位 × 織明

API 端點：
- /api/ai/intent/{customer_id} - 客戶意向分析
- /api/ai/scripts/{vehicle_id} - 銷售話術
- /api/ai/recommend/{customer_id} - 車輛推薦
- /api/ai/alerts - 庫存預警
- /api/ai/predict - 業績預測
- /api/reports/daily - 日報
- /api/reports/weekly - 週報
- /api/reports/monthly - 月報
- /api/reports/leaderboard - 排行榜
- /api/reports/export - Excel 匯出
"""
import json
from datetime import datetime
from urllib.parse import parse_qs
from handlers.base import BaseHandler
from services import ai_service, report_service
import config


class AIReportHandler(BaseHandler):
    """AI 與報表 API Handler"""
    
    def handle_request(self, method: str, path: str, params: dict = None):
        """處理請求"""
        params = params or {}
        
        # AI 端點
        if path.startswith('/api/ai/'):
            return self._handle_ai(method, path, params)
        
        # 報表端點
        if path.startswith('/api/reports/'):
            return self._handle_reports(method, path, params)
        
        return self.error_response(404, 'Not Found')
    
    # ============================================================
    # AI API
    # ============================================================
    
    def _handle_ai(self, method: str, path: str, params: dict):
        """處理 AI API"""
        db_path = self.get_tenant_db()
        
        # /api/ai/intent/{customer_id}
        if '/intent/' in path:
            customer_id = self._extract_id(path, 'intent')
            if not customer_id:
                return self.error_response(400, '缺少客戶 ID')
            result = ai_service.analyze_customer_intent(db_path, customer_id)
            return self.json_response(result)
        
        # /api/ai/intent-batch
        if path == '/api/ai/intent-batch':
            limit = int(params.get('limit', 50))
            result = ai_service.batch_analyze_intent(db_path, limit)
            return self.json_response({'success': True, 'data': result})
        
        # /api/ai/scripts/{vehicle_id}
        if '/scripts/' in path:
            vehicle_id = self._extract_id(path, 'scripts')
            if not vehicle_id:
                return self.error_response(400, '缺少車輛 ID')
            customer_id = params.get('customer_id')
            result = ai_service.get_sales_scripts(db_path, vehicle_id, customer_id)
            return self.json_response(result)
        
        # /api/ai/recommend/{customer_id}
        if '/recommend/' in path:
            customer_id = self._extract_id(path, 'recommend')
            if not customer_id:
                return self.error_response(400, '缺少客戶 ID')
            limit = int(params.get('limit', 5))
            result = ai_service.recommend_vehicles(db_path, customer_id, limit)
            return self.json_response(result)
        
        # /api/ai/alerts
        if path == '/api/ai/alerts':
            result = ai_service.analyze_inventory_alerts(db_path)
            return self.json_response(result)
        
        # /api/ai/predict
        if path == '/api/ai/predict':
            result = ai_service.predict_monthly_sales(db_path)
            return self.json_response(result)
        
        return self.error_response(404, 'AI API Not Found')
    
    # ============================================================
    # 報表 API
    # ============================================================
    
    def _handle_reports(self, method: str, path: str, params: dict):
        """處理報表 API"""
        db_path = self.get_tenant_db()
        
        # /api/reports/daily
        if path == '/api/reports/daily':
            date = params.get('date')
            result = report_service.generate_daily_report(db_path, date)
            return self.json_response(result)
        
        # /api/reports/weekly
        if path == '/api/reports/weekly':
            end_date = params.get('end_date')
            result = report_service.generate_weekly_report(db_path, end_date)
            return self.json_response(result)
        
        # /api/reports/monthly
        if path == '/api/reports/monthly':
            year_month = params.get('month')
            result = report_service.generate_monthly_report(db_path, year_month)
            return self.json_response(result)
        
        # /api/reports/leaderboard
        if path == '/api/reports/leaderboard':
            period = params.get('period', 'month')
            limit = int(params.get('limit', 10))
            result = report_service.get_leaderboard(db_path, period, limit)
            return self.json_response(result)
        
        # /api/reports/export
        if path == '/api/reports/export':
            report_type = params.get('type', 'daily')
            
            if report_type == 'daily':
                report = report_service.generate_daily_report(db_path, params.get('date'))
            elif report_type == 'weekly':
                report = report_service.generate_weekly_report(db_path, params.get('end_date'))
            elif report_type == 'monthly':
                report = report_service.generate_monthly_report(db_path, params.get('month'))
            else:
                return self.error_response(400, '無效的報表類型')
            
            try:
                excel_data = report_service.export_report_to_excel(report)
                return self.file_response(
                    excel_data,
                    f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            except ImportError as e:
                return self.error_response(500, str(e))
        
        # /api/reports/export-deals
        if path == '/api/reports/export-deals':
            start_date = params.get('start_date')
            end_date = params.get('end_date')
            
            if not start_date or not end_date:
                return self.error_response(400, '需要 start_date 和 end_date')
            
            try:
                excel_data = report_service.export_deals_to_excel(db_path, start_date, end_date)
                return self.file_response(
                    excel_data,
                    f"deals_{start_date}_{end_date}.xlsx",
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            except ImportError as e:
                return self.error_response(500, str(e))
        
        return self.error_response(404, 'Report API Not Found')
    
    # ============================================================
    # 輔助方法
    # ============================================================
    
    def _extract_id(self, path: str, segment: str) -> int:
        """從路徑提取 ID"""
        try:
            parts = path.split('/')
            idx = parts.index(segment)
            return int(parts[idx + 1])
        except (ValueError, IndexError):
            return None
    
    def get_tenant_db(self) -> str:
        """取得租戶資料庫路徑"""
        # 簡化版：直接返回主資料庫
        # 實際應根據請求的租戶 ID 返回對應資料庫
        return config.MASTER_DB
    
    def file_response(self, data: bytes, filename: str, content_type: str):
        """返回檔案下載"""
        return {
            'status': 200,
            'headers': {
                'Content-Type': content_type,
                'Content-Disposition': f'attachment; filename="{filename}"'
            },
            'body': data
        }


# 路由註冊
def register_routes(router):
    """註冊 AI 和報表路由"""
    handler = AIReportHandler()
    
    # AI 路由
    router.add_route('GET', '/api/ai/intent/{id}', handler.handle_request)
    router.add_route('GET', '/api/ai/intent-batch', handler.handle_request)
    router.add_route('GET', '/api/ai/scripts/{id}', handler.handle_request)
    router.add_route('GET', '/api/ai/recommend/{id}', handler.handle_request)
    router.add_route('GET', '/api/ai/alerts', handler.handle_request)
    router.add_route('GET', '/api/ai/predict', handler.handle_request)
    
    # 報表路由
    router.add_route('GET', '/api/reports/daily', handler.handle_request)
    router.add_route('GET', '/api/reports/weekly', handler.handle_request)
    router.add_route('GET', '/api/reports/monthly', handler.handle_request)
    router.add_route('GET', '/api/reports/leaderboard', handler.handle_request)
    router.add_route('GET', '/api/reports/export', handler.handle_request)
    router.add_route('GET', '/api/reports/export-deals', handler.handle_request)


# 📚 知識點
# -----------
# 1. RESTful API 設計：
#    - GET /api/ai/intent/{id}：查詢單一資源
#    - GET /api/reports/daily?date=xxx：查詢參數
#
# 2. 路由參數提取：
#    - path.split('/') 分割路徑
#    - 找到關鍵字位置後取下一個元素
#
# 3. 檔案下載回應：
#    - Content-Type: application/vnd...spreadsheet
#    - Content-Disposition: attachment
#    - 直接返回 bytes
#
# 4. 錯誤處理：
#    - ImportError：套件未安裝
#    - 參數驗證：必填欄位檢查
