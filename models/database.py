"""
車行寶 CRM v5.0 - 資料庫模組
北斗七星文創數位 × 織明
"""
import sqlite3
import hashlib
import os
from datetime import datetime
import config

def get_connection(db_path):
    """取得資料庫連線"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_master_db():
    """初始化主資料庫"""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    
    # 租戶表
    c.execute('''CREATE TABLE IF NOT EXISTS tenants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        db_path TEXT NOT NULL,
        plan TEXT DEFAULT 'free',
        plan_expires TEXT,
        line_channel_secret TEXT,
        line_channel_access_token TEXT,
        owner_name TEXT,
        owner_phone TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active'
    )''')
    
    # 訂閱記錄表
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER,
        plan_code TEXT,
        amount INTEGER,
        trade_no TEXT UNIQUE,
        merchant_trade_no TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        paid_at TEXT,
        expires_at TEXT,
        FOREIGN KEY (tenant_id) REFERENCES tenants(id)
    )''')
    
    # 錯誤日誌表
    c.execute('''CREATE TABLE IF NOT EXISTS error_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER,
        error_type TEXT,
        message TEXT,
        details TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()
    return True

def get_tenant_db_path(tenant_id):
    """取得租戶資料庫路徑"""
    if isinstance(tenant_id, int):
        return os.path.join(config.DATA_DIR, f'tenant_{tenant_id}.db')
    return os.path.join(config.DATA_DIR, f'tenant_{tenant_id}.db')

def get_tenant_by_code(code):
    """根據代碼取得租戶"""
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM tenants WHERE code = ? AND status = "active"', (code,))
    tenant = c.fetchone()
    conn.close()
    return dict(tenant) if tenant else None

def get_tenant_by_id(tenant_id):
    """根據 ID 取得租戶"""
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM tenants WHERE id = ?', (tenant_id,))
    tenant = c.fetchone()
    conn.close()
    return dict(tenant) if tenant else None

def create_tenant(code, name, admin_phone, admin_password, admin_name='管理員'):
    """建立新租戶"""
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    
    try:
        db_path = get_tenant_db_path(code)
        c.execute('''INSERT INTO tenants (code, name, db_path, owner_name, owner_phone) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (code, name, db_path, admin_name, admin_phone))
        tenant_id = c.lastrowid
        conn.commit()
        
        # 初始化租戶資料庫
        init_tenant_database(code, admin_phone, admin_password, admin_name)
        
        return {'success': True, 'tenant_id': tenant_id, 'code': code}
    except sqlite3.IntegrityError:
        return {'success': False, 'error': '店家代碼已存在'}
    finally:
        conn.close()

def verify_login(code, phone, password):
    """驗證登入"""
    tenant = get_tenant_by_code(code)
    if not tenant:
        return {'success': False, 'error': '店家代碼不存在'}
    
    # 驗證使用者
    conn = get_connection(tenant['db_path'])
    c = conn.cursor()
    
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    c.execute('''SELECT id, name, role, permissions FROM users 
                 WHERE phone = ? AND password = ? AND status = "active"''',
              (phone, pwd_hash))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return {'success': False, 'error': '帳號或密碼錯誤'}
    
    return {
        'success': True,
        'tenant_id': tenant['id'],
        'tenant_code': tenant['code'],
        'tenant_name': tenant['name'],
        'db_path': tenant['db_path'],
        'user_id': user['id'],
        'user_name': user['name'],
        'role': user['role'],
        'permissions': user['permissions'],
        'plan': tenant['plan'],
        'plan_expires': tenant['plan_expires']
    }

def init_tenant_database(tenant_code, admin_phone='0900000000', admin_password='1234', admin_name='老闆'):
    """初始化租戶資料庫"""
    db_path = get_tenant_db_path(tenant_code)
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # ===== 使用者表 =====
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'staff',
        permissions TEXT DEFAULT '[]',
        avatar TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_login TEXT,
        status TEXT DEFAULT 'active'
    )''')
    
    # ===== 客戶表 =====
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        phone2 TEXT,
        line_id TEXT,
        line_user_id TEXT,
        email TEXT,
        address TEXT,
        gender TEXT,
        birthday TEXT,
        source TEXT DEFAULT 'walk_in',
        level TEXT DEFAULT 'normal',
        tags TEXT DEFAULT '[]',
        notes TEXT,
        total_deals INTEGER DEFAULT 0,
        total_amount INTEGER DEFAULT 0,
        last_contact TEXT,
        next_followup TEXT,
        assigned_to INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (assigned_to) REFERENCES users(id)
    )''')
    
    # ===== 車輛表 =====
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate TEXT,
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        year INTEGER,
        color TEXT,
        mileage INTEGER DEFAULT 0,
        engine_cc INTEGER,
        fuel_type TEXT,
        transmission TEXT,
        vin TEXT,
        purchase_date TEXT,
        purchase_price INTEGER DEFAULT 0,
        purchase_from TEXT,
        repair_cost INTEGER DEFAULT 0,
        total_cost INTEGER DEFAULT 0,
        asking_price INTEGER DEFAULT 0,
        min_price INTEGER DEFAULT 0,
        photos TEXT DEFAULT '[]',
        features TEXT DEFAULT '[]',
        condition_notes TEXT,
        location TEXT,
        status TEXT DEFAULT 'in_stock',
        sold_date TEXT,
        sold_price INTEGER,
        sold_to INTEGER,
        created_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sold_to) REFERENCES customers(id),
        FOREIGN KEY (created_by) REFERENCES users(id)
    )''')
    
    # ===== 交易表 =====
    c.execute('''CREATE TABLE IF NOT EXISTS deals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deal_type TEXT NOT NULL,
        customer_id INTEGER,
        vehicle_id INTEGER,
        amount INTEGER NOT NULL,
        cost INTEGER DEFAULT 0,
        profit INTEGER DEFAULT 0,
        payment_method TEXT,
        payment_status TEXT DEFAULT 'pending',
        deal_date TEXT,
        notes TEXT,
        documents TEXT DEFAULT '[]',
        created_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'completed',
        FOREIGN KEY (customer_id) REFERENCES customers(id),
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
        FOREIGN KEY (created_by) REFERENCES users(id)
    )''')
    
    # ===== 跟進記錄表 =====
    c.execute('''CREATE TABLE IF NOT EXISTS followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        vehicle_id INTEGER,
        user_id INTEGER,
        type TEXT DEFAULT 'call',
        content TEXT,
        result TEXT,
        next_action TEXT,
        next_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id),
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # ===== 活動日誌表 =====
    c.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,
        action TEXT NOT NULL,
        target_type TEXT,
        target_id INTEGER,
        target_name TEXT,
        details TEXT,
        ip_address TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # ===== LINE 綁定表 =====
    c.execute('''CREATE TABLE IF NOT EXISTS line_bindings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        line_user_id TEXT UNIQUE,
        display_name TEXT,
        picture_url TEXT,
        bound_at TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )''')
    
    # ===== 設定表 =====
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 建立索引
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)',
        'CREATE INDEX IF NOT EXISTS idx_customers_line_user_id ON customers(line_user_id)',
        'CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status)',
        'CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status)',
        'CREATE INDEX IF NOT EXISTS idx_vehicles_brand ON vehicles(brand)',
        'CREATE INDEX IF NOT EXISTS idx_deals_customer ON deals(customer_id)',
        'CREATE INDEX IF NOT EXISTS idx_deals_vehicle ON deals(vehicle_id)',
        'CREATE INDEX IF NOT EXISTS idx_deals_date ON deals(deal_date)',
        'CREATE INDEX IF NOT EXISTS idx_followups_customer ON followups(customer_id)',
        'CREATE INDEX IF NOT EXISTS idx_followups_next_date ON followups(next_date)',
        'CREATE INDEX IF NOT EXISTS idx_line_bindings_customer ON line_bindings(customer_id)',
    ]
    for idx in indexes:
        c.execute(idx)
    
    # 建立管理員帳號
    pwd_hash = hashlib.sha256(admin_password.encode()).hexdigest()
    try:
        c.execute('''INSERT INTO users (name, phone, password, role, permissions)
                     VALUES (?, ?, ?, 'admin', '["all"]')''',
                  (admin_name, admin_phone, pwd_hash))
    except sqlite3.IntegrityError:
        pass
    
    conn.commit()
    conn.close()
    return db_path

def log_error(error_type, message, details='', tenant_id=None):
    """記錄錯誤"""
    try:
        conn = get_connection(config.MASTER_DB)
        c = conn.cursor()
        c.execute('''INSERT INTO error_logs (tenant_id, error_type, message, details)
                     VALUES (?, ?, ?, ?)''',
                  (tenant_id, error_type, message, details))
        conn.commit()
        conn.close()
    except:
        pass
