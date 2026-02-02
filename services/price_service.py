"""
車行寶 CRM v5.1 - 車價參考服務
北斗七星文創數位 × 織明

功能：車輛估價、市場行情參考
"""
import json
import urllib.request
from datetime import datetime, timedelta
from models import get_connection

# ===== 內部估價 =====

def estimate_price(brand, model, year, mileage, condition='good'):
    """根據車輛資訊估價
    
    Args:
        brand: 品牌
        model: 型號
        year: 年份
        mileage: 里程數
        condition: 狀況 ('excellent', 'good', 'fair', 'poor')
    
    Returns:
        估價資訊字典
    """
    # 基礎折舊計算
    current_year = datetime.now().year
    age = current_year - int(year)
    
    # 年份折舊率（每年約 10-15%）
    depreciation_rate = 0.12
    age_factor = max(0.3, (1 - depreciation_rate) ** age)
    
    # 里程折舊（每 10000km 約 2%）
    mileage_factor = max(0.7, 1 - (int(mileage) / 10000) * 0.02)
    
    # 狀況係數
    condition_factors = {
        'excellent': 1.1,
        'good': 1.0,
        'fair': 0.85,
        'poor': 0.7
    }
    condition_factor = condition_factors.get(condition, 1.0)
    
    # 品牌係數（保值率）
    brand_factors = {
        'toyota': 1.05, 'lexus': 1.1,
        'honda': 1.03, 'mazda': 1.0,
        'nissan': 0.95, 'mitsubishi': 0.92,
        'ford': 0.9, 'hyundai': 0.88,
        'kia': 0.87, 'suzuki': 0.9,
        'bmw': 0.85, 'mercedes': 0.85, 'benz': 0.85,
        'audi': 0.83, 'volkswagen': 0.85, 'vw': 0.85,
        'volvo': 0.88, 'subaru': 0.95,
    }
    brand_lower = brand.lower()
    brand_factor = brand_factors.get(brand_lower, 0.9)
    
    # 基礎新車價參考（簡化版，實際應查詢資料庫）
    base_prices = _get_base_price(brand_lower, model.lower())
    
    # 計算估價
    total_factor = age_factor * mileage_factor * condition_factor * brand_factor
    estimated_low = int(base_prices['low'] * total_factor)
    estimated_mid = int(base_prices['mid'] * total_factor)
    estimated_high = int(base_prices['high'] * total_factor)
    
    return {
        'success': True,
        'brand': brand,
        'model': model,
        'year': year,
        'mileage': mileage,
        'condition': condition,
        'factors': {
            'age': round(age_factor, 2),
            'mileage': round(mileage_factor, 2),
            'condition': round(condition_factor, 2),
            'brand': round(brand_factor, 2),
            'total': round(total_factor, 2)
        },
        'estimated_price': {
            'low': estimated_low,
            'mid': estimated_mid,
            'high': estimated_high
        },
        'note': '此為參考估價，實際價格需考慮市場供需、車況細節等因素'
    }


def _get_base_price(brand, model):
    """取得基礎參考價格"""
    # 常見車款參考價（新車價）
    price_db = {
        ('toyota', 'altis'): {'low': 700000, 'mid': 750000, 'high': 850000},
        ('toyota', 'camry'): {'low': 1000000, 'mid': 1100000, 'high': 1300000},
        ('toyota', 'yaris'): {'low': 550000, 'mid': 600000, 'high': 700000},
        ('toyota', 'rav4'): {'low': 950000, 'mid': 1050000, 'high': 1200000},
        ('toyota', 'cross'): {'low': 750000, 'mid': 850000, 'high': 950000},
        ('honda', 'civic'): {'low': 800000, 'mid': 900000, 'high': 1000000},
        ('honda', 'crv'): {'low': 950000, 'mid': 1050000, 'high': 1200000},
        ('honda', 'fit'): {'low': 650000, 'mid': 720000, 'high': 800000},
        ('mazda', '3'): {'low': 750000, 'mid': 850000, 'high': 950000},
        ('mazda', 'cx5'): {'low': 900000, 'mid': 1000000, 'high': 1150000},
        ('nissan', 'sentra'): {'low': 650000, 'mid': 720000, 'high': 800000},
        ('nissan', 'kicks'): {'low': 700000, 'mid': 780000, 'high': 880000},
    }
    
    key = (brand, model)
    if key in price_db:
        return price_db[key]
    
    # 預設價格（根據品牌）
    defaults = {
        'toyota': {'low': 700000, 'mid': 800000, 'high': 900000},
        'lexus': {'low': 1500000, 'mid': 1800000, 'high': 2200000},
        'honda': {'low': 700000, 'mid': 800000, 'high': 900000},
        'mazda': {'low': 750000, 'mid': 850000, 'high': 950000},
        'bmw': {'low': 1500000, 'mid': 2000000, 'high': 2500000},
        'mercedes': {'low': 1600000, 'mid': 2100000, 'high': 2600000},
        'benz': {'low': 1600000, 'mid': 2100000, 'high': 2600000},
    }
    
    return defaults.get(brand, {'low': 500000, 'mid': 600000, 'high': 700000})


