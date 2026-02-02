"""
車行寶 CRM v5.1 - 交易處理器
PYLIB: L3-cardeal-deal-handler
Version: 1.0.0
Created: 2026-02-02

功能：交易 CRUD API 處理
"""
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# ============================================================
# L0: 基礎常量
# ============================================================

DEAL_TYPES = {
    'buy': {'name': '收購', 'color': '#3b82f6', 'icon': '📥'},
    'sell': {'name': '售出', 'color': '#10b981', 'icon': '📤'},
    'trade_in': {'name': '換購', 'color': '#8b5cf6', 'icon': '🔄'},
    'consign': {'name': '寄賣', 'color': '#f59e0b', 'icon': '📋'},
}

PAYMENT_METHODS = {
    'cash': '現金',
    'transfer': '轉帳',
    'check': '支票',
    'loan': '貸款',
    'mixed': '混合',
}

PAYMENT_STATUS = {
    'pending': {'name': '待付款', 'color': '#f59e0b'},
    'partial': {'name': '部分付款', 'color': '#3b82f6'},
    'completed': {'name': '已完成', 'color': '#10b981'},
    'cancelled': {'name': '已取消', 'color': '#ef4444'},
}

# ============================================================
# L1: 資料結構
# ============================================================

from dataclasses import dataclass
from typing import Optional

@dataclass
class DealDTO:
    """交易資料傳輸物件"""
    deal_type: str
    amount: int
    vehicle_id: Optional[int] = None
    customer_id: Optional[int] = None
    cost: int = 0
    payment_method: str = "cash"
    payment_status: str = "completed"
    deal_date: str = ""
    notes: str = ""
    
    @property
    def profit(self) -> int:
        """計算利潤"""
        return self.amount - self.cost

# ============================================================
# L2: 核心邏輯 - 查詢
# ============================================================

from .base import BaseHandler
from models import get_connection, log_activity

