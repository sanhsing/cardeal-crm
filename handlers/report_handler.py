"""
車行寶 CRM v5.1 - 報表處理器
北斗七星文創數位 × 織明
"""
from datetime import datetime, timedelta
from .base import BaseHandler
from models import get_connection

def get_stats(handler, session):
    """取得統計數據（儀表板用）"""
    db_path = BaseHandler.get_db_path(session)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    stats = {}
    
    # 客戶統計
    c.execute('SELECT COUNT(*) FROM customers WHERE status = "active"')
    stats['customer_count'] = c.fetchone()[0]
    
    c.execute('SELECT level, COUNT(*) FROM customers WHERE status = "active" GROUP BY level')
    stats['customer_by_level'] = {row[0]: row[1] for row in c.fetchall()}
    
    # 車輛統計
    c.execute('SELECT status, COUNT(*) FROM vehicles GROUP BY status')
    stats['vehicle_by_status'] = {row[0]: row[1] for row in c.fetchall()}
    stats['vehicle_in_stock'] = stats['vehicle_by_status'].get('in_stock', 0)
    
    # 本月交易統計
    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    c.execute('''SELECT deal_type, COUNT(*), SUM(amount), SUM(profit)
                 FROM deals 
                 WHERE deal_date >= ? AND status = "completed"
                 GROUP BY deal_type''', (month_start,))
    
    deal_stats = {}
    for row in c.fetchall():
        deal_stats[row[0]] = {
            'count': row[1],
            'amount': row[2] or 0,
            'profit': row[3] or 0
        }
    stats['deals_this_month'] = deal_stats
    
    # 本月營收/利潤
    stats['revenue_this_month'] = deal_stats.get('sell', {}).get('amount', 0)
    stats['profit_this_month'] = deal_stats.get('sell', {}).get('profit', 0)
    
    # 待跟進數量
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''SELECT COUNT(*) FROM customers 
                 WHERE next_followup <= ? AND status = "active"''', (today,))
    stats['pending_followups'] = c.fetchone()[0]
    
    # 近7天新增客戶
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*) FROM customers WHERE created_at >= ?', (week_ago,))
    stats['new_customers_7d'] = c.fetchone()[0]
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'stats': stats
    })


def get_sales_report(handler, session):
    """取得銷售報表"""
    db_path = BaseHandler.get_db_path(session)
    query = BaseHandler.get_query_params(handler)
    
    # 日期範圍
    start_date = query.get('start', [None])[0]
    end_date = query.get('end', [None])[0]
    
    if not start_date:
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 每日銷售
    c.execute('''SELECT deal_date, deal_type, COUNT(*), SUM(amount), SUM(profit)
                 FROM deals 
                 WHERE deal_date BETWEEN ? AND ? AND status = "completed"
                 GROUP BY deal_date, deal_type
                 ORDER BY deal_date''', (start_date, end_date))
    
    daily_data = {}
    for row in c.fetchall():
        date = row[0]
        if date not in daily_data:
            daily_data[date] = {'buy': {}, 'sell': {}}
        daily_data[date][row[1]] = {
            'count': row[2],
            'amount': row[3] or 0,
            'profit': row[4] or 0
        }
    
    # 總計
    c.execute('''SELECT deal_type, COUNT(*), SUM(amount), SUM(profit)
                 FROM deals 
                 WHERE deal_date BETWEEN ? AND ? AND status = "completed"
                 GROUP BY deal_type''', (start_date, end_date))
    
    totals = {}
    for row in c.fetchall():
        totals[row[0]] = {
            'count': row[1],
            'amount': row[2] or 0,
            'profit': row[3] or 0
        }
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'report': {
            'start_date': start_date,
            'end_date': end_date,
            'daily': daily_data,
            'totals': totals
        }
    })


def get_inventory_report(handler, session):
    """取得庫存報表"""
    db_path = BaseHandler.get_db_path(session)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 品牌分佈
    c.execute('''SELECT brand, COUNT(*), SUM(total_cost), SUM(asking_price)
                 FROM vehicles 
                 WHERE status = "in_stock"
                 GROUP BY brand
                 ORDER BY COUNT(*) DESC''')
    
    by_brand = []
    for row in c.fetchall():
        by_brand.append({
            'brand': row[0],
            'count': row[1],
            'total_cost': row[2] or 0,
            'total_asking': row[3] or 0
        })
    
    # 庫齡分析
    c.execute('''SELECT 
                   CASE 
                     WHEN julianday('now') - julianday(purchase_date) <= 30 THEN '0-30天'
                     WHEN julianday('now') - julianday(purchase_date) <= 60 THEN '31-60天'
                     WHEN julianday('now') - julianday(purchase_date) <= 90 THEN '61-90天'
                     ELSE '90天以上'
                   END as age_group,
                   COUNT(*),
                   SUM(total_cost)
                 FROM vehicles 
                 WHERE status = "in_stock" AND purchase_date IS NOT NULL
                 GROUP BY age_group''')
    
    by_age = [{'group': row[0], 'count': row[1], 'cost': row[2] or 0} 
              for row in c.fetchall()]
    
    # 總計
    c.execute('''SELECT COUNT(*), SUM(total_cost), SUM(asking_price), AVG(total_cost)
                 FROM vehicles WHERE status = "in_stock"''')
    row = c.fetchone()
    totals = {
        'count': row[0] or 0,
        'total_cost': row[1] or 0,
        'total_asking': row[2] or 0,
        'avg_cost': round(row[3] or 0)
    }
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'report': {
            'by_brand': by_brand,
            'by_age': by_age,
            'totals': totals
        }
    })


def get_customer_report(handler, session):
    """取得客戶分析報表"""
    db_path = BaseHandler.get_db_path(session)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 來源分佈
    c.execute('''SELECT source, COUNT(*) FROM customers 
                 WHERE status = "active" GROUP BY source''')
    by_source = {row[0]: row[1] for row in c.fetchall()}
    
    # 等級分佈
    c.execute('''SELECT level, COUNT(*) FROM customers 
                 WHERE status = "active" GROUP BY level''')
    by_level = {row[0]: row[1] for row in c.fetchall()}
    
    # Top 10 客戶（按交易金額）
    c.execute('''SELECT id, name, phone, total_deals, total_amount
                 FROM customers 
                 WHERE status = "active"
                 ORDER BY total_amount DESC
                 LIMIT 10''')
    top_customers = [dict(row) for row in c.fetchall()]
    
    # 月度新增趨勢（近6個月）
    c.execute('''SELECT strftime('%Y-%m', created_at) as month, COUNT(*)
                 FROM customers 
                 WHERE created_at >= date('now', '-6 months')
                 GROUP BY month
                 ORDER BY month''')
    monthly_new = [{'month': row[0], 'count': row[1]} for row in c.fetchall()]
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'report': {
            'by_source': by_source,
            'by_level': by_level,
            'top_customers': top_customers,
            'monthly_new': monthly_new
        }
    })


def get_activity_logs(handler, session):
    """取得活動日誌"""
    db_path = BaseHandler.get_db_path(session)
    query = BaseHandler.get_query_params(handler)
    
    limit = int(query.get('limit', [50])[0])
    offset = int(query.get('offset', [0])[0])
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''SELECT * FROM activity_logs 
                 ORDER BY created_at DESC 
                 LIMIT ? OFFSET ?''', (limit, offset))
    logs = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'logs': logs
    })


# 📚 知識點
# -----------
# 1. datetime.now().replace(day=1)：取得當月第一天
#    - replace() 可替換日期的任何部分
#    - .strftime('%Y-%m-%d') 格式化為字串
#
# 2. timedelta：時間差計算
#    - datetime.now() - timedelta(days=7)：7天前
#    - timedelta(hours=1, minutes=30)：1.5小時
#
# 3. julianday() SQLite 函數：
#    - 將日期轉為儒略日數（連續整數）
#    - 方便計算日期差：julianday('now') - julianday(date)
#
# 4. CASE WHEN 條件分組：
#    - SQL 的 if-else
#    - 用於將連續數值分成區間
#
# 5. strftime('%Y-%m', date)：SQLite 日期格式化
#    - %Y：四位年份
#    - %m：兩位月份
#    - 用於按月分組統計
