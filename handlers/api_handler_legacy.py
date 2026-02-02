"""
車行寶 CRM v5.0 - API 處理模組
北斗七星文創數位 × 織明
"""
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

import json
import sqlite3
from models import get_connection, log_activity

def handle_get(router, path, query, session):
    """處理 GET API 請求"""
    db_path = session['data']['db_path']
    
    # 客戶列表
    if path == '/api/customers':
        return get_customers(router, db_path, query)
    
    # 車輛列表
    elif path == '/api/vehicles':
        return get_vehicles(router, db_path, query)
    
    # 交易列表
    elif path == '/api/deals':
        return get_deals(router, db_path, query)
    
    # 統計數據
    elif path == '/api/stats':
        return get_stats(router, db_path)
    
    # 跟進提醒
    elif path == '/api/followups':
        return get_followups(router, db_path, query)
    
    # 活動日誌
    elif path == '/api/logs':
        return get_logs(router, db_path, query)
    
    else:
        router.send_json({'error': 'API Not Found'}, 404)

def handle_post(router, path, data, session):
    """處理 POST API 請求"""
    db_path = session['data']['db_path']
    user_id = session['data']['user_id']
    user_name = session['data']['user_name']
    
    # 客戶
    if path == '/api/customers':
        return create_customer(router, db_path, data, user_id, user_name)
    elif path.startswith('/api/customers/') and path.endswith('/update'):
        cid = path.split('/')[3]
        return update_customer(router, db_path, cid, data, user_id, user_name)
    
    # 車輛
    elif path == '/api/vehicles':
        return create_vehicle(router, db_path, data, user_id, user_name)
    elif path.startswith('/api/vehicles/') and path.endswith('/update'):
        vid = path.split('/')[3]
        return update_vehicle(router, db_path, vid, data, user_id, user_name)
    
    # 交易
    elif path == '/api/deals':
        return create_deal(router, db_path, data, user_id, user_name)
    
    # 跟進
    elif path == '/api/followups':
        return create_followup(router, db_path, data, user_id, user_name)
    
    else:
        router.send_json({'error': 'API Not Found'}, 404)

# ===== 客戶 API =====

def get_customers(router, db_path, query):
    """取得客戶列表"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    status = query.get('status', ['active'])[0]
    search = query.get('search', [''])[0]
    level = query.get('level', [''])[0]
    limit = int(query.get('limit', [50])[0])
    offset = int(query.get('offset', [0])[0])
    
    sql = 'SELECT * FROM customers WHERE status = ?'
    params = [status]
    
    if search:
        sql += ' AND (name LIKE ? OR phone LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    if level:
        sql += ' AND level = ?'
        params.append(level)
    
    sql += ' ORDER BY updated_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    c.execute(sql, params)
    customers = [dict(row) for row in c.fetchall()]
    
    # 取得總數
    c.execute('SELECT COUNT(*) FROM customers WHERE status = ?', (status,))
    total = c.fetchone()[0]
    
    conn.close()
    
    router.send_json({
        'success': True,
        'customers': customers,
        'total': total
    })

def create_customer(router, db_path, data, user_id, user_name):
    """建立客戶"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''INSERT INTO customers (name, phone, phone2, email, address, source, level, tags, notes, assigned_to)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data.get('name'), data.get('phone'), data.get('phone2'), 
               data.get('email'), data.get('address'), data.get('source', 'walk_in'),
               data.get('level', 'normal'), json.dumps(data.get('tags', [])),
               data.get('notes'), data.get('assigned_to')))
    
    customer_id = c.lastrowid
    conn.commit()
    conn.close()
    
    log_activity(db_path, user_id, user_name, 'create', 'customer', customer_id, data.get('name'))
    
    router.send_json({'success': True, 'id': customer_id})

