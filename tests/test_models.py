"""
車行寶 CRM v5.1 - 資料模型測試
北斗七星文創數位 × 織明
"""
import unittest
from .test_base import DatabaseTestCase, AssertMixin
from models import get_connection, verify_login, create_tenant


class TestTenant(DatabaseTestCase, AssertMixin):
    """租戶模組測試"""
    
    def test_create_tenant_success(self):
        """測試建立租戶成功"""
        result = create_tenant('shop1', '測試車行', '0922222222', 'pass123', '老闆')
        self.assertSuccess(result)
        self.assertHasKey(result, 'tenant_id')
    
    def test_create_tenant_duplicate_code(self):
        """測試重複店家代碼"""
        create_tenant('shop2', '車行A', '0933333333', 'pass', '老闆A')
        result = create_tenant('shop2', '車行B', '0944444444', 'pass', '老闆B')
        self.assertFail(result)
        self.assertIn('已存在', result.get('error', ''))
    
    def test_verify_login_success(self):
        """測試登入成功"""
        result = verify_login('test', '0912345678', 'test1234')
        self.assertSuccess(result)
        self.assertHasKey(result, 'user_id')
        self.assertHasKey(result, 'tenant_id')
    
    def test_verify_login_wrong_password(self):
        """測試密碼錯誤"""
        result = verify_login('test', '0912345678', 'wrongpass')
        self.assertFail(result)
    
    def test_verify_login_wrong_tenant(self):
        """測試店家代碼錯誤"""
        result = verify_login('notexist', '0912345678', 'test1234')
        self.assertFail(result)


class TestCustomer(DatabaseTestCase, AssertMixin):
    """客戶模組測試"""
    
    def test_insert_customer(self):
        """測試新增客戶"""
        customer_id = self.insert_test_customer('王小明', '0955555555')
        self.assertIsNotNone(customer_id)
        self.assertGreater(customer_id, 0)
    
    def test_query_customer(self):
        """測試查詢客戶"""
        customer_id = self.insert_test_customer('李大華', '0966666666')
        
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        customer = c.fetchone()
        conn.close()
        
        self.assertIsNotNone(customer)
        self.assertEqual(customer['name'], '李大華')
        self.assertEqual(customer['phone'], '0966666666')
    
    def test_update_customer(self):
        """測試更新客戶"""
        customer_id = self.insert_test_customer()
        
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute('UPDATE customers SET level = ? WHERE id = ?', ('vip', customer_id))
        conn.commit()
        
        c.execute('SELECT level FROM customers WHERE id = ?', (customer_id,))
        level = c.fetchone()[0]
        conn.close()
        
        self.assertEqual(level, 'vip')
    
    def test_soft_delete_customer(self):
        """測試軟刪除客戶"""
        customer_id = self.insert_test_customer()
        
        conn = get_connection(self.db_path)
        c = conn.cursor()
        c.execute('UPDATE customers SET status = ? WHERE id = ?', ('deleted', customer_id))
        conn.commit()
        
        c.execute('SELECT status FROM customers WHERE id = ?', (customer_id,))
        status = c.fetchone()[0]
        conn.close()
        
        self.assertEqual(status, 'deleted')


class TestVehicle(DatabaseTestCase, AssertMixin):
    """車輛模組測試"""
    
    def test_insert_vehicle(self):
        """測試新增車輛"""
        vehicle_id = self.insert_test_vehicle('Honda', 'Civic')
        self.assertIsNotNone(vehicle_id)
        self.assertGreater(vehicle_id, 0)
    
    def test_vehicle_status_change(self):
        """測試車輛狀態變更"""
        vehicle_id = self.insert_test_vehicle()
        
        conn = get_connection(self.db_path)
        c = conn.cursor()
        
        # 預訂
        c.execute('UPDATE vehicles SET status = ? WHERE id = ?', ('reserved', vehicle_id))
        conn.commit()
        
        c.execute('SELECT status FROM vehicles WHERE id = ?', (vehicle_id,))
        self.assertEqual(c.fetchone()[0], 'reserved')
        
        # 售出
        c.execute('UPDATE vehicles SET status = ?, sold_date = date("now") WHERE id = ?', 
                  ('sold', vehicle_id))
        conn.commit()
        
        c.execute('SELECT status FROM vehicles WHERE id = ?', (vehicle_id,))
        self.assertEqual(c.fetchone()[0], 'sold')
        
        conn.close()
    
    def test_vehicle_cost_calculation(self):
        """測試車輛成本計算"""
        conn = get_connection(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO vehicles 
                     (brand, model, year, purchase_price, repair_cost, total_cost, status)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  ('Mazda', '3', 2021, 500000, 30000, 530000, 'in_stock'))
        vehicle_id = c.lastrowid
        conn.commit()
        
        c.execute('SELECT purchase_price, repair_cost, total_cost FROM vehicles WHERE id = ?',
                  (vehicle_id,))
        row = c.fetchone()
        conn.close()
        
        self.assertEqual(row['total_cost'], row['purchase_price'] + row['repair_cost'])


class TestDeal(DatabaseTestCase, AssertMixin):
    """交易模組測試"""
    
    def test_create_deal(self):
        """測試建立交易"""
        customer_id = self.insert_test_customer()
        vehicle_id = self.insert_test_vehicle()
        
        conn = get_connection(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO deals 
                     (deal_type, customer_id, vehicle_id, amount, cost, profit, deal_date)
                     VALUES (?, ?, ?, ?, ?, ?, date("now"))''',
                  ('sell', customer_id, vehicle_id, 600000, 530000, 70000))
        deal_id = c.lastrowid
        conn.commit()
        conn.close()
        
        self.assertGreater(deal_id, 0)
    
    def test_deal_profit_calculation(self):
        """測試交易利潤計算"""
        customer_id = self.insert_test_customer()
        vehicle_id = self.insert_test_vehicle()
        
        conn = get_connection(self.db_path)
        c = conn.cursor()
        
        amount = 600000
        cost = 530000
        profit = amount - cost
        
        c.execute('''INSERT INTO deals 
                     (deal_type, customer_id, vehicle_id, amount, cost, profit, deal_date)
                     VALUES (?, ?, ?, ?, ?, ?, date("now"))''',
                  ('sell', customer_id, vehicle_id, amount, cost, profit))
        deal_id = c.lastrowid
        conn.commit()
        
        c.execute('SELECT profit FROM deals WHERE id = ?', (deal_id,))
        saved_profit = c.fetchone()[0]
        conn.close()
        
        self.assertEqual(saved_profit, 70000)


if __name__ == '__main__':
    unittest.main()


# 📚 知識點
# -----------
# 1. 測試命名規範：
#    - test_ 開頭
#    - 描述測試目的
#    - test_create_tenant_success
#
# 2. AAA 模式：
#    - Arrange：準備測試資料
#    - Act：執行被測試的動作
#    - Assert：驗證結果
#
# 3. 邊界測試：
#    - 正常情況
#    - 錯誤情況
#    - 邊界值
#
# 4. 測試隔離：
#    - 每個測試獨立
#    - setUp 重置狀態
#    - 不依賴執行順序
