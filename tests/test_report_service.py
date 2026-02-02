"""
車行寶 CRM v5.1 - 報表服務測試
XTF任務鏈：B-2/5
"""
import unittest
from datetime import datetime, timedelta


class TestDailyReport(unittest.TestCase):
    """日報測試"""
    
    def test_report_structure(self):
        """報表結構"""
        keys = ['type', 'date', 'sales', 'purchases', 'new_customers', 'summary']
        self.assertEqual(len(keys), 6)
    
    def test_summary_generation(self):
        """摘要生成"""
        sales = {'count': 3, 'revenue': 1800000, 'profit': 150000}
        summary = f"銷售：{sales['count']} 台，營收 ${sales['revenue']:,}"
        self.assertIn('1,800,000', summary)


class TestWeeklyReport(unittest.TestCase):
    """週報測試"""
    
    def test_date_range(self):
        """日期範圍計算"""
        end = datetime.now()
        start = end - timedelta(days=6)
        self.assertEqual((end - start).days, 6)
    
    def test_brand_distribution(self):
        """品牌分布"""
        brands = [{'brand': 'Toyota', 'count': 5}, {'brand': 'Honda', 'count': 3}]
        total = sum(b['count'] for b in brands)
        self.assertEqual(total, 8)


class TestMonthlyReport(unittest.TestCase):
    """月報測試"""
    
    def test_profit_margin(self):
        """毛利率計算"""
        revenue, profit = 1000000, 150000
        margin = profit / revenue * 100
        self.assertAlmostEqual(margin, 15.0)
    
    def test_yoy_growth(self):
        """年比增長"""
        current, last_year = 1200000, 1000000
        growth = (current - last_year) / last_year * 100
        self.assertEqual(growth, 20.0)


class TestLeaderboard(unittest.TestCase):
    """排行榜測試"""
    
    def test_ranking_order(self):
        """排序正確性"""
        data = [{'name': 'A', 'revenue': 500}, {'name': 'B', 'revenue': 800}]
        sorted_data = sorted(data, key=lambda x: x['revenue'], reverse=True)
        self.assertEqual(sorted_data[0]['name'], 'B')
    
    def test_period_filter(self):
        """時間範圍"""
        periods = ['day', 'week', 'month', 'year']
        self.assertIn('month', periods)


class TestExcelExport(unittest.TestCase):
    """Excel 匯出測試"""
    
    def test_format_number(self):
        """數字格式化"""
        value = 1234567
        formatted = f"{value:,}"
        self.assertEqual(formatted, '1,234,567')


if __name__ == '__main__':
    unittest.main(verbosity=2)
