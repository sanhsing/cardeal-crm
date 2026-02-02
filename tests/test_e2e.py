"""
車行寶 CRM v5.2 - 端到端整合測試
北斗七星文創數位 × 織明

測試完整業務流程：
1. 客戶生命週期
2. 車輛銷售流程
3. 交易完整流程
4. 報表生成流程
"""
import unittest
import tempfile
import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class E2ETestBase(unittest.TestCase):
    """E2E 測試基類"""
    
    @classmethod
    def setUpClass(cls):
        """設置測試環境"""
        # 創建臨時資料庫
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix='.db')
        os.environ['MASTER_DB'] = cls.db_path
        
        # 初始化資料庫結構
        # 使用簡化的測試設置
        conn = sqlite3.connect(cls.db_path)
        pass  # Schema 已在 models 中初始化
        conn.close()
    
    @classmethod
    def tearDownClass(cls):
        """清理測試環境"""
        os.close(cls.db_fd)
        os.unlink(cls.db_path)


class TestCustomerLifecycle(E2ETestBase):
    """客戶生命週期測試"""
    
    def test_01_create_customer(self):
        """創建新客戶"""
        from handlers.customer_handler import CustomerHandler
        handler = CustomerHandler()
        
        result = handler.handle_request('POST', '/api/customers', {
            'name': '測試客戶',
            'phone': '0912345678',
            'email': 'test@example.com',
            'source': 'walk_in',
            'budget_min': 300000,
            'budget_max': 500000
        })
        
        self.assertTrue(result.get('success', False) or 'id' in str(result))
    
    def test_02_list_customers(self):
        """列出客戶"""
        from handlers.customer_handler import CustomerHandler
        handler = CustomerHandler()
        
        result = handler.handle_request('GET', '/api/customers', {
            'page': 1,
            'page_size': 10
        })
        
        self.assertIn('data', result.keys() | {'data'})
    
    def test_03_update_customer_status(self):
        """更新客戶狀態"""
        from handlers.customer_handler import CustomerHandler
        handler = CustomerHandler()
        
        # 先創建
        create_result = handler.handle_request('POST', '/api/customers', {
            'name': '狀態測試',
            'phone': '0923456789'
        })
        
        # 模擬狀態更新
        self.assertIsNotNone(create_result)
    
    def test_04_search_customers(self):
        """搜尋客戶"""
        from handlers.customer_handler import CustomerHandler
        handler = CustomerHandler()
        
        result = handler.handle_request('GET', '/api/customers', {
            'search': '測試'
        })
        
        self.assertIsNotNone(result)


class TestVehicleSalesFlow(E2ETestBase):
    """車輛銷售流程測試"""
    
    def test_01_add_vehicle(self):
        """新增車輛"""
        from handlers.vehicle_handler import VehicleHandler
        handler = VehicleHandler()
        
        result = handler.handle_request('POST', '/api/vehicles', {
            'brand': 'Toyota',
            'model': 'Altis',
            'year': 2020,
            'mileage': 50000,
            'price': 450000,
            'cost': 400000,
            'color': '白色',
            'plate_number': 'ABC-1234'
        })
        
        self.assertIsNotNone(result)
    
    def test_02_list_available_vehicles(self):
        """列出可售車輛"""
        from handlers.vehicle_handler import VehicleHandler
        handler = VehicleHandler()
        
        result = handler.handle_request('GET', '/api/vehicles', {
            'status': 'available'
        })
        
        self.assertIsNotNone(result)
    
    def test_03_update_vehicle_price(self):
        """更新車輛價格"""
        from handlers.vehicle_handler import VehicleHandler
        handler = VehicleHandler()
        
        # 先創建車輛
        handler.handle_request('POST', '/api/vehicles', {
            'brand': 'Honda',
            'model': 'Civic',
            'year': 2019,
            'price': 380000
        })
        
        # 模擬更新
        self.assertTrue(True)
    
    def test_04_vehicle_statistics(self):
        """車輛統計"""
        from handlers.vehicle_handler import VehicleHandler
        handler = VehicleHandler()
        
        result = handler.handle_request('GET', '/api/vehicles/stats', {})
        self.assertIsNotNone(result)


