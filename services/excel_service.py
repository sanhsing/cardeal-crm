"""
車行寶 CRM v5.1 - Excel 服務模組
北斗七星文創數位 × 織明

功能：匯入/匯出 Excel 檔案
"""
import csv
import io
import json
from datetime import datetime
from models import get_connection

# ===== 匯出功能 =====

def export_customers(db_path, format='csv'):
    """匯出客戶資料"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''SELECT id, name, phone, phone2, email, address, 
                        source, level, notes, total_deals, total_amount,
                        created_at, last_contact
                 FROM customers 
                 WHERE status = "active"
                 ORDER BY created_at DESC''')
    
    rows = c.fetchall()
    conn.close()
    
    # 欄位標題
    headers = ['編號', '姓名', '電話', '電話2', 'Email', '地址',
               '來源', '等級', '備註', '交易次數', '交易總額',
               '建立時間', '最後聯繫']
    
    return _generate_csv(headers, rows)


def export_vehicles(db_path, status=None):
    """匯出車輛資料"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    sql = '''SELECT id, plate, brand, model, year, color, mileage,
                    purchase_date, purchase_price, repair_cost, total_cost,
                    asking_price, min_price, status, created_at
             FROM vehicles'''
    params = []
    
    if status:
        sql += ' WHERE status = ?'
        params.append(status)
    
    sql += ' ORDER BY created_at DESC'
    
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    
    headers = ['編號', '車牌', '品牌', '型號', '年份', '顏色', '里程',
               '購入日期', '購入價', '整備費', '總成本',
               '定價', '底價', '狀態', '建立時間']
    
    return _generate_csv(headers, rows)


def export_deals(db_path, start_date=None, end_date=None):
    """匯出交易記錄"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    sql = '''SELECT d.id, d.deal_type, d.deal_date, 
                    c.name as customer_name, c.phone as customer_phone,
                    v.brand, v.model, v.plate,
                    d.amount, d.cost, d.profit, d.payment_method, d.notes
             FROM deals d
             LEFT JOIN customers c ON d.customer_id = c.id
             LEFT JOIN vehicles v ON d.vehicle_id = v.id
             WHERE d.status = "completed"'''
    params = []
    
    if start_date:
        sql += ' AND d.deal_date >= ?'
        params.append(start_date)
    if end_date:
        sql += ' AND d.deal_date <= ?'
        params.append(end_date)
    
    sql += ' ORDER BY d.deal_date DESC'
    
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    
    headers = ['編號', '類型', '日期', '客戶', '客戶電話',
               '品牌', '型號', '車牌', '金額', '成本', '利潤',
               '付款方式', '備註']
    
    return _generate_csv(headers, rows)


def _generate_csv(headers, rows):
    """產生 CSV 內容"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 寫入 BOM（讓 Excel 正確識別 UTF-8）
    output.write('\ufeff')
    
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_format_cell(cell) for cell in row])
    
    return output.getvalue()


def _format_cell(value):
    """格式化儲存格"""
    if value is None:
        return ''
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


# ===== 匯入功能 =====

def import_customers(db_path, csv_content, user_id=None):
    """匯入客戶資料"""
    reader = csv.DictReader(io.StringIO(csv_content))
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    success = 0
    errors = []
    
    for i, row in enumerate(reader, start=2):  # 從第2行開始（第1行是標題）
        try:
            name = row.get('姓名', '').strip()
            if not name:
                errors.append(f'第 {i} 行：姓名不能為空')
                continue
            
            phone = row.get('電話', '').strip()
            
            # 檢查是否已存在
            if phone:
                c.execute('SELECT id FROM customers WHERE phone = ?', (phone,))
                if c.fetchone():
                    errors.append(f'第 {i} 行：電話 {phone} 已存在')
                    continue
            
            c.execute('''INSERT INTO customers (name, phone, phone2, email, address, source, level, notes)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (name,
                       phone,
                       row.get('電話2', '').strip(),
                       row.get('Email', '').strip(),
                       row.get('地址', '').strip(),
                       _map_source(row.get('來源', '')),
                       _map_level(row.get('等級', '')),
                       row.get('備註', '').strip()))
            success += 1
            
        except Exception as e:
            errors.append(f'第 {i} 行：{str(e)}')
    
    conn.commit()
    conn.close()
    
    return {
        'success': True,
        'imported': success,
        'errors': errors
    }


