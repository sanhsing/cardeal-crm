"""
車行寶 CRM v5.1 - 測試基礎框架
北斗七星文創數位 × 織明

使用方式：python -m pytest tests/ -v
"""
import os
import sys
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from models import get_connection, init_master_db
from models.schema import init_tenant_database


class BaseTestCase(unittest.TestCase):
    """測試基礎類別"""
    
    @classmethod
    def setUpClass(cls):
        """測試類別初始化"""
        # 使用臨時目錄
        cls.temp_dir = tempfile.mkdtemp()
        cls.original_data_dir = config.DATA_DIR
        config.DATA_DIR = cls.temp_dir
        config.MASTER_DB = os.path.join(cls.temp_dir, 'master.db')
    
    @classmethod
    def tearDownClass(cls):
        """測試類別清理"""
        config.DATA_DIR = cls.original_data_dir
        # 清理臨時檔案
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def setUp(self):
        """每個測試前執行"""
        # 初始化資料庫
        init_master_db()
    
    def tearDown(self):
        """每個測試後執行"""
        pass
    
    def create_test_tenant(self, code='test', name='測試店家'):
        """建立測試租戶"""
        from models import create_tenant
        result = create_tenant(code, name, '0912345678', 'test1234', '測試管理員')
        return result
    
    def get_test_db_path(self, code='test'):
        """取得測試資料庫路徑"""
        return os.path.join(config.DATA_DIR, f'tenant_{code}.db')


class DatabaseTestCase(BaseTestCase):
    """資料庫測試類別"""
    
    def setUp(self):
        super().setUp()
        self.create_test_tenant()
        self.db_path = self.get_test_db_path()
    
    def insert_test_customer(self, name='測試客戶', phone='0911111111'):
        """插入測試客戶"""
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO customers (name, phone, source, level)
                     VALUES (?, ?, 'walk_in', 'normal')''', (name, phone))
        customer_id = c.lastrowid
        conn.commit()
        conn.close()
        return customer_id
    
    def insert_test_vehicle(self, brand='Toyota', model='Altis'):
        """插入測試車輛"""
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO vehicles (brand, model, year, status)
                     VALUES (?, ?, 2020, 'in_stock')''', (brand, model))
        vehicle_id = c.lastrowid
        conn.commit()
        conn.close()
        return vehicle_id


class APITestCase(BaseTestCase):
    """API 測試類別"""
    
    def setUp(self):
        super().setUp()
        self.create_test_tenant()
        self.mock_handler = self._create_mock_handler()
    
    def _create_mock_handler(self):
        """建立 Mock Handler"""
        handler = Mock()
        handler.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token'
        }
        handler.path = '/api/test'
        handler.command = 'GET'
        handler.client_address = ('127.0.0.1', 12345)
        
        # Mock wfile
        handler.wfile = Mock()
        handler.wfile.write = Mock()
        
        return handler
    
    def mock_session(self, user_id=1, tenant_id=1):
        """建立 Mock Session"""
        return {
            'user_id': user_id,
            'tenant_id': tenant_id,
            'data': {
                'user_id': user_id,
                'user_name': '測試使用者',
                'role': 'admin',
                'tenant_id': tenant_id,
                'tenant_code': 'test',
                'db_path': self.get_test_db_path()
            }
        }


# ===== 斷言輔助 =====

class AssertMixin:
    """斷言輔助方法"""
    
    def assertSuccess(self, result):
        """斷言操作成功"""
        self.assertTrue(result.get('success'), f"Expected success but got: {result}")
    
    def assertFail(self, result):
        """斷言操作失敗"""
        self.assertFalse(result.get('success'), f"Expected failure but got: {result}")
    
    def assertHasKey(self, data, key):
        """斷言有特定鍵"""
        self.assertIn(key, data, f"Expected key '{key}' in {data}")
    
    def assertCountEqual(self, actual, expected):
        """斷言數量相等"""
        self.assertEqual(len(actual), expected, f"Expected {expected} items but got {len(actual)}")


# ===== 執行測試 =====

def run_tests(verbosity=2):
    """執行所有測試"""
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


if __name__ == '__main__':
    run_tests()


# 📚 知識點
# -----------
# 1. unittest 測試框架：
#    - TestCase：測試類別基類
#    - setUp/tearDown：每個測試前後執行
#    - setUpClass/tearDownClass：整個類別前後執行
#
# 2. Mock 模擬：
#    - Mock()：建立模擬物件
#    - patch()：暫時替換模組/物件
#    - 用於隔離測試，不依賴外部資源
#
# 3. tempfile.mkdtemp()：
#    - 建立臨時目錄
#    - 測試結束後清理
#    - 避免污染正式資料
#
# 4. 測試隔離：
#    - 每個測試獨立
#    - 不依賴執行順序
#    - 不共享狀態
#
# 5. 斷言方法：
#    - assertTrue/assertFalse：布林斷言
#    - assertEqual：相等斷言
#    - assertIn：包含斷言