def update_customer(router, db_path, customer_id, data, user_id, user_name):
    """更新客戶"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    fields = []
    values = []
    
    for key in ['name', 'phone', 'phone2', 'email', 'address', 'source', 'level', 'notes', 'next_followup']:
        if key in data:
            fields.append(f'{key} = ?')
            values.append(data[key])
    
    if 'tags' in data:
        fields.append('tags = ?')
        values.append(json.dumps(data['tags']))
    
    fields.append('updated_at = CURRENT_TIMESTAMP')
    values.append(customer_id)
    
    c.execute(f'UPDATE customers SET {", ".join(fields)} WHERE id = ?', values)
    conn.commit()
    conn.close()
    
    log_activity(db_path, user_id, user_name, 'update', 'customer', customer_id, data.get('name', ''))
    
    router.send_json({'success': True})

# ===== 車輛 API =====

def get_vehicles(router, db_path, query):
    """取得車輛列表"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    status = query.get('status', [''])[0]
    search = query.get('search', [''])[0]
    brand = query.get('brand', [''])[0]
    limit = int(query.get('limit', [50])[0])
    offset = int(query.get('offset', [0])[0])
    
    sql = 'SELECT * FROM vehicles WHERE 1=1'
    params = []
    
    if status:
        sql += ' AND status = ?'
        params.append(status)
    
    if search:
        sql += ' AND (brand LIKE ? OR model LIKE ? OR plate LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
    
    if brand:
        sql += ' AND brand = ?'
        params.append(brand)
    
    sql += ' ORDER BY updated_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    c.execute(sql, params)
    vehicles = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    router.send_json({
        'success': True,
        'vehicles': vehicles
    })

def create_vehicle(router, db_path, data, user_id, user_name):
    """建立車輛"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 計算總成本
    purchase_price = int(data.get('purchase_price', 0))
    repair_cost = int(data.get('repair_cost', 0))
    total_cost = purchase_price + repair_cost
    
    c.execute('''INSERT INTO vehicles 
                 (plate, brand, model, year, color, mileage, engine_cc, fuel_type, transmission,
                  purchase_date, purchase_price, purchase_from, repair_cost, total_cost,
                  asking_price, min_price, features, condition_notes, location, status, created_by)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data.get('plate'), data.get('brand'), data.get('model'),
               data.get('year'), data.get('color'), data.get('mileage', 0),
               data.get('engine_cc'), data.get('fuel_type'), data.get('transmission'),
               data.get('purchase_date'), purchase_price, data.get('purchase_from'),
               repair_cost, total_cost, data.get('asking_price', 0), data.get('min_price', 0),
               json.dumps(data.get('features', [])), data.get('condition_notes'),
               data.get('location'), data.get('status', 'in_stock'), user_id))
    
    vehicle_id = c.lastrowid
    conn.commit()
    conn.close()
    
    log_activity(db_path, user_id, user_name, 'create', 'vehicle', vehicle_id, 
                 f"{data.get('brand')} {data.get('model')}")
    
    router.send_json({'success': True, 'id': vehicle_id})

def update_vehicle(router, db_path, vehicle_id, data, user_id, user_name):
    """更新車輛"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    fields = []
    values = []
    
    updatable = ['plate', 'brand', 'model', 'year', 'color', 'mileage', 'engine_cc',
                 'fuel_type', 'transmission', 'purchase_price', 'repair_cost',
                 'asking_price', 'min_price', 'condition_notes', 'location', 'status']
    
    for key in updatable:
        if key in data:
            fields.append(f'{key} = ?')
            values.append(data[key])
    
    # 重新計算總成本
    if 'purchase_price' in data or 'repair_cost' in data:
        c.execute('SELECT purchase_price, repair_cost FROM vehicles WHERE id = ?', (vehicle_id,))
        current = c.fetchone()
        pp = int(data.get('purchase_price', current['purchase_price']))
        rc = int(data.get('repair_cost', current['repair_cost']))
        fields.append('total_cost = ?')
        values.append(pp + rc)
    
    fields.append('updated_at = CURRENT_TIMESTAMP')
    values.append(vehicle_id)
    
    c.execute(f'UPDATE vehicles SET {", ".join(fields)} WHERE id = ?', values)
    conn.commit()
    conn.close()
    
    log_activity(db_path, user_id, user_name, 'update', 'vehicle', vehicle_id, '')
    
    router.send_json({'success': True})

# ===== 交易 API =====