def get_deals(handler, db_path: str, query: Dict) -> None:
    """
    取得交易列表
    
    Args:
        handler: HTTP handler
        db_path: 租戶資料庫路徑
        query: 查詢參數 {deal_type, date_from, date_to, limit}
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 解析參數
    deal_type = query.get('deal_type', [''])[0]
    date_from = query.get('date_from', [''])[0]
    date_to = query.get('date_to', [''])[0]
    limit = int(query.get('limit', [100])[0])
    
    # 建構 SQL
    sql = '''
        SELECT d.*, 
               c.name as customer_name, c.phone as customer_phone,
               v.brand, v.model, v.plate
        FROM deals d
        LEFT JOIN customers c ON d.customer_id = c.id
        LEFT JOIN vehicles v ON d.vehicle_id = v.id
        WHERE 1=1
    '''
    params = []
    
    if deal_type:
        sql += ' AND d.deal_type = ?'
        params.append(deal_type)
    
    if date_from:
        sql += ' AND d.deal_date >= ?'
        params.append(date_from)
    
    if date_to:
        sql += ' AND d.deal_date <= ?'
        params.append(date_to)
    
    sql += ' ORDER BY d.deal_date DESC, d.created_at DESC LIMIT ?'
    params.append(limit)
    
    # 執行查詢
    c.execute(sql, params)
    deals = [dict(row) for row in c.fetchall()]
    
    # 計算匯總
    c.execute('''
        SELECT 
            COUNT(*) as count,
            SUM(amount) as total_amount,
            SUM(profit) as total_profit
        FROM deals
        WHERE deal_type = 'sell'
        AND deal_date >= date('now', 'start of month')
    ''')
    monthly = dict(c.fetchone())
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'deals': deals,
        'monthly_summary': monthly
    })


def get_deal_by_id(handler, db_path: str, deal_id: int) -> None:
    """取得單一交易詳情"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT d.*, 
               c.name as customer_name, c.phone as customer_phone,
               v.brand, v.model, v.plate, v.total_cost as vehicle_cost,
               u.name as created_by_name
        FROM deals d
        LEFT JOIN customers c ON d.customer_id = c.id
        LEFT JOIN vehicles v ON d.vehicle_id = v.id
        LEFT JOIN users u ON d.created_by = u.id
        WHERE d.id = ?
    ''', (deal_id,))
    
    deal = c.fetchone()
    conn.close()
    
    if not deal:
        return BaseHandler.send_json(handler, {
            'success': False,
            'error': '交易不存在'
        }, 404)
    
    BaseHandler.send_json(handler, {
        'success': True,
        'deal': dict(deal)
    })

# ============================================================
# L3: 業務處理 - 增刪改
# ============================================================

def create_deal(handler, db_path: str, data: Dict, user_id: int, user_name: str) -> None:
    """建立交易"""
    deal_type = data.get('deal_type')
    amount = int(data.get('amount', 0))
    
    # 驗證
    if not deal_type or deal_type not in DEAL_TYPES:
        return BaseHandler.send_json(handler, {
            'success': False,
            'error': '請選擇交易類型'
        })
    
    if amount <= 0:
        return BaseHandler.send_json(handler, {
            'success': False,
            'error': '請填寫交易金額'
        })
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 計算成本和利潤
    cost = int(data.get('cost', 0))
    vehicle_id = data.get('vehicle_id')
    
    # 如果是賣出且有車輛，從車輛取得成本
    if deal_type == 'sell' and vehicle_id:
        c.execute('SELECT total_cost FROM vehicles WHERE id = ?', (vehicle_id,))
        vehicle = c.fetchone()
        if vehicle:
            cost = vehicle['total_cost'] or 0
    
    profit = amount - cost
    deal_date = data.get('deal_date') or datetime.now().strftime('%Y-%m-%d')
    
    # 插入交易
    c.execute('''
        INSERT INTO deals 
        (deal_type, customer_id, vehicle_id, amount, cost, profit,
         payment_method, payment_status, deal_date, notes, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        deal_type,
        data.get('customer_id'),
        vehicle_id,
        amount,
        cost,
        profit,
        data.get('payment_method', 'cash'),
        data.get('payment_status', 'completed'),
        deal_date,
        data.get('notes', ''),
        user_id
    ))
    
    deal_id = c.lastrowid
    
    # 如果是賣出，更新車輛狀態
    if deal_type == 'sell' and vehicle_id:
        c.execute('''
            UPDATE vehicles 
            SET status = 'sold', sold_date = ?, sold_price = ?, sold_to = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (deal_date, amount, data.get('customer_id'), vehicle_id))
    
    # 如果是收購，建立車輛記錄（可選）
    # ...
    
    # 更新客戶統計
    customer_id = data.get('customer_id')
    if customer_id:
        c.execute('''
            UPDATE customers 
            SET total_deals = total_deals + 1, 
                total_amount = total_amount + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (amount, customer_id))
    
    conn.commit()
    conn.close()
    
    # 記錄活動
    type_name = DEAL_TYPES[deal_type]['name']
    log_activity(db_path, user_id, user_name, 'create', 'deal', deal_id, 
                 f"{type_name} ${amount:,}")
    
    BaseHandler.send_json(handler, {
        'success': True,
        'id': deal_id,
        'profit': profit,
        'message': f'交易建立成功，利潤 ${profit:,}'
    })


def update_deal(handler, db_path: str, deal_id: int, data: Dict, user_id: int, user_name: str) -> None:
    """更新交易"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 檢查交易是否存在
    c.execute('SELECT * FROM deals WHERE id = ?', (deal_id,))
    deal = c.fetchone()
    
    if not deal:
        conn.close()
        return BaseHandler.send_json(handler, {
            'success': False,
            'error': '交易不存在'
        }, 404)
    
    # 只允許更新部分欄位
    fields = []
    values = []
    
    updatable = ['payment_method', 'payment_status', 'notes']
    
    for key in updatable:
        if key in data:
            fields.append(f'{key} = ?')
            values.append(data[key])
    
    if not fields:
        conn.close()
        return BaseHandler.send_json(handler, {
            'success': False,
            'error': '沒有要更新的欄位'
        })
    
    values.append(deal_id)
    c.execute(f'UPDATE deals SET {", ".join(fields)} WHERE id = ?', values)
    conn.commit()
    conn.close()
    
    # 記錄活動
    log_activity(db_path, user_id, user_name, 'update', 'deal', deal_id, '')
    
    BaseHandler.send_json(handler, {
        'success': True,
        'message': '交易更新成功'
    })


def cancel_deal(handler, db_path: str, deal_id: int, user_id: int, user_name: str) -> None:
    """取消交易"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 取得交易資訊
    c.execute('SELECT * FROM deals WHERE id = ? AND status != "cancelled"', (deal_id,))
    deal = c.fetchone()
    
    if not deal:
        conn.close()
        return BaseHandler.send_json(handler, {
            'success': False,
            'error': '交易不存在或已取消'
        }, 404)
    
    # 更新交易狀態
    c.execute('UPDATE deals SET status = "cancelled" WHERE id = ?', (deal_id,))
    
    # 如果是賣出，恢復車輛狀態
    if deal['deal_type'] == 'sell' and deal['vehicle_id']:
        c.execute('''
            UPDATE vehicles 
            SET status = 'in_stock', sold_date = NULL, sold_price = NULL, sold_to = NULL
            WHERE id = ?
        ''', (deal['vehicle_id'],))
    
    # 更新客戶統計
    if deal['customer_id']:
        c.execute('''
            UPDATE customers 
            SET total_deals = total_deals - 1, 
                total_amount = total_amount - ?
            WHERE id = ?
        ''', (deal['amount'], deal['customer_id']))
    
    conn.commit()
    conn.close()
    
    # 記錄活動
    log_activity(db_path, user_id, user_name, 'cancel', 'deal', deal_id, f"${deal['amount']:,}")
    
    BaseHandler.send_json(handler, {
        'success': True,
        'message': '交易已取消'
    })

