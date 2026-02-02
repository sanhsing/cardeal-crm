"""
車行寶 CRM v5.1 - 車輛處理器
PYLIB: L3-cardeal-vehicle-handler
Version: 1.0.0
Created: 2026-02-02

功能：車輛 CRUD API 處理
"""
import json
from typing import Dict, List, Optional

# ============================================================
# L0: 基礎常量
# ============================================================

VEHICLE_STATUS = {
    'in_stock': {'name': '在庫', 'color': '#10b981', 'icon': '🟢'},
    'reserved': {'name': '已預訂', 'color': '#f59e0b', 'icon': '🟡'},
    'sold': {'name': '已售出', 'color': '#6b7280', 'icon': '⚫'},
    'maintenance': {'name': '整備中', 'color': '#3b82f6', 'icon': '🔵'},
}

FUEL_TYPES = ['汽油', '柴油', '油電混合', '純電動', 'LPG']
TRANSMISSIONS = ['手排', '自排', 'CVT', '雙離合']

COMMON_BRANDS = [
    'Toyota', 'Honda', 'Nissan', 'Mazda', 'Mitsubishi',
    'Ford', 'Volkswagen', 'BMW', 'Mercedes-Benz', 'Lexus',
    'Hyundai', 'Kia', 'Subaru', 'Suzuki', 'Luxgen'
]

# ============================================================
# L1: 資料結構
# ============================================================

from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class VehicleDTO:
    """車輛資料傳輸物件"""
    brand: str
    model: str
    plate: str = ""
    year: int = 0
    color: str = ""
    mileage: int = 0
    engine_cc: int = 0
    fuel_type: str = ""
    transmission: str = ""
    purchase_price: int = 0
    repair_cost: int = 0
    asking_price: int = 0
    min_price: int = 0
    status: str = "in_stock"
    features: List[str] = field(default_factory=list)
    condition_notes: str = ""
    
    @property
    def total_cost(self) -> int:
        """計算總成本"""
        return self.purchase_price + self.repair_cost
    
    @property
    def potential_profit(self) -> int:
        """計算預期利潤"""
        return self.asking_price - self.total_cost

# ============================================================
# L2: 核心邏輯 - 查詢
# ============================================================

from .base import BaseHandler
from models import get_connection, log_activity

def get_vehicles(handler, db_path: str, query: Dict) -> None:
    """
    取得車輛列表
    
    Args:
        handler: HTTP handler
        db_path: 租戶資料庫路徑
        query: 查詢參數 {status, search, brand, limit, offset}
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 解析參數
    status = query.get('status', [''])[0]
    search = query.get('search', [''])[0]
    brand = query.get('brand', [''])[0]
    limit = int(query.get('limit', [50])[0])
    offset = int(query.get('offset', [0])[0])
    
    # 建構 SQL
    sql = 'SELECT * FROM vehicles WHERE 1=1'
    params = []
    
    if status:
        sql += ' AND status = ?'
        params.append(status)
    
    if search:
        sql += ' AND (brand LIKE ? OR model LIKE ? OR plate LIKE ?)'
        params.extend([f'%{search}%'] * 3)
    
    if brand:
        sql += ' AND brand = ?'
        params.append(brand)
    
    sql += ' ORDER BY updated_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    # 執行查詢
    c.execute(sql, params)
    vehicles = [dict(row) for row in c.fetchall()]
    
    # 計算欄位
    for v in vehicles:
        v['total_cost'] = (v.get('purchase_price') or 0) + (v.get('repair_cost') or 0)
        v['potential_profit'] = (v.get('asking_price') or 0) - v['total_cost']
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'vehicles': vehicles
    })


def get_vehicle_by_id(handler, db_path: str, vehicle_id: int) -> None:
    """取得單一車輛詳情"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('SELECT * FROM vehicles WHERE id = ?', (vehicle_id,))
    vehicle = c.fetchone()
    
    if not vehicle:
        conn.close()
        return BaseHandler.send_json(handler, {
            'success': False,
            'error': '車輛不存在'
        }, 404)
    
    result = dict(vehicle)
    
    # 計算欄位
    result['total_cost'] = (result.get('purchase_price') or 0) + (result.get('repair_cost') or 0)
    result['potential_profit'] = (result.get('asking_price') or 0) - result['total_cost']
    
    # 取得交易記錄
    c.execute('''
        SELECT d.*, c.name as customer_name
        FROM deals d
        LEFT JOIN customers c ON d.customer_id = c.id
        WHERE d.vehicle_id = ?
        ORDER BY d.deal_date DESC
    ''', (vehicle_id,))
    result['deals'] = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'vehicle': result
    })