def get_deals(router, db_path, query):
    """取得交易列表"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''SELECT d.*, c.name as customer_name, v.brand, v.model
                 FROM deals d
                 LEFT JOIN customers c ON d.customer_id = c.id
                 LEFT JOIN vehicles v ON d.vehicle_id = v.id
                 ORDER BY d.deal_date DESC, d.created_at DESC
                 LIMIT 100''')
    
    deals = [dict(row) for row in c.fetchall()]
    conn.close()
    
    router.send_json({
        'success': True,
        'deals': deals
    })

def create_deal(router, db_path, data, user_id, user_name):
    """建立交易"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    amount = int(data.get('amount', 0))
    cost = int(data.get('cost', 0))
    profit = amount - cost
    
    c.execute('''INSERT INTO deals 
                 (deal_type, customer_id, vehicle_id, amount, cost, profit,
                  payment_method, payment_status, deal_date, notes, created_by)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data.get('deal_type'), data.get('customer_id'), data.get('vehicle_id'),
               amount, cost, profit, data.get('payment_method'),
               data.get('payment_status', 'completed'), data.get('deal_date'),
               data.get('notes'), user_id))
    
    deal_id = c.lastrowid
    
    # 更新車輛狀態
    if data.get('vehicle_id') and data.get('deal_type') == 'sell':
        c.execute('''UPDATE vehicles SET status = 'sold', sold_date = ?, sold_price = ?, sold_to = ?
                     WHERE id = ?''',
                  (data.get('deal_date'), amount, data.get('customer_id'), data.get('vehicle_id')))
    
    # 更新客戶統計
    if data.get('customer_id'):
        c.execute('''UPDATE customers SET total_deals = total_deals + 1, 
                     total_amount = total_amount + ?, updated_at = CURRENT_TIMESTAMP
                     WHERE id = ?''',
                  (amount, data.get('customer_id')))
    
    conn.commit()
    conn.close()
    
    log_activity(db_path, user_id, user_name, 'create', 'deal', deal_id, 
                 f"{data.get('deal_type')} ${amount:,}")
    
    router.send_json({'success': True, 'id': deal_id})

# ===== 統計 API =====

def get_stats(router, db_path):
    """取得統計數據"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 客戶統計
    c.execute('SELECT COUNT(*) FROM customers WHERE status = "active"')
    customer_count = c.fetchone()[0]
    
    # 車輛統計
    c.execute('SELECT status, COUNT(*) FROM vehicles GROUP BY status')
    vehicle_stats = {row[0]: row[1] for row in c.fetchall()}
    
    # 本月交易
    c.execute('''SELECT deal_type, COUNT(*), SUM(amount), SUM(profit)
                 FROM deals 
                 WHERE deal_date >= date('now', 'start of month')
                 GROUP BY deal_type''')
    deal_stats = {}
    for row in c.fetchall():
        deal_stats[row[0]] = {
            'count': row[1],
            'amount': row[2] or 0,
            'profit': row[3] or 0
        }
    
    # 待跟進
    c.execute('''SELECT COUNT(*) FROM customers 
                 WHERE next_followup <= date('now') AND status = "active"''')
    pending_followups = c.fetchone()[0]
    
    conn.close()
    
    router.send_json({
        'success': True,
        'stats': {
            'customers': customer_count,
            'vehicles': vehicle_stats,
            'deals': deal_stats,
            'pending_followups': pending_followups
        }
    })

# ===== 跟進 API =====

def get_followups(router, db_path, query):
    """取得跟進記錄"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    customer_id = query.get('customer_id', [''])[0]
    
    if customer_id:
        c.execute('''SELECT f.*, u.name as user_name
                     FROM followups f
                     LEFT JOIN users u ON f.user_id = u.id
                     WHERE f.customer_id = ?
                     ORDER BY f.created_at DESC''', (customer_id,))
    else:
        c.execute('''SELECT f.*, c.name as customer_name, u.name as user_name
                     FROM followups f
                     LEFT JOIN customers c ON f.customer_id = c.id
                     LEFT JOIN users u ON f.user_id = u.id
                     WHERE f.next_date <= date('now', '+7 days')
                     ORDER BY f.next_date ASC
                     LIMIT 50''')
    
    followups = [dict(row) for row in c.fetchall()]
    conn.close()
    
    router.send_json({
        'success': True,
        'followups': followups
    })

def create_followup(router, db_path, data, user_id, user_name):
    """建立跟進記錄"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''INSERT INTO followups 
                 (customer_id, vehicle_id, user_id, type, content, result, next_action, next_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (data.get('customer_id'), data.get('vehicle_id'), user_id,
               data.get('type', 'call'), data.get('content'), data.get('result'),
               data.get('next_action'), data.get('next_date')))
    
    followup_id = c.lastrowid
    
    # 更新客戶最後聯繫時間和下次跟進
    c.execute('''UPDATE customers SET last_contact = CURRENT_TIMESTAMP, 
                 next_followup = ?, updated_at = CURRENT_TIMESTAMP
                 WHERE id = ?''',
              (data.get('next_date'), data.get('customer_id')))
    
    conn.commit()
    conn.close()
    
    router.send_json({'success': True, 'id': followup_id})

# ===== 日誌 API =====

def get_logs(router, db_path, query):
    """取得活動日誌"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    limit = int(query.get('limit', [50])[0])
    
    c.execute('''SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT ?''', (limit,))
    logs = [dict(row) for row in c.fetchall()]
    conn.close()
    
    router.send_json({
        'success': True,
        'logs': logs
    })