# ============================================================
# L4: 統計 & 報表
# ============================================================

def get_deal_stats(handler, db_path: str, query: Dict) -> None:
    """取得交易統計"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    period = query.get('period', ['month'])[0]
    
    # 根據週期設定日期範圍
    if period == 'today':
        date_filter = "date('now')"
    elif period == 'week':
        date_filter = "date('now', '-7 days')"
    elif period == 'month':
        date_filter = "date('now', 'start of month')"
    elif period == 'year':
        date_filter = "date('now', 'start of year')"
    else:
        date_filter = "date('now', 'start of month')"
    
    stats = {}
    
    # 售出統計
    c.execute(f'''
        SELECT COUNT(*), SUM(amount), SUM(profit)
        FROM deals
        WHERE deal_type = 'sell' AND status = 'completed'
        AND deal_date >= {date_filter}
    ''')
    row = c.fetchone()
    stats['sell'] = {
        'count': row[0] or 0,
        'amount': row[1] or 0,
        'profit': row[2] or 0
    }
    
    # 收購統計
    c.execute(f'''
        SELECT COUNT(*), SUM(amount)
        FROM deals
        WHERE deal_type = 'buy' AND status = 'completed'
        AND deal_date >= {date_filter}
    ''')
    row = c.fetchone()
    stats['buy'] = {
        'count': row[0] or 0,
        'amount': row[1] or 0
    }
    
    # 每日趨勢（近7天）
    c.execute('''
        SELECT date(deal_date) as day,
               SUM(CASE WHEN deal_type = 'sell' THEN amount ELSE 0 END) as sell_amount,
               SUM(CASE WHEN deal_type = 'sell' THEN profit ELSE 0 END) as profit
        FROM deals
        WHERE deal_date >= date('now', '-7 days')
        AND status = 'completed'
        GROUP BY day
        ORDER BY day
    ''')
    stats['daily_trend'] = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'period': period,
        'stats': stats
    })


def get_profit_report(handler, db_path: str, query: Dict) -> None:
    """取得利潤報表"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    year = int(query.get('year', [datetime.now().year])[0])
    
    # 月度利潤
    c.execute('''
        SELECT 
            strftime('%m', deal_date) as month,
            COUNT(*) as count,
            SUM(amount) as revenue,
            SUM(cost) as cost,
            SUM(profit) as profit
        FROM deals
        WHERE deal_type = 'sell' AND status = 'completed'
        AND strftime('%Y', deal_date) = ?
        GROUP BY month
        ORDER BY month
    ''', (str(year),))
    
    monthly = []
    for row in c.fetchall():
        monthly.append({
            'month': int(row['month']),
            'count': row['count'],
            'revenue': row['revenue'] or 0,
            'cost': row['cost'] or 0,
            'profit': row['profit'] or 0,
            'margin': round((row['profit'] / row['revenue'] * 100), 1) if row['revenue'] else 0
        })
    
    # 年度匯總
    c.execute('''
        SELECT 
            COUNT(*) as count,
            SUM(amount) as revenue,
            SUM(cost) as cost,
            SUM(profit) as profit
        FROM deals
        WHERE deal_type = 'sell' AND status = 'completed'
        AND strftime('%Y', deal_date) = ?
    ''', (str(year),))
    
    yearly = dict(c.fetchone())
    yearly['margin'] = round((yearly['profit'] / yearly['revenue'] * 100), 1) if yearly['revenue'] else 0
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'year': year,
        'monthly': monthly,
        'yearly': yearly
    })


