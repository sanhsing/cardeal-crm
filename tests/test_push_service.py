"""
車行寶 CRM v5.2 - Push 服務測試
北斗七星文創數位 × 織明
"""
import unittest
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import push_service


class TestVAPIDManager(unittest.TestCase):
    """VAPID 管理器測試"""
    
    def test_unconfigured(self):
        """測試未配置狀態"""
        manager = push_service.VAPIDManager('', '', '')
        self.assertFalse(manager.is_configured())
    
    def test_configured(self):
        """測試已配置狀態"""
        manager = push_service.VAPIDManager('public', 'private', 'mailto:test@test.com')
        self.assertTrue(manager.is_configured())
    
    def test_get_public_key(self):
        """測試取得公鑰"""
        manager = push_service.VAPIDManager('test_public_key', 'private', 'subject')
        self.assertEqual(manager.get_public_key(), 'test_public_key')


class TestSubscriptionManager(unittest.TestCase):
    """訂閱管理器測試"""
    
    @classmethod
    def setUpClass(cls):
        """建立測試資料庫"""
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix='.db')
    
    @classmethod
    def tearDownClass(cls):
        """清理"""
        os.close(cls.db_fd)
        os.unlink(cls.db_path)
    
    def test_save_subscription(self):
        """測試儲存訂閱"""
        manager = push_service.SubscriptionManager(self.db_path)
        
        subscription = {
            'endpoint': 'https://fcm.googleapis.com/test/12345',
            'keys': {
                'p256dh': 'test_p256dh_key',
                'auth': 'test_auth_key'
            }
        }
        
        result = manager.save(subscription, user_id=1, tenant_id=1)
        self.assertTrue(result['success'])
    
    def test_get_by_user(self):
        """測試按用戶查詢"""
        manager = push_service.SubscriptionManager(self.db_path)
        
        # 先儲存
        subscription = {
            'endpoint': 'https://fcm.googleapis.com/test/user1',
            'keys': {'p256dh': 'key1', 'auth': 'auth1'}
        }
        manager.save(subscription, user_id=1)
        
        # 查詢
        subs = manager.get_by_user(1)
        self.assertGreater(len(subs), 0)
    
    def test_delete_subscription(self):
        """測試刪除訂閱"""
        manager = push_service.SubscriptionManager(self.db_path)
        
        endpoint = 'https://fcm.googleapis.com/test/delete'
        subscription = {
            'endpoint': endpoint,
            'keys': {'p256dh': 'key', 'auth': 'auth'}
        }
        manager.save(subscription)
        
        # 刪除
        result = manager.delete(endpoint)
        self.assertTrue(result['success'])
    
    def test_count(self):
        """測試計數"""
        manager = push_service.SubscriptionManager(self.db_path)
        count = manager.count()
        self.assertIsInstance(count, int)


class TestPushSender(unittest.TestCase):
    """推播發送器測試"""
    
    def test_unconfigured_vapid(self):
        """測試未配置 VAPID"""
        vapid = push_service.VAPIDManager('', '', '')
        sender = push_service.PushSender(vapid)
        
        result = sender.send({}, {})
        self.assertFalse(result['success'])
        self.assertIn('VAPID', result['error'])


class TestConvenienceFunctions(unittest.TestCase):
    """便捷函數測試"""
    
    def test_get_vapid_public_key_unconfigured(self):
        """測試未配置時取得公鑰"""
        # 暫存原值
        original = push_service.vapid
        push_service.vapid = push_service.VAPIDManager('', '', '')
        
        result = push_service.get_vapid_public_key()
        self.assertFalse(result['success'])
        
        # 還原
        push_service.vapid = original


if __name__ == '__main__':
    unittest.main(verbosity=2)