def import_vehicles(db_path, csv_content, user_id=None):
    """匯入車輛資料"""
    reader = csv.DictReader(io.StringIO(csv_content))
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    success = 0
    errors = []
    
    for i, row in enumerate(reader, start=2):
        try:
            brand = row.get('品牌', '').strip()
            model = row.get('型號', '').strip()
            
            if not brand or not model:
                errors.append(f'第 {i} 行：品牌和型號不能為空')
                continue
            
            purchase_price = _parse_number(row.get('購入價', 0))
            repair_cost = _parse_number(row.get('整備費', 0))
            
            c.execute('''INSERT INTO vehicles 
                         (plate, brand, model, year, color, mileage,
                          purchase_date, purchase_price, repair_cost, total_cost,
                          asking_price, min_price, status, created_by)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (row.get('車牌', '').strip(),
                       brand, model,
                       _parse_number(row.get('年份')),
                       row.get('顏色', '').strip(),
                       _parse_number(row.get('里程', 0)),
                       row.get('購入日期', '').strip(),
                       purchase_price,
                       repair_cost,
                       purchase_price + repair_cost,
                       _parse_number(row.get('定價', 0)),
                       _parse_number(row.get('底價', 0)),
                       'in_stock',
                       user_id))
            success += 1
            
        except Exception as e:
            errors.append(f'第 {i} 行：{str(e)}')
    
    conn.commit()
    conn.close()
    
    return {
        'success': True,
        'imported': success,
        'errors': errors
    }


def _parse_number(value, default=0):
    """解析數字"""
    if not value:
        return default
    try:
        # 移除逗號和空白
        cleaned = str(value).replace(',', '').replace(' ', '').strip()
        return int(float(cleaned))
    except:
        return default


def _map_source(value):
    """對照來源"""
    mapping = {
        '現場': 'walk_in', '現場來店': 'walk_in',
        '電話': 'phone', '電話詢問': 'phone',
        'LINE': 'line', 'line': 'line',
        'FB': 'facebook', 'Facebook': 'facebook', 'facebook': 'facebook',
        '介紹': 'referral', '朋友介紹': 'referral',
        '網站': 'web',
    }
    return mapping.get(value.strip(), 'other')


def _map_level(value):
    """對照等級"""
    mapping = {
        'VIP': 'vip', 'vip': 'vip',
        '一般': 'normal', '普通': 'normal',
        '潛在': 'potential',
        '冷淡': 'cold',
    }
    return mapping.get(value.strip(), 'normal')


# ===== 模板產生 =====

def generate_customer_template():
    """產生客戶匯入模板"""
    headers = ['姓名', '電話', '電話2', 'Email', '地址', '來源', '等級', '備註']
    example = ['王小明', '0912345678', '', 'test@example.com', '台北市...', '現場來店', '一般', '對 Toyota 有興趣']
    
    output = io.StringIO()
    output.write('\ufeff')  # BOM
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerow(example)
    
    return output.getvalue()


def generate_vehicle_template():
    """產生車輛匯入模板"""
    headers = ['車牌', '品牌', '型號', '年份', '顏色', '里程', '購入日期', '購入價', '整備費', '定價', '底價']
    example = ['ABC-1234', 'Toyota', 'Altis', '2020', '白色', '50000', '2026-01-15', '450000', '30000', '520000', '480000']
    
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerow(example)
    
    return output.getvalue()


# 📚 知識點
# -----------
# 1. io.StringIO：記憶體中的文字串流
#    - 像檔案一樣讀寫，但不實際建立檔案
#    - .getvalue() 取得全部內容
#    - 適合產生 CSV/文字輸出
#
# 2. csv 模組：
#    - csv.writer：寫入 CSV
#    - csv.DictReader：讀取 CSV 為字典（用欄位名當 key）
#    - 自動處理逗號、引號等特殊字元
#
# 3. BOM (Byte Order Mark)：
#    - '\ufeff' 是 UTF-8 的 BOM
#    - 加在檔案開頭讓 Excel 正確識別中文
#    - 否則 Excel 會用預設編碼（可能亂碼）
#
# 4. enumerate(iterable, start=n)：
#    - 迭代時同時取得索引和值
#    - start=2 讓索引從 2 開始（配合 Excel 行號）
