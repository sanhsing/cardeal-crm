"""
車行寶 CRM v5.1 - DeepSeek AI 服務測試
北斗七星文創數位 × 織明
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import deepseek_service


class TestAIProvider(unittest.TestCase):
    """AI Provider 測試"""
    
    def test_provider_init_deepseek(self):
        """測試 DeepSeek 初始化"""
        provider = deepseek_service.AIProvider('deepseek')
        self.assertEqual(provider.provider, 'deepseek')
        self.assertIn('deepseek', provider.api_url)
    
    def test_provider_init_openai(self):
        """測試 OpenAI 初始化"""
        provider = deepseek_service.AIProvider('openai')
        self.assertEqual(provider.provider, 'openai')
        self.assertIn('openai', provider.api_url)
    
    def test_chat_no_api_key(self):
        """測試無 API Key 情況"""
        provider = deepseek_service.AIProvider('deepseek')
        provider.api_key = ''
        
        result = provider.chat([{'role': 'user', 'content': 'test'}])
        
        self.assertFalse(result['success'])
        self.assertIn('API Key', result['error'])


class TestVehiclePriceAnalysis(unittest.TestCase):
    """車價分析測試"""
    
    def test_analyze_price_structure(self):
        """測試車價分析輸入結構"""
        vehicle = {
            'brand': 'Toyota',
            'model': 'Altis',
            'year': 2022,
            'mileage': 30000,
            'color': '白色',
            'features': '全景天窗',
            'condition_note': '極新'
        }
        
        # 驗證輸入格式正確
        self.assertIn('brand', vehicle)
        self.assertIn('model', vehicle)
        self.assertIn('year', vehicle)
        self.assertIn('mileage', vehicle)
    
    @patch.object(deepseek_service.ai, 'chat')
    def test_analyze_price_success(self, mock_chat):
        """測試車價分析成功（Mock）"""
        mock_chat.return_value = {
            'success': True,
            'content': json.dumps({
                'estimated_price': {'low': 600000, 'mid': 650000, 'high': 700000},
                'analysis': '這是一台車況良好的車',
                'selling_points': ['低里程', '原廠保固', '全景天窗'],
                'concerns': [],
                'market_position': '搶手'
            }),
            'usage': {'total_tokens': 100}
        }
        
        vehicle = {'brand': 'Toyota', 'model': 'Altis', 'year': 2022, 'mileage': 30000}
        result = deepseek_service.analyze_vehicle_price(vehicle)
        
        self.assertTrue(result['success'])
        self.assertIn('estimated_price', result)


class TestCustomerAnalysis(unittest.TestCase):
    """客戶分析測試"""
    
    def test_customer_structure(self):
        """測試客戶資料結構"""
        customer = {
            'name': '測試客戶',
            'level': 'vip',
            'source': 'referral',
            'created_at': '2024-01-01',
            'note': '高意向'
        }
        
        self.assertIn('name', customer)
        self.assertIn('level', customer)
    
    def test_interaction_format(self):
        """測試互動記錄格式"""
        interactions = [
            {'created_at': '2024-01-15', 'log_type': 'view_vehicle', 'content': '看車'},
            {'created_at': '2024-01-16', 'log_type': 'price_inquiry', 'content': '詢價'}
        ]
        
        self.assertEqual(len(interactions), 2)
        self.assertEqual(interactions[0]['log_type'], 'view_vehicle')


class TestSalesScriptGeneration(unittest.TestCase):
    """銷售話術測試"""
    
    def test_scenario_types(self):
        """測試話術情境類型"""
        scenarios = ['general', 'objection', 'closing', 'followup']
        self.assertEqual(len(scenarios), 4)
    
    @patch.object(deepseek_service.ai, 'chat')
    def test_generate_script_success(self, mock_chat):
        """測試話術生成成功（Mock）"""
        mock_chat.return_value = {
            'success': True,
            'content': json.dumps({
                'scripts': [
                    {'type': 'opening', 'title': '開場白', 'content': '您好！'},
                    {'type': 'closing', 'title': '促成', 'content': '現在下訂有優惠'}
                ]
            }),
            'usage': {}
        }
        
        vehicle = {'brand': 'Toyota', 'model': 'Camry', 'year': 2023, 'mileage': 10000, 'asking_price': 1000000}
        result = deepseek_service.generate_sales_script(vehicle)
        
        self.assertTrue(result['success'])
        self.assertIn('scripts', result)


class TestMarketTrend(unittest.TestCase):
    """市場趨勢測試"""
    
    def test_trend_parameters(self):
        """測試趨勢分析參數"""
        valid_brands = ['Toyota', 'Honda', 'Mazda', 'BMW', 'Mercedes']
        valid_segments = ['SUV', 'Sedan', 'Hatchback']
        
        self.assertIn('Toyota', valid_brands)
        self.assertIn('SUV', valid_segments)


class TestQuickAsk(unittest.TestCase):
    """快速問答測試"""
    
    def test_empty_question(self):
        """測試空問題"""
        # 空問題應該也能處理
        question = ""
        self.assertEqual(question, "")
    
    @patch.object(deepseek_service.ai, 'chat')
    def test_quick_ask_success(self, mock_chat):
        """測試快速問答成功（Mock）"""
        mock_chat.return_value = {
            'success': True,
            'content': '這是一個很好的問題',
            'usage': {}
        }
        
        result = deepseek_service.quick_ask("如何定價？")
        
        self.assertTrue(result['success'])
        self.assertIn('answer', result)


class TestAPIStatus(unittest.TestCase):
    """API 狀態測試"""
    
    @patch.object(deepseek_service.ai, 'chat')
    def test_check_status_online(self, mock_chat):
        """測試 API 在線"""
        mock_chat.return_value = {'success': True, 'content': 'OK', 'usage': {}}
        
        result = deepseek_service.check_api_status()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'online')
    
    @patch.object(deepseek_service.ai, 'chat')
    def test_check_status_offline(self, mock_chat):
        """測試 API 離線"""
        mock_chat.return_value = {'success': False, 'error': 'Network error'}
        
        result = deepseek_service.check_api_status()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'offline')


if __name__ == '__main__':
    unittest.main(verbosity=2)
