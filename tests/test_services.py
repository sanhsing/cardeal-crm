"""
車行寶 CRM v5.1 - 服務層測試
北斗七星文創數位 × 織明
"""
import unittest
from unittest.mock import patch, Mock
from .test_base import BaseTestCase, AssertMixin


class TestSecurityService(BaseTestCase, AssertMixin):
    """安全服務測試"""
    
    def test_generate_csrf_token(self):
        """測試 CSRF Token 生成"""
        from services.security_service import generate_csrf_token
        
        token = generate_csrf_token('session123')
        
        self.assertIsNotNone(token)
        self.assertEqual(len(token), 64)  # 32 bytes hex = 64 chars
    
    def test_verify_csrf_token_valid(self):
        """測試 CSRF Token 驗證成功"""
        from services.security_service import generate_csrf_token, verify_csrf_token
        
        session_id = 'session456'
        token = generate_csrf_token(session_id)
        
        result = verify_csrf_token(token, session_id)
        self.assertTrue(result)
    
    def test_verify_csrf_token_wrong_session(self):
        """測試 CSRF Token Session 不匹配"""
        from services.security_service import generate_csrf_token, verify_csrf_token
        
        token = generate_csrf_token('session1')
        result = verify_csrf_token(token, 'session2')
        
        self.assertFalse(result)
    
    def test_rate_limit(self):
        """測試速率限制"""
        from services.security_service import check_rate_limit
        
        # 前5次應該通過
        for i in range(5):
            allowed, remaining, reset = check_rate_limit(f'test_ip_{i}', 'LOGIN')
            self.assertTrue(allowed)
    
    def test_password_hash(self):
        """測試密碼雜湊"""
        from services.security_service import hash_password, verify_password
        
        password = 'mySecretPass123'
        hashed = hash_password(password)
        
        # 驗證格式（salt$hash）
        self.assertIn('$', hashed)
        
        # 驗證正確密碼
        self.assertTrue(verify_password(password, hashed))
        
        # 驗證錯誤密碼
        self.assertFalse(verify_password('wrongpass', hashed))
    
    def test_sanitize_html(self):
        """測試 XSS 防護"""
        from services.security_service import sanitize_html
        
        dangerous = '<script>alert("xss")</script>'
        safe = sanitize_html(dangerous)
        
        self.assertNotIn('<script>', safe)
        self.assertIn('&lt;script&gt;', safe)
    
    def test_validator_phone(self):
        """測試手機號碼驗證"""
        from services.security_service import Validator
        
        self.assertTrue(Validator.phone('0912345678'))
        self.assertTrue(Validator.phone('0988888888'))
        self.assertFalse(Validator.phone('091234567'))   # 少一位
        self.assertFalse(Validator.phone('09123456789')) # 多一位
        self.assertFalse(Validator.phone('0812345678'))  # 不是09開頭
    
    def test_validator_email(self):
        """測試 Email 驗證"""
        from services.security_service import Validator
        
        self.assertTrue(Validator.email('test@example.com'))
        self.assertTrue(Validator.email('user.name@domain.co.uk'))
        self.assertTrue(Validator.email(''))  # 空值允許（可選欄位）
        self.assertFalse(Validator.email('invalid'))
        self.assertFalse(Validator.email('no@domain'))