def get_brands(handler, db_path: str) -> None:
    """取得品牌列表（從現有資料）"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT brand, COUNT(*) as count 
        FROM vehicles 
        WHERE brand IS NOT NULL AND brand != ''
        GROUP BY brand 
        ORDER BY count DESC
    ''')
    
    brands = [{'name': row[0], 'count': row[1]} for row in c.fetchall()]
    conn.close()
    
    # 合併常用品牌
    existing = {b['name'] for b in brands}
    for common in COMMON_BRANDS:
        if common not in existing:
            brands.append({'name': common, 'count': 0})
    
    BaseHandler.send_json(handler, {
        'success': True,
        'brands': brands
    })

# ============================================================
# L3: 業務處理 - 增刪改
# ============================================================

def create_vehicle(handler, db_path: str, data: Dict, user_id: int, user_name: str) -> None:
    """建立車輛"""
    # 驗證必填
    if not data.get('brand') or not data.get('model'):
        return BaseHandler.send_json(handler, {
            'success': False,
            'error': '請填寫品牌和型號'
        })
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 計算總成本
    purchase_price = int(data.get('purchase_price') or 0)
    repair_cost = int(data.get('repair_cost') or 0)
    total_cost = purchase_price + repair_cost
    
    # 插入資料
    c.execute('''
        INSERT INTO vehicles 
        (plate, brand, model, year, color, mileage, engine_cc, fuel_type, transmission,
         purchase_date, purchase_price, purchase_from, repair_cost, total_cost,
         asking_price, min_price, features, condition_notes, location, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('plate', ''),
        data.get('brand'),
        data.get('model'),
        data.get('year'),
        data.get('color', ''),
        data.get('mileage', 0),
        data.get('engine_cc'),
        data.get('fuel_type', ''),
        data.get('transmission', ''),
        data.get('purchase_date'),
        purchase_price,
        data.get('purchase_from', ''),
        repair_cost,
        total_cost,
        data.get('asking_price', 0),
        data.get('min_price', 0),
        json.dumps(data.get('features', [])),
        data.get('condition_notes', ''),
        data.get('location', ''),
        data.get('status', 'in_stock'),
        user_id
    ))
    
    vehicle_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # 記錄活動
    vehicle_name = f"{data.get('brand')} {data.get('model')}"
    log_activity(db_path, user_id, user_name, 'create', 'vehicle', vehicle_id, vehicle_name)
    
    BaseHandler.send_json(handler, {
        'success': True,
        'id': vehicle_id,
        'message': '車輛建立成功'
    })


def update_vehicle(handler, db_path: str, vehicle_id: int, data: Dict, user_id: int, user_name: str) -> None:
    """更新車輛"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 檢查車輛是否存在
    c.execute('SELECT brand, model, purchase_price, repair_cost FROM vehicles WHERE id = ?', (vehicle_id,))
    current = c.fetchone()
    
    if not current:
        conn.close()
        return BaseHandler.send_json(handler, {
            'success': False,
            'error': '車輛不存在'
        }, 404)
    
    # 建構更新語句
    fields = []
    values = []
    
    updatable = [
        'plate', 'brand', 'model', 'year', 'color', 'mileage', 
        'engine_cc', 'fuel_type', 'transmission', 'purchase_date',
        'purchase_price', 'purchase_from', 'repair_cost',
        'asking_price', 'min_price', 'condition_notes', 'location', 'status'
    ]
    
    for key in updatable:
        if key in data:
            fields.append(f'{key} = ?')
            values.append(data[key])
    
    if 'features' in data:
        fields.append('features = ?')
        values.append(json.dumps(data['features']))
    
    # 重新計算總成本
    pp = int(data.get('purchase_price', current['purchase_price']) or 0)
    rc = int(data.get('repair_cost', current['repair_cost']) or 0)
    fields.append('total_cost = ?')
    values.append(pp + rc)
    
    fields.append('updated_at = CURRENT_TIMESTAMP')
    values.append(vehicle_id)
    
    c.execute(f'UPDATE vehicles SET {", ".join(fields)} WHERE id = ?', values)
    conn.commit()
    conn.close()
    
    # 記錄活動
    vehicle_name = f"{data.get('brand', current['brand'])} {data.get('model', current['model'])}"
    log_activity(db_path, user_id, user_name, 'update', 'vehicle', vehicle_id, vehicle_name)
    
    BaseHandler.send_json(handler, {
        'success': True,
        'message': '車輛更新成功'
    })


