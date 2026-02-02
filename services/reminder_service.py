"""
車行寶 CRM v5.1 - 跟進提醒服務
北斗七星文創數位 × 織明

功能：跟進提醒、到期通知、LINE/Telegram 推播
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import config
from models import get_connection

# ===== 提醒類型 =====

REMINDER_TYPES = {
    'followup_due': {
        'name': '跟進到期',
        'template': '📋 客戶 {customer_name} 的跟進已到期\n備註：{notes}',
        'priority': 'high'
    },
    'followup_upcoming': {
        'name': '即將跟進',
        'template': '⏰ 客戶 {customer_name} 需要在 {due_date} 前跟進',
        'priority': 'normal'
    },
    'vehicle_long_stock': {
        'name': '車輛庫存過久',
        'template': '🚗 車輛 {vehicle_info} 已在庫 {days} 天',
        'priority': 'normal'
    },
    'customer_cold': {
        'name': '客戶轉冷',
        'template': '❄️ 客戶 {customer_name} 已 {days} 天未跟進',
        'priority': 'low'
    },
    'subscription_expire': {
        'name': '訂閱到期',
        'template': '💳 您的訂閱將於 {expire_date} 到期',
        'priority': 'high'
    }
}


# ===== 取得待提醒項目 =====

def get_due_followups(db_path: str, days_ahead: int = 0) -> List[Dict]:
    """取得到期/即將到期的跟進
    
    Args:
        db_path: 資料庫路徑
        days_ahead: 提前幾天提醒（0=今天到期, 1=明天到期）
    
    Returns:
        跟進列表
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    target_date = datetime.now().date() + timedelta(days=days_ahead)
    
    c.execute('''
        SELECT f.id, f.customer_id, f.content, f.next_date as due_date, 
               f.type, f.result,
               c.name as customer_name, c.phone as customer_phone
        FROM followups f
        JOIN customers c ON f.customer_id = c.id
        WHERE f.result IS NULL
          AND date(f.next_date) <= ?
        ORDER BY f.next_date ASC
    ''', (target_date.isoformat(),))
    
    followups = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return followups


