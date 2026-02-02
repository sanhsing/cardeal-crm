"""
車行寶 CRM v5.1 - 客戶處理器
北斗七星文創數位 × 織明
"""
from typing import Dict
from .base import BaseHandler
from models import get_connection


def get_customers(handler, session) -> None:
    """取得客戶列表"""
    db_path = session['data']['db_path']
    query = BaseHandler.get_query_params(handler)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 基本查詢
    sql = '''SELECT id, name, phone, phone2, email, address, 
                    source, level, status, notes,
                    total_deals, total_amount, last_contact,
                    next_followup, created_at
             FROM customers WHERE status != "deleted"'''
    params = []
    
    # 搜尋
    search = query.get('search', '')
    if search:
        sql += ' AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)'
        search_pattern = f'%{search}%'
        params.extend([search_pattern, search_pattern, search_pattern])
    
    # 等級篩選
    level = query.get('level', '')
    if level:
        sql += ' AND level = ?'
        params.append(level)
    
    # 來源篩選
    source = query.get('source', '')
    if source:
        sql += ' AND source = ?'
        params.append(source)
    
    # 排序
    sort = query.get('sort', 'created_at')
    order = query.get('order', 'desc')
    allowed_sorts = ['name', 'created_at', 'last_contact', 'total_deals', 'total_amount']
    if sort in allowed_sorts:
        sql += f' ORDER BY {sort} {order.upper()}'
    else:
        sql += ' ORDER BY created_at DESC'
    
    # 分頁
    limit = min(int(query.get('limit', 50)), 100)
    offset = int(query.get('offset', 0))
    sql += ' LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    c.execute(sql, params)
    customers = [dict(row) for row in c.fetchall()]
    
    # 總數
    c.execute('SELECT COUNT(*) FROM customers WHERE status != "deleted"')
    total = c.fetchone()[0]
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'customers': customers,
        'total': total,
        'limit': limit,
        'offset': offset
    })


def get_customer(handler, session, customer_id: int) -> None:
    """取得客戶詳情"""
    db_path = session['data']['db_path']
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('SELECT * FROM customers WHERE id = ? AND status != "deleted"', (customer_id,))
    customer = c.fetchone()
    
    if not customer:
        conn.close()
        return BaseHandler.send_json(handler, {'success': False, 'error': '客戶不存在'}, 404)
    
    customer = dict(customer)
    
    # 取得跟進記錄
    c.execute('''SELECT * FROM followups WHERE customer_id = ? 
                 ORDER BY created_at DESC LIMIT 20''', (customer_id,))
    customer['followups'] = [dict(row) for row in c.fetchall()]
    
    # 取得交易記錄
    c.execute('''SELECT d.*, v.brand, v.model, v.plate
                 FROM deals d
                 LEFT JOIN vehicles v ON d.vehicle_id = v.id
                 WHERE d.customer_id = ?
                 ORDER BY d.deal_date DESC LIMIT 20''', (customer_id,))
    customer['deals'] = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    BaseHandler.send_json(handler, {'success': True, 'customer': customer})


def create_customer(handler, session) -> None:
    """新增客戶"""
    db_path = session['data']['db_path']
    user_id = session['data']['user_id']
    user_name = session['data']['user_name']
    
    data = BaseHandler.get_json_body(handler)
    if not data:
        return BaseHandler.send_json(handler, {'success': False, 'error': '無效的請求資料'}, 400)
    
    name = data.get('name', '').strip()
    if not name:
        return BaseHandler.send_json(handler, {'success': False, 'error': '客戶姓名為必填'}, 400)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 檢查電話是否重複
    phone = data.get('phone', '').strip()
    if phone:
        c.execute('SELECT id FROM customers WHERE phone = ? AND status != "deleted"', (phone,))
        if c.fetchone():
            conn.close()
            return BaseHandler.send_json(handler, {'success': False, 'error': '此電話已存在'}, 400)
    
    c.execute('''INSERT INTO customers 
                 (name, phone, phone2, email, address, source, level, notes, created_by)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (name, phone,
               data.get('phone2', '').strip(),
               data.get('email', '').strip(),
               data.get('address', '').strip(),
               data.get('source', 'other'),
               data.get('level', 'normal'),
               data.get('notes', '').strip(),
               user_id))
    
    customer_id = c.lastrowid
    
    # 記錄活動日誌
    c.execute('''INSERT INTO activity_logs (action, target_type, target_id, user_id, user_name, details)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              ('create', 'customer', customer_id, user_id, user_name, f'新增客戶：{name}'))
    
    conn.commit()
    conn.close()
    
    BaseHandler.send_json(handler, {'success': True, 'id': customer_id})