def sell_vehicle(handler, db_path: str, vehicle_id: int, data: Dict, user_id: int, user_name: str) -> None:
    """售出車輛（快速操作）"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 檢查車輛
    c.execute('SELECT brand, model, total_cost, status FROM vehicles WHERE id = ?', (vehicle_id,))
    vehicle = c.fetchone()
    
    if not vehicle:
        conn.close()
        return BaseHandler.send_json(handler, {
            'success': False,
            'error': '車輛不存在'
        }, 404)
    
    if vehicle['status'] == 'sold':
        conn.close()
        return BaseHandler.send_json(handler, {
            'success': False,
            'error': '車輛已售出'
        })
    
    # 更新車輛狀態
    sold_price = int(data.get('price', 0))
    sold_date = data.get('date') or datetime.now().strftime('%Y-%m-%d')
    customer_id = data.get('customer_id')
    
    c.execute('''
        UPDATE vehicles 
        SET status = 'sold', sold_date = ?, sold_price = ?, sold_to = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (sold_date, sold_price, customer_id, vehicle_id))
    
    # 建立交易記錄
    profit = sold_price - (vehicle['total_cost'] or 0)
    
    c.execute('''
        INSERT INTO deals 
        (deal_type, customer_id, vehicle_id, amount, cost, profit, deal_date, created_by)
        VALUES ('sell', ?, ?, ?, ?, ?, ?, ?)
    ''', (customer_id, vehicle_id, sold_price, vehicle['total_cost'], profit, sold_date, user_id))
    
    conn.commit()
    conn.close()
    
    # 記錄活動
    vehicle_name = f"{vehicle['brand']} {vehicle['model']}"
    log_activity(db_path, user_id, user_name, 'sell', 'vehicle', vehicle_id, 
                 f"{vehicle_name} 售出 ${sold_price:,}")
    
    BaseHandler.send_json(handler, {
        'success': True,
        'profit': profit,
        'message': f'車輛售出成功，利潤 ${profit:,}'
    })

# ============================================================
# L4: 統計 & 報表
# ============================================================

def get_vehicle_stats(handler, db_path: str) -> None:
    """取得車輛統計"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    stats = {}
    
    # 按狀態統計
    c.execute('SELECT status, COUNT(*) FROM vehicles GROUP BY status')
    stats['by_status'] = {row[0]: row[1] for row in c.fetchall()}
    
    # 在庫總成本
    c.execute('SELECT SUM(total_cost) FROM vehicles WHERE status = "in_stock"')
    stats['total_cost'] = c.fetchone()[0] or 0
    
    # 在庫總預期售價
    c.execute('SELECT SUM(asking_price) FROM vehicles WHERE status = "in_stock"')
    stats['total_asking'] = c.fetchone()[0] or 0
    
    # 預期利潤
    stats['expected_profit'] = stats['total_asking'] - stats['total_cost']
    
    # 按品牌統計
    c.execute('''
        SELECT brand, COUNT(*), SUM(total_cost)
        FROM vehicles 
        WHERE status = "in_stock"
        GROUP BY brand
        ORDER BY COUNT(*) DESC
        LIMIT 10
    ''')
    stats['by_brand'] = [
        {'brand': row[0], 'count': row[1], 'cost': row[2] or 0}
        for row in c.fetchall()
    ]
    
    # 庫存天數分佈
    c.execute('''
        SELECT 
            CASE 
                WHEN julianday('now') - julianday(created_at) <= 30 THEN '0-30天'
                WHEN julianday('now') - julianday(created_at) <= 60 THEN '31-60天'
                WHEN julianday('now') - julianday(created_at) <= 90 THEN '61-90天'
                ELSE '90天以上'
            END as age_group,
            COUNT(*)
        FROM vehicles
        WHERE status = "in_stock"
        GROUP BY age_group
    ''')
    stats['by_age'] = {row[0]: row[1] for row in c.fetchall()}
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'stats': stats
    })


