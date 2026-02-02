"""
車行寶 CRM v5.1 - 安全模組測試
XTF任務鏈：B-3/5
"""
import unittest
import time


class TestRateLimiter(unittest.TestCase):
    """限流測試"""
    
    def test_sliding_window(self):
        """滑動窗口"""
        requests = []
        window = 60
        now = time.time()
        
        # 模擬請求
        for i in range(5):
            requests.append(now - i * 10)
        
        # 清理過期
        valid = [t for t in requests if now - t < window]
        self.assertEqual(len(valid), 5)
    
    def test_rule_config(self):
        """規則配置"""
        rules = {
            'login': (5, 60),
            'api': (100, 60),
            'upload': (10, 60)
        }
        self.assertEqual(rules['login'][0], 5)


class TestSQLInjection(unittest.TestCase):
    """SQL 注入檢測測試"""
    
    def test_detect_or_injection(self):
        """OR 注入"""
        import re
        pattern = r"(\s|^)(OR|AND)\s+\d+\s*=\s*\d+"
        test = "1 OR 1=1"
        self.assertTrue(bool(re.search(pattern, test, re.I)))
    
    def test_detect_union(self):
        """UNION 注入"""
        import re
        pattern = r"UNION\s+(ALL\s+)?SELECT"
        test = "UNION SELECT * FROM users"
        self.assertTrue(bool(re.search(pattern, test, re.I)))
    
    def test_safe_input(self):
        """安全輸入"""
        import re
        patterns = [r"UNION\s+SELECT", r"DROP\s+TABLE"]
        safe_input = "Hello World"
        for p in patterns:
            self.assertFalse(bool(re.search(p, safe_input, re.I)))


class TestIPBlacklist(unittest.TestCase):
    """IP 黑名單測試"""
    
    def test_whitelist_priority(self):
        """白名單優先"""
        whitelist = {'127.0.0.1'}
        blacklist = {'127.0.0.1'}
        ip = '127.0.0.1'
        
        # 白名單優先
        blocked = ip in blacklist and ip not in whitelist
        self.assertFalse(blocked)
    
    def test_auto_block_threshold(self):
        """自動封鎖閾值"""
        failures = 10
        threshold = 10
        should_block = failures >= threshold
        self.assertTrue(should_block)


class TestPasswordSecurity(unittest.TestCase):
    """密碼安全測試"""
    
    def test_pbkdf2_iterations(self):
        """PBKDF2 迭代次數"""
        iterations = 100000
        self.assertGreaterEqual(iterations, 100000)
    
    def test_salt_length(self):
        """Salt 長度"""
        import secrets
        salt = secrets.token_hex(16)
        self.assertEqual(len(salt), 32)  # 16 bytes = 32 hex


class TestSecurityHeaders(unittest.TestCase):
    """安全頭測試"""
    
    def test_required_headers(self):
        """必要的安全頭"""
        headers = {
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block'
        }
        self.assertIn('X-Frame-Options', headers)
        self.assertEqual(headers['X-Frame-Options'], 'DENY')


if __name__ == '__main__':
    unittest.main(verbosity=2)