# ===== 歷史行情 =====

def get_price_history(db_path, brand=None, model=None, months=6):
    """取得歷史成交價格"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')
    
    sql = '''SELECT v.brand, v.model, v.year, d.amount, d.deal_date
             FROM deals d
             JOIN vehicles v ON d.vehicle_id = v.id
             WHERE d.deal_type = "sell" 
             AND d.status = "completed"
             AND d.deal_date >= ?'''
    params = [start_date]
    
    if brand:
        sql += ' AND v.brand = ?'
        params.append(brand)
    if model:
        sql += ' AND v.model = ?'
        params.append(model)
    
    sql += ' ORDER BY d.deal_date DESC'
    
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'brand': row['brand'],
            'model': row['model'],
            'year': row['year'],
            'price': row['amount'],
            'date': row['deal_date']
        })
    
    # 計算統計
    if history:
        prices = [h['price'] for h in history]
        stats = {
            'count': len(prices),
            'avg': int(sum(prices) / len(prices)),
            'min': min(prices),
            'max': max(prices)
        }
    else:
        stats = {'count': 0, 'avg': 0, 'min': 0, 'max': 0}
    
    return {
        'success': True,
        'history': history[:20],  # 最多返回20筆
        'stats': stats
    }


# ===== 市場比較 =====

def compare_with_market(db_path, vehicle_id):
    """與市場行情比較"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 取得車輛資訊
    c.execute('SELECT brand, model, year, mileage, asking_price FROM vehicles WHERE id = ?', 
              (vehicle_id,))
    vehicle = c.fetchone()
    
    if not vehicle:
        conn.close()
        return {'success': False, 'error': '車輛不存在'}
    
    # 取得同款車歷史成交
    c.execute('''SELECT AVG(d.amount) as avg_price, COUNT(*) as count
                 FROM deals d
                 JOIN vehicles v ON d.vehicle_id = v.id
                 WHERE v.brand = ? AND v.model = ? 
                 AND d.deal_type = "sell" AND d.status = "completed"
                 AND d.deal_date >= date("now", "-6 months")''',
              (vehicle['brand'], vehicle['model']))
    market = c.fetchone()
    conn.close()
    
    # 估價
    estimate = estimate_price(
        vehicle['brand'], 
        vehicle['model'], 
        vehicle['year'], 
        vehicle['mileage']
    )
    
    asking = vehicle['asking_price'] or 0
    market_avg = int(market['avg_price'] or 0)
    
    # 定價分析
    if market_avg > 0:
        price_diff = asking - market_avg
        price_ratio = asking / market_avg
        if price_ratio > 1.15:
            advice = '定價偏高，可能較難成交'
        elif price_ratio > 1.05:
            advice = '定價略高於市場，有議價空間'
        elif price_ratio > 0.95:
            advice = '定價合理，符合市場行情'
        else:
            advice = '定價具競爭力，應可快速成交'
    else:
        price_diff = 0
        price_ratio = 1
        advice = '無足夠市場資料比較'
    
    return {
        'success': True,
        'vehicle': dict(vehicle),
        'market': {
            'avg_price': market_avg,
            'sample_count': market['count'] or 0
        },
        'estimate': estimate['estimated_price'],
        'analysis': {
            'asking_price': asking,
            'diff_from_market': price_diff,
            'ratio': round(price_ratio, 2),
            'advice': advice
        }
    }


# 📚 知識點
# -----------
# 1. 折舊計算：
#    - 複利折舊：(1 - rate) ** years
#    - 每年 12% 折舊，5年後剩 (0.88)^5 ≈ 53%
#    - max() 設定下限，避免價格過低
#
# 2. 係數設計：
#    - 多個係數相乘得到總係數
#    - 每個係數獨立可調
#    - 容易理解和維護
#
# 3. 字典的 .get() 方法：
#    - dict.get(key, default)
#    - key 不存在時返回 default
#    - 避免 KeyError
#
# 4. SQL JOIN：
#    - JOIN vehicles v ON d.vehicle_id = v.id
#    - 連結兩個表的資料
#    - 可用 v.brand 引用 vehicles 表的欄位
#
# 5. 日期計算：
#    - date("now", "-6 months")：SQLite 日期函數
#    - 計算 6 個月前的日期