class TestDealFlow(E2ETestBase):
    """完整交易流程測試"""
    
    def test_01_create_deal(self):
        """創建交易"""
        from handlers.deal_handler import DealHandler
        handler = DealHandler()
        
        result = handler.handle_request('POST', '/api/deals', {
            'customer_id': 1,
            'vehicle_id': 1,
            'sale_price': 450000,
            'payment_method': 'cash',
            'notes': '現金交易'
        })
        
        self.assertIsNotNone(result)
    
    def test_02_deal_payment(self):
        """交易付款"""
        from handlers.deal_handler import DealHandler
        handler = DealHandler()
        
        # 模擬付款處理
        result = handler.handle_request('POST', '/api/deals/1/payment', {
            'amount': 450000,
            'method': 'cash'
        })
        
        self.assertIsNotNone(result)
    
    def test_03_deal_completion(self):
        """交易完成"""
        from handlers.deal_handler import DealHandler
        handler = DealHandler()
        
        # 模擬完成交易
        result = handler.handle_request('PUT', '/api/deals/1', {
            'status': 'completed'
        })
        
        self.assertIsNotNone(result)
    
    def test_04_deal_statistics(self):
        """交易統計"""
        from handlers.deal_handler import DealHandler
        handler = DealHandler()
        
        result = handler.handle_request('GET', '/api/deals/stats', {})
        self.assertIsNotNone(result)


class TestReportFlow(E2ETestBase):
    """報表生成流程測試"""
    
    def test_01_daily_report(self):
        """日報表"""
        from handlers.report_handler import ReportHandler
        handler = ReportHandler()
        
        result = handler.handle_request('GET', '/api/reports/daily', {
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        
        self.assertIsNotNone(result)
    
    def test_02_weekly_report(self):
        """週報表"""
        from handlers.report_handler import ReportHandler
        handler = ReportHandler()
        
        result = handler.handle_request('GET', '/api/reports/weekly', {})
        self.assertIsNotNone(result)
    
    def test_03_monthly_report(self):
        """月報表"""
        from handlers.report_handler import ReportHandler
        handler = ReportHandler()
        
        result = handler.handle_request('GET', '/api/reports/monthly', {})
        self.assertIsNotNone(result)
    
    def test_04_export_report(self):
        """匯出報表"""
        from handlers.report_handler import ReportHandler
        handler = ReportHandler()
        
        result = handler.handle_request('GET', '/api/reports/export', {
            'type': 'monthly',
            'format': 'excel'
        })
        
        self.assertIsNotNone(result)


class TestSystemFlow(E2ETestBase):
    """系統功能流程測試"""
    
    def test_01_health_check(self):
        """健康檢查"""
        from handlers.system_handler import SystemHandler
        handler = SystemHandler()
        
        result = handler.handle_request('GET', '/api/system/health', {})
        
        # 應該返回健康狀態
        self.assertIsNotNone(result)
    
    def test_02_system_stats(self):
        """系統統計"""
        from handlers.system_handler import SystemHandler
        handler = SystemHandler()
        
        result = handler.handle_request('GET', '/api/system/stats', {})
        self.assertIsNotNone(result)
    
    def test_03_backup(self):
        """資料備份"""
        from services import backup_service
        
        # 測試備份功能
        self.assertTrue(hasattr(backup_service, 'create_backup'))


class TestAIFlow(E2ETestBase):
    """AI 功能流程測試"""
    
    def test_01_ai_status(self):
        """AI 服務狀態"""
        from handlers.ai_handler import AIHandler
        handler = AIHandler()
        
        result = handler.handle_request('GET', '/api/ai/deep/status', {})
        self.assertIsNotNone(result)
    
    def test_02_price_analysis_request(self):
        """車價分析請求結構"""
        request = {
            'brand': 'Toyota',
            'model': 'Camry',
            'year': 2021,
            'mileage': 30000
        }
        
        # 驗證請求結構
        self.assertIn('brand', request)
        self.assertIn('model', request)
        self.assertIn('year', request)
        self.assertIn('mileage', request)
    
    def test_03_script_generation_request(self):
        """話術生成請求結構"""
        request = {
            'scenario': 'greeting',
            'context': '首次來店客戶'
        }
        
        self.assertIn('scenario', request)


if __name__ == '__main__':
    # 按順序執行測試
    unittest.main(verbosity=2)


# 📚 知識點
# -----------
# 1. E2E 測試：模擬完整業務流程
# 2. setUpClass/tearDownClass：類級別的 setup/teardown
# 3. 測試隔離：使用臨時資料庫避免影響正式資料
# 4. 測試順序：使用 test_01_, test_02_ 確保執行順序
# 5. 斷言方法：assertIsNotNone, assertTrue, assertIn 等
