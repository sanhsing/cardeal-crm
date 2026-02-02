"""
車行寶 CRM v5.2 - 數據分析服務
北斗七星文創數位 × 織明

功能：
1. 銷售趨勢分析
2. 客戶漏斗分析
3. 庫存周轉分析
4. 業績排行榜
5. AI 預測洞察
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict


def get_connection(db_path: str) -> sqlite3.Connection:
    """獲取資料庫連接"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# 1. 銷售趨勢分析
# ============================================================

def get_sales_trend(db_path: str, days: int = 30) -> Dict[str, Any]:
    """獲取銷售趨勢數據"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # 每日銷售額
    c.execute('''
        SELECT DATE(deal_date) as date, 
               COUNT(*) as count,
               SUM(sale_price) as amount
        FROM deals 
        WHERE deal_date >= ? AND status = 'completed'
        GROUP BY DATE(deal_date)
        ORDER BY date
    ''', (start_date,))
    
    daily_data = []
    for row in c.fetchall():
        daily_data.append({
            'date': row['date'],
            'count': row['count'],
            'amount': row['amount'] or 0
        })
    
    # 計算統計
    total_count = sum(d['count'] for d in daily_data)
    total_amount = sum(d['amount'] for d in daily_data)
    avg_daily = total_amount / days if days > 0 else 0
    
    # 同比增長（與上一期比較）
    prev_start = (datetime.now() - timedelta(days=days*2)).strftime('%Y-%m-%d')
    prev_end = start_date
    
    c.execute('''
        SELECT SUM(sale_price) as amount
        FROM deals 
        WHERE deal_date >= ? AND deal_date < ? AND status = 'completed'
    ''', (prev_start, prev_end))
    
    prev_amount = c.fetchone()['amount'] or 0
    growth_rate = ((total_amount - prev_amount) / prev_amount * 100) if prev_amount > 0 else 0
    
    conn.close()
    
    return {
        'daily': daily_data,
        'summary': {
            'total_count': total_count,
            'total_amount': total_amount,
            'avg_daily': round(avg_daily, 2),
            'growth_rate': round(growth_rate, 2)
        }
    }


def get_sales_by_brand(db_path: str, days: int = 30) -> List[Dict[str, Any]]:
    """獲取品牌銷售分佈"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    c.execute('''
        SELECT v.brand, COUNT(*) as count, SUM(d.sale_price) as amount
        FROM deals d
        JOIN vehicles v ON d.vehicle_id = v.id
        WHERE d.deal_date >= ? AND d.status = 'completed'
        GROUP BY v.brand
        ORDER BY amount DESC
        LIMIT 10
    ''', (start_date,))
    
    result = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return result


# ============================================================
# 2. 客戶漏斗分析
# ============================================================

def get_customer_funnel(db_path: str) -> Dict[str, Any]:
    """獲取客戶轉化漏斗"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 各階段客戶數
    status_order = ['potential', 'contacted', 'interested', 'negotiating', 'deal', 'lost']
    funnel = []
    
    for status in status_order:
        c.execute('SELECT COUNT(*) as count FROM customers WHERE status = ?', (status,))
        count = c.fetchone()['count']
        funnel.append({
            'status': status,
            'count': count,
            'label': {
                'potential': '潛在客戶',
                'contacted': '已聯繫',
                'interested': '有興趣',
                'negotiating': '洽談中',
                'deal': '已成交',
                'lost': '已流失'
            }.get(status, status)
        })
    
    # 計算轉化率
    for i in range(1, len(funnel)):
        prev = funnel[i-1]['count']
        curr = funnel[i]['count']
        funnel[i]['conversion'] = round(curr / prev * 100, 1) if prev > 0 else 0
    
    funnel[0]['conversion'] = 100
    
    # 計算整體轉化率
    total = funnel[0]['count']
    deals = next((f['count'] for f in funnel if f['status'] == 'deal'), 0)
    overall_rate = round(deals / total * 100, 1) if total > 0 else 0
    
    conn.close()
    
    return {
        'funnel': funnel,
        'overall_rate': overall_rate
    }


def get_customer_sources(db_path: str) -> List[Dict[str, Any]]:
    """獲取客戶來源分佈"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT source, COUNT(*) as count
        FROM customers
        WHERE source IS NOT NULL AND source != ''
        GROUP BY source
        ORDER BY count DESC
    ''')
    
    result = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return result


# ============================================================
# 3. 庫存分析
# ============================================================