def get_followups(handler, db_path: str, query: Dict) -> None:
    """取得跟進列表"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 篩選條件
    status = query.get('status', ['pending'])[0]
    limit = int(query.get('limit', ['50'])[0])
    
    if status == 'pending':
        # 待跟進：有設定下次跟進日期且未完成
        c.execute('''
            SELECT c.id as customer_id, c.name as customer_name, c.phone,
                   c.next_followup, c.level, c.notes,
                   MAX(f.created_at) as last_followup_date,
                   (SELECT content FROM followups WHERE customer_id = c.id ORDER BY created_at DESC LIMIT 1) as last_content
            FROM customers c
            LEFT JOIN followups f ON c.id = f.customer_id
            WHERE c.status = 'active'
            AND c.next_followup IS NOT NULL
            AND c.next_followup <= date('now', '+7 days')
            GROUP BY c.id
            ORDER BY c.next_followup ASC
            LIMIT ?
        ''', (limit,))
    else:
        # 所有跟進記錄
        c.execute('''
            SELECT f.id, f.customer_id, c.name as customer_name, c.phone,
                   f.followup_type, f.content, f.created_at, f.created_by
            FROM followups f
            JOIN customers c ON f.customer_id = c.id
            ORDER BY f.created_at DESC
            LIMIT ?
        ''', (limit,))
    
    rows = c.fetchall()
    conn.close()
    
    followups = [dict(row) for row in rows]
    
    BaseHandler.send_json(handler, {
        'success': True,
        'followups': followups,
        'count': len(followups)
    })


def create_followup(handler, db_path: str, data: Dict, user_id: int, user_name: str) -> None:
    """建立跟進記錄"""
    customer_id = data.get('customer_id')
    followup_type = data.get('followup_type', 'phone')  # phone/line/visit/other
    content = data.get('content', '')
    next_followup = data.get('next_followup')  # 下次跟進日期
    
    if not customer_id:
        return BaseHandler.send_json(handler, {'success': False, 'error': '缺少客戶 ID'}, 400)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    try:
        # 新增跟進記錄
        c.execute('''
            INSERT INTO followups (customer_id, followup_type, content, created_by)
            VALUES (?, ?, ?, ?)
        ''', (customer_id, followup_type, content, user_name))
        
        followup_id = c.lastrowid
        
        # 更新客戶的最後聯繫和下次跟進
        if next_followup:
            c.execute('''
                UPDATE customers 
                SET last_contact = datetime('now'), next_followup = ?
                WHERE id = ?
            ''', (next_followup, customer_id))
        else:
            c.execute('''
                UPDATE customers 
                SET last_contact = datetime('now')
                WHERE id = ?
            ''', (customer_id,))
        
        # 記錄操作日誌
        c.execute('''
            INSERT INTO activity_logs (user_id, user_name, action, target_type, target_id, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, user_name, 'create', 'followup', followup_id, content[:100]))
        
        conn.commit()
        
        BaseHandler.send_json(handler, {
            'success': True,
            'id': followup_id,
            'message': '跟進記錄已新增'
        })
        
    except Exception as e:
        conn.rollback()
        BaseHandler.send_json(handler, {'success': False, 'error': str(e)}, 500)
    finally:
        conn.close()


# 📚 知識點
# -----------
# 1. strftime('%Y', date)：SQLite 日期格式化
#    - %Y：四位年（2026）
#    - %m：兩位月（01-12）
#    - %d：兩位日（01-31）
#    - %H:%M:%S：時:分:秒
#
# 2. SUM(CASE WHEN ... THEN ... ELSE 0 END)：條件加總
#    - SQL 版的 if-else
#    - 用於同一查詢中分類統計
#
# 3. round(value, 1)：四捨五入到小數點後1位
#    - round(3.1415, 2) → 3.14
#
# 4. 交易取消的反向操作：
#    - 更新車輛狀態
#    - 減少客戶統計
#    - 這種操作要在同一個事務中完成