class TestCacheService(BaseTestCase, AssertMixin):
    """快取服務測試"""
    
    def test_cache_set_get(self):
        """測試快取存取"""
        from services.cache_service import cache_set, cache_get
        
        cache_set('test_key', 'test_value')
        result = cache_get('test_key')
        
        self.assertEqual(result, 'test_value')
    
    def test_cache_default_value(self):
        """測試快取預設值"""
        from services.cache_service import cache_get
        
        result = cache_get('nonexistent_key', 'default')
        self.assertEqual(result, 'default')
    
    def test_cache_delete(self):
        """測試快取刪除"""
        from services.cache_service import cache_set, cache_get, cache_delete
        
        cache_set('delete_key', 'value')
        cache_delete('delete_key')
        
        result = cache_get('delete_key')
        self.assertIsNone(result)
    
    def test_lru_cache_eviction(self):
        """測試 LRU 快取淘汰"""
        from services.cache_service import LRUCache
        
        cache = LRUCache(max_size=3, default_ttl=300)
        
        cache.set('a', 1)
        cache.set('b', 2)
        cache.set('c', 3)
        
        # 存取 a，讓它變成最近使用
        cache.get('a')
        
        # 新增 d，應該淘汰 b（最久沒用）
        cache.set('d', 4)
        
        self.assertIsNone(cache.get('b'))  # b 被淘汰
        self.assertEqual(cache.get('a'), 1)  # a 還在
        self.assertEqual(cache.get('d'), 4)  # d 是新的
    
    def test_cached_decorator(self):
        """測試快取裝飾器"""
        from services.cache_service import cached, cache_clear
        
        cache_clear()
        call_count = 0
        
        @cached(ttl=60, key_prefix='test')
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # 第一次呼叫
        result1 = expensive_function(5)
        self.assertEqual(result1, 10)
        self.assertEqual(call_count, 1)
        
        # 第二次呼叫（應該從快取取）
        result2 = expensive_function(5)
        self.assertEqual(result2, 10)
        self.assertEqual(call_count, 1)  # 沒有增加


class TestPriceService(BaseTestCase, AssertMixin):
    """車價服務測試"""
    
    def test_estimate_price(self):
        """測試車價估算"""
        from services.price_service import estimate_price
        
        result = estimate_price('Toyota', 'Altis', 2020, 50000, 'good')
        
        self.assertSuccess(result)
        self.assertHasKey(result, 'estimated_price')
        self.assertHasKey(result, 'factors')
        
        # 估價應該是正數
        self.assertGreater(result['estimated_price']['mid'], 0)
    
    def test_estimate_price_depreciation(self):
        """測試折舊計算"""
        from services.price_service import estimate_price
        
        # 同款車，年份不同
        newer = estimate_price('Toyota', 'Altis', 2023, 30000, 'good')
        older = estimate_price('Toyota', 'Altis', 2018, 30000, 'good')
        
        # 新車應該比舊車貴
        self.assertGreater(
            newer['estimated_price']['mid'],
            older['estimated_price']['mid']
        )
    
    def test_estimate_price_mileage_impact(self):
        """測試里程影響"""
        from services.price_service import estimate_price
        
        low_mileage = estimate_price('Honda', 'Civic', 2020, 20000, 'good')
        high_mileage = estimate_price('Honda', 'Civic', 2020, 100000, 'good')
        
        # 低里程應該比高里程貴
        self.assertGreater(
            low_mileage['estimated_price']['mid'],
            high_mileage['estimated_price']['mid']
        )


class TestExcelService(BaseTestCase, AssertMixin):
    """Excel 服務測試"""
    
    def test_generate_customer_template(self):
        """測試客戶匯入模板生成"""
        from services.excel_service import generate_customer_template
        
        csv_content = generate_customer_template()
        
        self.assertIn('姓名', csv_content)
        self.assertIn('電話', csv_content)
        self.assertIn('來源', csv_content)
    
    def test_generate_vehicle_template(self):
        """測試車輛匯入模板生成"""
        from services.excel_service import generate_vehicle_template
        
        csv_content = generate_vehicle_template()
        
        self.assertIn('品牌', csv_content)
        self.assertIn('型號', csv_content)
        self.assertIn('購入價', csv_content)


if __name__ == '__main__':
    unittest.main()


# 📚 知識點
# -----------
# 1. unittest.mock：
#    - patch：暫時替換物件
#    - Mock：建立模擬物件
#    - 隔離外部依賴
#
# 2. nonlocal 關鍵字：
#    - 在巢狀函數中修改外層變數
#    - 不是 global，只往外一層
#
# 3. 測試邊界值：
#    - 正常值
#    - 邊界值（最大、最小）
#    - 異常值
#
# 4. 測試覆蓋率：
#    - 正向測試（預期成功）
#    - 負向測試（預期失敗）
#    - 邊界測試