def get_cold_customers(db_path: str, inactive_days: int = 30) -> List[Dict]:
    """取得長期未跟進的客戶
    
    Args:
        db_path: 資料庫路徑
        inactive_days: 多少天未跟進視為冷淡
    
    Returns:
        客戶列表
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    threshold = (datetime.now() - timedelta(days=inactive_days)).isoformat()
    
    c.execute('''
        SELECT c.id, c.name, c.phone, c.level, c.last_contact,
               julianday('now') - julianday(c.last_contact) as days_inactive
        FROM customers c
        WHERE c.status = 'active'
          AND c.level != 'cold'
          AND (c.last_contact IS NULL OR c.last_contact < ?)
        ORDER BY c.last_contact ASC
        LIMIT 50
    ''', (threshold,))
    
    customers = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return customers


def get_long_stock_vehicles(db_path: str, days_threshold: int = 60) -> List[Dict]:
    """取得庫存過久的車輛
    
    Args:
        db_path: 資料庫路徑
        days_threshold: 多少天視為過久
    
    Returns:
        車輛列表
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT id, brand, model, year, plate, purchase_date, asking_price,
               julianday('now') - julianday(purchase_date) as days_in_stock
        FROM vehicles
        WHERE status = 'in_stock'
          AND julianday('now') - julianday(purchase_date) > ?
        ORDER BY purchase_date ASC
    ''', (days_threshold,))
    
    vehicles = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return vehicles


# ===== 發送提醒 =====

def send_reminder_telegram(tenant_id: int, reminder_type: str, data: dict) -> bool:
    """透過 Telegram 發送提醒"""
    from services import telegram_service
    
    if not config.TELEGRAM_BOT_TOKEN:
        return False
    
    template = REMINDER_TYPES.get(reminder_type, {}).get('template', '')
    if not template:
        return False
    
    try:
        message = template.format(**data)
        telegram_service.send_message(message)
        return True
    except Exception as e:
        print(f"Telegram 提醒發送失敗: {e}")
        return False


def send_reminder_line(tenant_id: int, user_line_id: str, 
                       reminder_type: str, data: dict) -> bool:
    """透過 LINE 發送提醒"""
    from services import line_service
    
    if not config.LINE_CHANNEL_ACCESS_TOKEN or not user_line_id:
        return False
    
    template = REMINDER_TYPES.get(reminder_type, {}).get('template', '')
    if not template:
        return False
    
    try:
        message = template.format(**data)
        line_service.push_message(user_line_id, message)
        return True
    except Exception as e:
        print(f"LINE 提醒發送失敗: {e}")
        return False


# ===== 批量處理 =====

def process_daily_reminders(db_path: str, tenant_id: int) -> dict:
    """處理每日提醒
    
    Args:
        db_path: 租戶資料庫路徑
        tenant_id: 租戶 ID
    
    Returns:
        處理結果統計
    """
    stats = {
        'followup_due': 0,
        'followup_upcoming': 0,
        'cold_customers': 0,
        'long_stock': 0,
        'sent': 0,
        'failed': 0
    }
    
    # 今日到期的跟進
    due_today = get_due_followups(db_path, 0)
    stats['followup_due'] = len(due_today)
    
    for f in due_today:
        data = {
            'customer_name': f['customer_name'],
            'notes': f.get('content') or '無',
            'due_date': f['due_date']
        }
        if send_reminder_telegram(tenant_id, 'followup_due', data):
            stats['sent'] += 1
        else:
            stats['failed'] += 1
    
    # 明日到期的跟進
    due_tomorrow = get_due_followups(db_path, 1)
    stats['followup_upcoming'] = len(due_tomorrow)
    
    for f in due_tomorrow:
        data = {
            'customer_name': f['customer_name'],
            'due_date': f['due_date']
        }
        send_reminder_telegram(tenant_id, 'followup_upcoming', data)
    
    # 冷淡客戶（每週一提醒）
    if datetime.now().weekday() == 0:  # 週一
        cold = get_cold_customers(db_path)
        stats['cold_customers'] = len(cold)
        
        if cold:
            message = f"❄️ 本週有 {len(cold)} 位客戶超過30天未跟進\n"
            message += "\n".join([f"• {c['name']}" for c in cold[:10]])
            if len(cold) > 10:
                message += f"\n... 還有 {len(cold) - 10} 位"
            
            from services import telegram_service
            telegram_service.send_message(message)
    
    # 庫存過久（每週一提醒）
    if datetime.now().weekday() == 0:
        long_stock = get_long_stock_vehicles(db_path)
        stats['long_stock'] = len(long_stock)
        
        if long_stock:
            message = f"🚗 庫存超過60天的車輛：{len(long_stock)} 台\n"
            for v in long_stock[:5]:
                days = int(v['days_in_stock'])
                message += f"• {v['brand']} {v['model']} ({days}天)\n"
            
            from services import telegram_service
            telegram_service.send_message(message)
    
    return stats


# ===== API 接口 =====

def get_pending_reminders(db_path: str) -> dict:
    """取得所有待處理提醒（供 API 使用）"""
    return {
        'due_followups': get_due_followups(db_path, 0),
        'upcoming_followups': get_due_followups(db_path, 3),
        'cold_customers': get_cold_customers(db_path)[:10],
        'long_stock_vehicles': get_long_stock_vehicles(db_path)[:10]
    }


def mark_followup_done(db_path: str, followup_id: int, 
                       result: str = None, user_id: int = None) -> dict:
    """標記跟進完成"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''UPDATE followups 
                 SET result = ?
                 WHERE id = ?''',
              (result or '已完成', followup_id))
    
    if c.rowcount == 0:
        conn.close()
        return {'success': False, 'error': '跟進不存在'}
    
    # 更新客戶最後聯絡時間
    c.execute('''UPDATE customers 
                 SET last_contact = datetime('now')
                 WHERE id = (SELECT customer_id FROM followups WHERE id = ?)''',
              (followup_id,))
    
    conn.commit()
    conn.close()
    
    return {'success': True}


def create_next_followup(db_path: str, customer_id: int, 
                         days_later: int = 7, notes: str = None,
                         user_id: int = None, user_name: str = None) -> dict:
    """建立下次跟進"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    next_date = (datetime.now() + timedelta(days=days_later)).strftime('%Y-%m-%d')
    
    c.execute('''INSERT INTO followups 
                 (customer_id, user_id, type, content, next_date)
                 VALUES (?, ?, 'call', ?, ?)''',
              (customer_id, user_id, notes or '定期跟進', next_date))
    
    followup_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {'success': True, 'id': followup_id, 'next_date': next_date}


# 📚 知識點
# -----------
# 1. 提醒系統設計：
#    - 分類型（到期、即將、冷淡）
#    - 分優先級（high/normal/low）
#    - 模板化訊息
#
# 2. 批量處理策略：
#    - 每日執行
#    - 週一特殊處理（週報）
#    - 限制數量避免洗版
#
# 3. julianday() 函數：
#    - SQLite 日期計算
#    - julianday('now') - julianday(date) = 天數差
#
# 4. 多通道通知：
#    - Telegram（管理者）
#    - LINE（客戶/業務）
#    - 失敗不阻斷流程
#
# 5. timedelta 日期計算：
#    - datetime.now() + timedelta(days=7)
#    - 比字串操作更安全
