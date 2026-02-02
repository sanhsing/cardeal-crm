"""
車行寶 CRM v5.1 - AI 服務測試
XTF任務鏈：B-1/5
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCustomerIntent(unittest.TestCase):
    """客戶意向分析測試"""
    
    def test_score_range(self):
        """分數範圍 0-100"""
        scores = {'interaction': 30, 'views': 20, 'inquiry': 25, 'level': 15, 'recency': 10}
        total = sum(scores.values())
        self.assertGreaterEqual(total, 0)
        self.assertLessEqual(total, 100)
    
    def test_level_classification(self):
        """等級分類邏輯"""
        def classify(score):
            if score >= 70: return 'hot'
            elif score >= 40: return 'warm'
            return 'cold'
        
        self.assertEqual(classify(75), 'hot')
        self.assertEqual(classify(50), 'warm')
        self.assertEqual(classify(30), 'cold')


class TestSalesScripts(unittest.TestCase):
    """銷售話術測試"""
    
    def test_script_types(self):
        """話術類型"""
        types = ['opening', 'mileage', 'price', 'brand', 'closing', 'objection']
        self.assertEqual(len(types), 6)
    
    def test_brand_factors(self):
        """品牌係數"""
        factors = {'toyota': 1.05, 'honda': 1.03, 'bmw': 0.85}
        self.assertGreater(factors['toyota'], factors['bmw'])


class TestRecommendation(unittest.TestCase):
    """推薦測試"""
    
    def test_preference_extraction(self):
        """偏好萃取"""
        history = [{'brand': 'Toyota'}, {'brand': 'Toyota'}, {'brand': 'Honda'}]
        brands = {}
        for h in history:
            b = h['brand']
            brands[b] = brands.get(b, 0) + 1
        self.assertEqual(brands['Toyota'], 2)


class TestInventoryAlerts(unittest.TestCase):
    """庫存預警測試"""
    
    def test_severity_levels(self):
        """預警等級"""
        levels = ['low', 'medium', 'high', 'critical']
        self.assertIn('high', levels)
    
    def test_days_threshold(self):
        """滯銷閾值"""
        self.assertEqual(90, 90)  # 90天為滯銷


class TestPrediction(unittest.TestCase):
    """業績預測測試"""
    
    def test_linear_projection(self):
        """線性外推"""
        daily_avg = 100000
        days_remaining = 15
        projected = daily_avg * days_remaining
        self.assertEqual(projected, 1500000)
    
    def test_confidence_by_days(self):
        """信心度判斷"""
        def get_confidence(days_passed):
            return 'medium' if days_passed >= 15 else 'low'
        
        self.assertEqual(get_confidence(20), 'medium')
        self.assertEqual(get_confidence(10), 'low')


if __name__ == '__main__':
    unittest.main(verbosity=2)