def update_customer(handler, session, customer_id: int) -> None:
    """更新客戶"""
    db_path = session['data']['db_path']
    user_id = session['data']['user_id']
    user_name = session['data']['user_name']
    
    data = BaseHandler.get_json_body(handler)
    if not data:
        return BaseHandler.send_json(handler, {'success': False, 'error': '無效的請求資料'}, 400)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 檢查客戶是否存在
    c.execute('SELECT name FROM customers WHERE id = ? AND status != "deleted"', (customer_id,))
    existing = c.fetchone()
    if not existing:
        conn.close()
        return BaseHandler.send_json(handler, {'success': False, 'error': '客戶不存在'}, 404)
    
    # 動態更新欄位
    updates = []
    params = []
    
    allowed_fields = ['name', 'phone', 'phone2', 'email', 'address', 
                      'source', 'level', 'notes', 'next_followup']
    
    for field in allowed_fields:
        if field in data:
            updates.append(f'{field} = ?')
            params.append(data[field])
    
    if not updates:
        conn.close()
        return BaseHandler.send_json(handler, {'success': False, 'error': '沒有要更新的欄位'}, 400)
    
    updates.append('updated_at = CURRENT_TIMESTAMP')
    params.append(customer_id)
    
    sql = f'UPDATE customers SET {", ".join(updates)} WHERE id = ?'
    c.execute(sql, params)
    
    # 記錄活動日誌
    c.execute('''INSERT INTO activity_logs (action, target_type, target_id, user_id, user_name, details)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              ('update', 'customer', customer_id, user_id, user_name, f'更新客戶：{existing[0]}'))
    
    conn.commit()
    conn.close()
    
    BaseHandler.send_json(handler, {'success': True})


def delete_customer(handler, session, customer_id: int) -> None:
    """刪除客戶（軟刪除）"""
    db_path = session['data']['db_path']
    user_id = session['data']['user_id']
    user_name = session['data']['user_name']
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('SELECT name FROM customers WHERE id = ? AND status != "deleted"', (customer_id,))
    existing = c.fetchone()
    if not existing:
        conn.close()
        return BaseHandler.send_json(handler, {'success': False, 'error': '客戶不存在'}, 404)
    
    c.execute('UPDATE customers SET status = "deleted", updated_at = CURRENT_TIMESTAMP WHERE id = ?',
              (customer_id,))
    
    c.execute('''INSERT INTO activity_logs (action, target_type, target_id, user_id, user_name, details)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              ('delete', 'customer', customer_id, user_id, user_name, f'刪除客戶：{existing[0]}'))
    
    conn.commit()
    conn.close()
    
    BaseHandler.send_json(handler, {'success': True})


# 📚 知識點
# -----------
# 1. 軟刪除（Soft Delete）：
#    - 不真正刪除，只標記 status = "deleted"
#    - 可以恢復、保留歷史記錄
#    - 查詢時加 WHERE status != "deleted"
#
# 2. 動態 SQL 更新：
#    - 只更新有傳入的欄位
#    - 用 list 組裝 SET 子句
#    - 避免覆蓋其他欄位
#
# 3. 活動日誌：
#    - 記錄「誰」在「何時」做了「什麼」
#    - 用於審計和問題追蹤
