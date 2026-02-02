"""
車行寶 CRM v5.1 - 圖表數據服務
北斗七星文創數位 × 織明

功能：儀表板圖表數據生成
"""
from datetime import datetime, timedelta
from typing import Dict, List
from models import get_connection


# ===== 銷售趨勢 =====

def get_sales_trend(db_path: str, days: int = 30) -> Dict:
    """取得銷售趨勢數據
    
    Args:
        db_path: 資料庫路徑
        days: 天數範圍
    
    Returns:
        {labels: [...], revenue: [...], profit: [...], count: [...]}
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    c.execute('''
        SELECT date(deal_date) as date,
               SUM(amount) as revenue,
               SUM(profit) as profit,
               COUNT(*) as count
        FROM deals
        WHERE deal_type = 'sell'
          AND deal_date >= ?
          AND status != 'cancelled'
        GROUP BY date(deal_date)
        ORDER BY date ASC
    ''', (start_date,))
    
    rows = c.fetchall()
    conn.close()
    
    # 填充缺失日期
    labels = []
    revenue = []
    profit = []
    count = []
    
    data_map = {row['date']: row for row in rows}
    
    for i in range(days):
        d = (datetime.now() - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
        labels.append(d[5:])  # MM-DD 格式
        
        if d in data_map:
            revenue.append(data_map[d]['revenue'] or 0)
            profit.append(data_map[d]['profit'] or 0)
            count.append(data_map[d]['count'])
        else:
            revenue.append(0)
            profit.append(0)
            count.append(0)
    
    return {
        'labels': labels,
        'datasets': {
            'revenue': revenue,
            'profit': profit,
            'count': count
        }
    }


def get_monthly_comparison(db_path: str, months: int = 6) -> Dict:
    """取得月度對比數據"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    labels = []
    revenue = []
    profit = []
    count = []
    
    for i in range(months - 1, -1, -1):
        # 計算月份
        date = datetime.now() - timedelta(days=30 * i)
        year_month = date.strftime('%Y-%m')
        labels.append(date.strftime('%m月'))
        
        # 查詢該月數據
        c.execute('''
            SELECT SUM(amount) as revenue,
                   SUM(profit) as profit,
                   COUNT(*) as count
            FROM deals
            WHERE deal_type = 'sell'
              AND strftime('%Y-%m', deal_date) = ?
              AND status != 'cancelled'
        ''', (year_month,))
        
        row = c.fetchone()
        revenue.append(row['revenue'] or 0)
        profit.append(row['profit'] or 0)
        count.append(row['count'] or 0)
    
    conn.close()
    
    return {
        'labels': labels,
        'datasets': {
            'revenue': revenue,
            'profit': profit,
            'count': count
        }
    }


# ===== 庫存分析 =====

def get_inventory_by_brand(db_path: str) -> Dict:
    """取得各品牌庫存分布"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT brand, COUNT(*) as count,
               SUM(total_cost) as total_cost,
               SUM(asking_price) as total_asking
        FROM vehicles
        WHERE status = 'in_stock'
        GROUP BY brand
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    rows = c.fetchall()
    conn.close()
    
    return {
        'labels': [row['brand'] for row in rows],
        'datasets': {
            'count': [row['count'] for row in rows],
            'cost': [row['total_cost'] or 0 for row in rows],
            'asking': [row['total_asking'] or 0 for row in rows]
        }
    }


def get_inventory_by_status(db_path: str) -> Dict:
    """取得庫存狀態分布"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT status, COUNT(*) as count
        FROM vehicles
        GROUP BY status
    ''')
    
    rows = c.fetchall()
    conn.close()
    
    status_names = {
        'in_stock': '在庫',
        'reserved': '已預訂',
        'sold': '已售出',
        'maintenance': '整備中'
    }
    
    return {
        'labels': [status_names.get(row['status'], row['status']) for row in rows],
        'datasets': {
            'count': [row['count'] for row in rows]
        }
    }


def get_inventory_age(db_path: str) -> Dict:
    """取得庫存週期分布"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 分組：0-30天、31-60天、61-90天、90+天
    c.execute('''
        SELECT 
            CASE 
                WHEN julianday('now') - julianday(purchase_date) <= 30 THEN '0-30天'
                WHEN julianday('now') - julianday(purchase_date) <= 60 THEN '31-60天'
                WHEN julianday('now') - julianday(purchase_date) <= 90 THEN '61-90天'
                ELSE '90+天'
            END as age_group,
            COUNT(*) as count
        FROM vehicles
        WHERE status = 'in_stock'
        GROUP BY age_group
        ORDER BY 
            CASE age_group
                WHEN '0-30天' THEN 1
                WHEN '31-60天' THEN 2
                WHEN '61-90天' THEN 3
                ELSE 4
            END
    ''')
    
    rows = c.fetchall()
    conn.close()
    
    return {
        'labels': [row['age_group'] for row in rows],
        'datasets': {
            'count': [row['count'] for row in rows]
        }
    }


# ===== 客戶分析 =====

def get_customer_by_source(db_path: str) -> Dict:
    """取得客戶來源分布"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT source, COUNT(*) as count
        FROM customers
        WHERE status = 'active'
        GROUP BY source
        ORDER BY count DESC
    ''')
    
    rows = c.fetchall()
    conn.close()
    
    source_names = {
        'walk_in': '現場來店',
        'phone': '電話詢問',
        'line': 'LINE',
        'facebook': 'Facebook',
        'referral': '朋友介紹',
        'web': '網站',
        'other': '其他'
    }
    
    return {
        'labels': [source_names.get(row['source'], row['source'] or '未知') for row in rows],
        'datasets': {
            'count': [row['count'] for row in rows]
        }
    }