def get_inventory_stats(db_path: str) -> Dict[str, Any]:
    """獲取庫存統計"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 庫存狀態分佈
    c.execute('''
        SELECT status, COUNT(*) as count, SUM(price) as value
        FROM vehicles
        GROUP BY status
    ''')
    
    status_dist = [dict(row) for row in c.fetchall()]
    
    # 品牌分佈
    c.execute('''
        SELECT brand, COUNT(*) as count
        FROM vehicles
        WHERE status = 'available'
        GROUP BY brand
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    brand_dist = [dict(row) for row in c.fetchall()]
    
    # 庫齡分析
    c.execute('''
        SELECT 
            CASE 
                WHEN julianday('now') - julianday(created_at) <= 30 THEN '30天內'
                WHEN julianday('now') - julianday(created_at) <= 60 THEN '30-60天'
                WHEN julianday('now') - julianday(created_at) <= 90 THEN '60-90天'
                ELSE '90天以上'
            END as age_group,
            COUNT(*) as count
        FROM vehicles
        WHERE status = 'available'
        GROUP BY age_group
    ''')
    
    age_dist = [dict(row) for row in c.fetchall()]
    
    # 總體統計
    c.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available,
            SUM(CASE WHEN status = 'available' THEN price ELSE 0 END) as total_value,
            AVG(price) as avg_price
        FROM vehicles
    ''')
    
    summary = dict(c.fetchone())
    
    conn.close()
    
    return {
        'status_distribution': status_dist,
        'brand_distribution': brand_dist,
        'age_distribution': age_dist,
        'summary': {
            'total': summary['total'] or 0,
            'available': summary['available'] or 0,
            'total_value': summary['total_value'] or 0,
            'avg_price': round(summary['avg_price'] or 0, 0)
        }
    }


def get_inventory_turnover(db_path: str, days: int = 90) -> Dict[str, Any]:
    """計算庫存周轉率"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # 期間銷售數量
    c.execute('''
        SELECT COUNT(*) as sold
        FROM deals
        WHERE deal_date >= ? AND status = 'completed'
    ''', (start_date,))
    
    sold = c.fetchone()['sold'] or 0
    
    # 平均庫存（簡化計算：當前庫存）
    c.execute('''
        SELECT COUNT(*) as current_stock
        FROM vehicles
        WHERE status = 'available'
    ''')
    
    current_stock = c.fetchone()['current_stock'] or 0
    
    # 周轉率 = 銷售數量 / 平均庫存
    avg_stock = current_stock + (sold / 2)  # 簡化估算
    turnover_rate = round(sold / avg_stock, 2) if avg_stock > 0 else 0
    
    # 周轉天數
    turnover_days = round(days / turnover_rate) if turnover_rate > 0 else 0
    
    conn.close()
    
    return {
        'period_days': days,
        'sold': sold,
        'current_stock': current_stock,
        'turnover_rate': turnover_rate,
        'turnover_days': turnover_days
    }


# ============================================================
# 4. 業績排行榜
# ============================================================

def get_performance_ranking(db_path: str, days: int = 30) -> Dict[str, Any]:
    """獲取業績排行榜"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # 業務員銷售排行
    c.execute('''
        SELECT u.name, 
               COUNT(*) as deal_count,
               SUM(d.sale_price) as total_amount,
               AVG(d.sale_price) as avg_amount
        FROM deals d
        JOIN users u ON d.created_by = u.id
        WHERE d.deal_date >= ? AND d.status = 'completed'
        GROUP BY d.created_by
        ORDER BY total_amount DESC
        LIMIT 10
    ''', (start_date,))
    
    sales_ranking = [dict(row) for row in c.fetchall()]
    
    # 新增客戶排行
    c.execute('''
        SELECT u.name, COUNT(*) as customer_count
        FROM customers c
        JOIN users u ON c.created_by = u.id
        WHERE c.created_at >= ?
        GROUP BY c.created_by
        ORDER BY customer_count DESC
        LIMIT 10
    ''', (start_date,))
    
    customer_ranking = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return {
        'sales_ranking': sales_ranking,
        'customer_ranking': customer_ranking,
        'period_days': days
    }


# ============================================================
# 5. 綜合儀表板
# ============================================================

def get_dashboard_data(db_path: str) -> Dict[str, Any]:
    """獲取綜合儀表板數據"""
    return {
        'sales_trend': get_sales_trend(db_path, 30),
        'sales_by_brand': get_sales_by_brand(db_path, 30),
        'customer_funnel': get_customer_funnel(db_path),
        'customer_sources': get_customer_sources(db_path),
        'inventory': get_inventory_stats(db_path),
        'turnover': get_inventory_turnover(db_path, 90),
        'performance': get_performance_ranking(db_path, 30),
        'generated_at': datetime.now().isoformat()
    }


def get_kpi_summary(db_path: str) -> Dict[str, Any]:
    """獲取 KPI 摘要"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    
    # 本月銷售
    c.execute('''
        SELECT COUNT(*) as count, COALESCE(SUM(sale_price), 0) as amount
        FROM deals 
        WHERE deal_date >= ? AND status = 'completed'
    ''', (month_start,))
    monthly = dict(c.fetchone())
    
    # 活躍客戶
    c.execute('''
        SELECT COUNT(*) as count
        FROM customers 
        WHERE status NOT IN ('deal', 'lost')
    ''')
    active_customers = c.fetchone()['count']
    
    # 可售車輛
    c.execute('''
        SELECT COUNT(*) as count, COALESCE(SUM(price), 0) as value
        FROM vehicles 
        WHERE status = 'available'
    ''')
    inventory = dict(c.fetchone())
    
    # 待跟進
    c.execute('''
        SELECT COUNT(*) as count
        FROM followups 
        WHERE next_date <= ? AND next_date IS NOT NULL
    ''', (today,))
    pending_followups = c.fetchone()['count']
    
    conn.close()
    
    return {
        'monthly_sales': {
            'count': monthly['count'],
            'amount': monthly['amount']
        },
        'active_customers': active_customers,
        'inventory': {
            'count': inventory['count'],
            'value': inventory['value']
        },
        'pending_followups': pending_followups
    }


# 📚 知識點
# -----------
# 1. SQL 聚合：COUNT, SUM, AVG, GROUP BY
# 2. 日期計算：julianday() 用於計算日期差
# 3. 漏斗分析：追蹤用戶在各階段的轉化
# 4. 周轉率：衡量庫存效率的關鍵指標
# 5. 同比增長：與同期數據比較的百分比變化
