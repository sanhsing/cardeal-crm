"""
車行寶 CRM v5.1 - 批量操作處理器
北斗七星文創數位 × 織明

功能：批量刪除、批量更新、批量匯入
"""
from typing import List, Dict
from .base import BaseHandler
from models import get_connection


def batch_delete_customers(handler, session) -> None:
    """批量刪除客戶（軟刪除）"""
    db_path = BaseHandler.get_db_path(session)
    data = BaseHandler.get_json_body(handler)
    
    if not data or 'ids' not in data:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '缺少 ids 參數'}, 400)
    
    ids = data['ids']
    if not isinstance(ids, list) or len(ids) == 0:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': 'ids 必須是非空陣列'}, 400)
    
    # 限制單次最多 100 筆
    if len(ids) > 100:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '單次最多刪除 100 筆'}, 400)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 軟刪除
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f'''UPDATE customers 
                  SET status = 'deleted', updated_at = datetime('now')
                  WHERE id IN ({placeholders}) AND status = 'active' ''',
              ids)
    
    affected = c.rowcount
    conn.commit()
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'deleted': affected,
        'message': f'已刪除 {affected} 筆客戶'
    })


def batch_update_customer_level(handler, session) -> None:
    """批量更新客戶等級"""
    db_path = BaseHandler.get_db_path(session)
    data = BaseHandler.get_json_body(handler)
    
    if not data or 'ids' not in data or 'level' not in data:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '缺少 ids 或 level 參數'}, 400)
    
    ids = data['ids']
    level = data['level']
    
    # 驗證等級
    valid_levels = ['vip', 'normal', 'potential', 'cold']
    if level not in valid_levels:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': f'等級必須是 {valid_levels} 之一'}, 400)
    
    if len(ids) > 100:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '單次最多更新 100 筆'}, 400)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f'''UPDATE customers 
                  SET level = ?, updated_at = datetime('now')
                  WHERE id IN ({placeholders}) AND status = 'active' ''',
              [level] + ids)
    
    affected = c.rowcount
    conn.commit()
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'updated': affected,
        'message': f'已更新 {affected} 筆客戶等級為 {level}'
    })


def batch_delete_vehicles(handler, session) -> None:
    """批量刪除車輛（軟刪除）"""
    db_path = BaseHandler.get_db_path(session)
    data = BaseHandler.get_json_body(handler)
    
    if not data or 'ids' not in data:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '缺少 ids 參數'}, 400)
    
    ids = data['ids']
    
    if len(ids) > 100:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '單次最多刪除 100 筆'}, 400)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 只能刪除在庫車輛
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f'''UPDATE vehicles 
                  SET status = 'deleted', updated_at = datetime('now')
                  WHERE id IN ({placeholders}) AND status = 'in_stock' ''',
              ids)
    
    affected = c.rowcount
    conn.commit()
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'deleted': affected,
        'message': f'已刪除 {affected} 台車輛'
    })


def batch_update_vehicle_status(handler, session) -> None:
    """批量更新車輛狀態"""
    db_path = BaseHandler.get_db_path(session)
    data = BaseHandler.get_json_body(handler)
    
    if not data or 'ids' not in data or 'status' not in data:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '缺少 ids 或 status 參數'}, 400)
    
    ids = data['ids']
    status = data['status']
    
    # 驗證狀態
    valid_status = ['in_stock', 'reserved', 'maintenance']
    if status not in valid_status:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': f'狀態必須是 {valid_status} 之一'}, 400)
    
    if len(ids) > 100:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '單次最多更新 100 筆'}, 400)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    placeholders = ','.join(['?' for _ in ids])
    c.execute(f'''UPDATE vehicles 
                  SET status = ?, updated_at = datetime('now')
                  WHERE id IN ({placeholders}) ''',
              [status] + ids)
    
    affected = c.rowcount
    conn.commit()
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'updated': affected,
        'message': f'已更新 {affected} 台車輛狀態為 {status}'
    })


def batch_update_vehicle_price(handler, session) -> None:
    """批量調整車輛價格"""
    db_path = BaseHandler.get_db_path(session)
    data = BaseHandler.get_json_body(handler)
    
    if not data or 'ids' not in data:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '缺少 ids 參數'}, 400)
    
    ids = data['ids']
    adjust_type = data.get('type', 'percent')  # percent 或 fixed
    adjust_value = data.get('value', 0)
    
    if len(ids) > 100:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '單次最多更新 100 筆'}, 400)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    placeholders = ','.join(['?' for _ in ids])
    
    if adjust_type == 'percent':
        # 百分比調整：例如 -5 表示降價 5%
        factor = 1 + (adjust_value / 100)
        c.execute(f'''UPDATE vehicles 
                      SET asking_price = CAST(asking_price * ? AS INTEGER),
                          updated_at = datetime('now')
                      WHERE id IN ({placeholders}) AND status = 'in_stock' ''',
                  [factor] + ids)
    else:
        # 固定金額調整
        c.execute(f'''UPDATE vehicles 
                      SET asking_price = asking_price + ?,
                          updated_at = datetime('now')
                      WHERE id IN ({placeholders}) AND status = 'in_stock' ''',
                  [adjust_value] + ids)
    
    affected = c.rowcount
    conn.commit()
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'updated': affected,
        'message': f'已調整 {affected} 台車輛價格'
    })


def batch_create_followups(handler, session) -> None:
    """批量建立跟進"""
    db_path = BaseHandler.get_db_path(session)
    user_id = session['data']['user_id']
    data = BaseHandler.get_json_body(handler)
    
    if not data or 'customer_ids' not in data:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '缺少 customer_ids 參數'}, 400)
    
    customer_ids = data['customer_ids']
    followup_type = data.get('type', 'call')
    content = data.get('content', '')
    next_date = data.get('next_date')
    
    if not next_date:
        from datetime import datetime, timedelta
        next_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    if len(customer_ids) > 100:
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '單次最多建立 100 筆'}, 400)
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    created = 0
    for customer_id in customer_ids:
        try:
            c.execute('''INSERT INTO followups 
                         (customer_id, user_id, type, content, next_date)
                         VALUES (?, ?, ?, ?, ?)''',
                      (customer_id, user_id, followup_type, content or '定期跟進', next_date))
            created += 1
        except:
            continue
    
    conn.commit()
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'created': created,
        'message': f'已建立 {created} 筆跟進'
    })


# 📚 知識點
# -----------
# 1. 批量操作設計：
#    - 限制單次數量（防止超時）
#    - 使用 IN 子句批量處理
#    - 返回實際影響的筆數
#
# 2. SQL 動態 placeholder：
#    - ','.join(['?' for _ in ids])
#    - 產生 "?,?,?" 形式
#    - 防止 SQL Injection
#
# 3. 軟刪除 vs 硬刪除：
#    - 軟刪除：status = 'deleted'
#    - 保留資料，可恢復
#    - 關聯資料不會斷
#
# 4. 價格調整策略：
#    - 百分比：乘以係數
#    - 固定金額：加減
#    - CAST AS INTEGER 轉整數
#
# 5. 錯誤處理：
#    - 循環中 try-except
#    - 部分成功仍繼續
#    - 返回實際成功數