def get_inventory_report(handler, db_path: str, query: Dict) -> None:
    """取得庫存報表"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            id, plate, brand, model, year, color,
            purchase_date, purchase_price, repair_cost, total_cost,
            asking_price, min_price,
            (asking_price - total_cost) as potential_profit,
            julianday('now') - julianday(created_at) as days_in_stock,
            status
        FROM vehicles
        WHERE status = "in_stock"
        ORDER BY created_at ASC
    ''')
    
    vehicles = [dict(row) for row in c.fetchall()]
    
    # 計算匯總
    summary = {
        'count': len(vehicles),
        'total_cost': sum(v['total_cost'] or 0 for v in vehicles),
        'total_asking': sum(v['asking_price'] or 0 for v in vehicles),
        'total_profit': sum(v['potential_profit'] or 0 for v in vehicles),
        'avg_days': sum(v['days_in_stock'] or 0 for v in vehicles) / len(vehicles) if vehicles else 0
    }
    
    conn.close()
    
    BaseHandler.send_json(handler, {
        'success': True,
        'vehicles': vehicles,
        'summary': summary
    })


def delete_vehicle(handler, db_path: str, vehicle_id: int, user_id: int, user_name: str) -> None:
    """刪除車輛（軟刪除）"""
    from .base import BaseHandler
    from models import get_connection
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 檢查車輛是否存在
    c.execute('SELECT brand, model, status FROM vehicles WHERE id = ?', (vehicle_id,))
    vehicle = c.fetchone()
    
    if not vehicle:
        conn.close()
        return BaseHandler.send_json(handler, {'success': False, 'error': '車輛不存在'}, 404)
    
    # 檢查是否已售出
    if vehicle['status'] == 'sold':
        conn.close()
        return BaseHandler.send_json(handler, {'success': False, 'error': '已售出車輛無法刪除'}, 400)
    
    # 軟刪除
    c.execute('UPDATE vehicles SET status = "deleted", updated_at = CURRENT_TIMESTAMP WHERE id = ?',
              (vehicle_id,))
    
    # 記錄日誌
    c.execute('''INSERT INTO activity_logs (action, target_type, target_id, user_id, user_name, details)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              ('delete', 'vehicle', vehicle_id, user_id, user_name, 
               f'刪除車輛：{vehicle["brand"]} {vehicle["model"]}'))
    
    conn.commit()
    conn.close()
    
    BaseHandler.send_json(handler, {'success': True})


# 📚 知識點
# -----------
# 1. @property：把方法變成屬性存取
#    - 定義：@property def total_cost(self) -> Any: return ...
#    - 使用：vehicle.total_cost（不是 vehicle.total_cost()）
#    - 好處：計算欄位不佔儲存空間，存取時才計算
#
# 2. julianday()：SQLite 的日期函數
#    - 返回儒略日數（從公元前4713年1月1日算起的天數）
#    - julianday('now') - julianday(date) = 相差天數
#
# 3. CASE WHEN：SQL 的條件判斷
#    - 類似 if-elif-else
#    - 用於分組統計
#
# 4. f-string 格式化：
#    - f"${profit:,}" → "$1,234,567"
#    - :, 是千位分隔符