def get_customer_by_level(db_path: str) -> Dict:
    """取得客戶等級分布"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT level, COUNT(*) as count
        FROM customers
        WHERE status = 'active'
        GROUP BY level
    ''')
    
    rows = c.fetchall()
    conn.close()
    
    level_names = {
        'vip': 'VIP',
        'normal': '一般',
        'potential': '潛在',
        'cold': '冷淡'
    }
    
    return {
        'labels': [level_names.get(row['level'], row['level']) for row in rows],
        'datasets': {
            'count': [row['count'] for row in rows]
        }
    }


def get_customer_growth(db_path: str, months: int = 6) -> Dict:
    """取得客戶成長趨勢"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    labels = []
    new_customers = []
    total_customers = []
    
    for i in range(months - 1, -1, -1):
        date = datetime.now() - timedelta(days=30 * i)
        year_month = date.strftime('%Y-%m')
        labels.append(date.strftime('%m月'))
        
        # 該月新增客戶
        c.execute('''
            SELECT COUNT(*) as count
            FROM customers
            WHERE strftime('%Y-%m', created_at) = ?
        ''', (year_month,))
        new_customers.append(c.fetchone()['count'])
        
        # 截至該月底的總客戶數
        month_end = f"{year_month}-31"
        c.execute('''
            SELECT COUNT(*) as count
            FROM customers
            WHERE date(created_at) <= ?
              AND status = 'active'
        ''', (month_end,))
        total_customers.append(c.fetchone()['count'])
    
    conn.close()
    
    return {
        'labels': labels,
        'datasets': {
            'new': new_customers,
            'total': total_customers
        }
    }


# ===== 綜合儀表板 =====

def get_dashboard_data(db_path: str) -> Dict:
    """取得儀表板所需的所有數據"""
    return {
        'sales_trend': get_sales_trend(db_path, 30),
        'monthly_comparison': get_monthly_comparison(db_path, 6),
        'inventory_by_brand': get_inventory_by_brand(db_path),
        'inventory_by_status': get_inventory_by_status(db_path),
        'inventory_age': get_inventory_age(db_path),
        'customer_by_source': get_customer_by_source(db_path),
        'customer_by_level': get_customer_by_level(db_path),
        'customer_growth': get_customer_growth(db_path, 6)
    }


# 📚 知識點
# -----------
# 1. 圖表數據結構：
#    - labels: X 軸標籤
#    - datasets: 各數據系列
#    - 標準化格式便於前端繪製
#
# 2. 日期填充：
#    - 查詢可能缺少某些日期
#    - 用 data_map 對照填充 0
#    - 保證圖表連續
#
# 3. strftime() 日期格式：
#    - SQLite 內建函數
#    - '%Y-%m' 取年月
#    - '%m月' 中文顯示
#
# 4. CASE WHEN 分組：
#    - SQL 條件分組
#    - 庫存週期分段統計
#    - ORDER BY CASE 自定義排序
#
# 5. julianday() 天數計算：
#    - SQLite Julian 日期
#    - 兩個 julianday 相減 = 天數差
