"""
車行寶 CRM v5.1 - 資料庫結構定義
北斗七星文創數位 × 織明

所有表結構集中管理，方便維護和升級
"""
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

import hashlib
import os
import config
from .database import get_connection

# ===== 主資料庫結構 =====

MASTER_TABLES = {
    'tenants': '''
        CREATE TABLE IF NOT EXISTS tenants (
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
        )
    ''',
    
    'subscriptions': '''
        CREATE TABLE IF NOT EXISTS subscriptions (
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
        )
    ''',
    
    'error_logs': '''
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            error_type TEXT,
            message TEXT,
            details TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    '''
}

# ===== 租戶資料庫結構 =====

TENANT_TABLES = {
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
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
        )
    ''',
    
    'customers': '''
        CREATE TABLE IF NOT EXISTS customers (
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
        )
    ''',
    
    'vehicles': '''
        CREATE TABLE IF NOT EXISTS vehicles (
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
        )
    ''',
    
    'vehicle_images': '''
        CREATE TABLE IF NOT EXISTS vehicle_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            path TEXT NOT NULL,
            is_primary INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
        )
    ''',
    
    'deals': '''
        CREATE TABLE IF NOT EXISTS deals (
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
        )
    ''',
    
    'followups': '''
        CREATE TABLE IF NOT EXISTS followups (
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
        )
    ''',
    
    'activity_logs': '''
        CREATE TABLE IF NOT EXISTS activity_logs (
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
        )
    ''',
    
    'line_bindings': '''
        CREATE TABLE IF NOT EXISTS line_bindings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            line_user_id TEXT UNIQUE,
            display_name TEXT,
            picture_url TEXT,
            bound_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''',
    
    'settings': '''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    '''
}

# ===== 索引定義 =====

TENANT_INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)',
    'CREATE INDEX IF NOT EXISTS idx_customers_line_user_id ON customers(line_user_id)',
    'CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status)',
    'CREATE INDEX IF NOT EXISTS idx_customers_level ON customers(level)',
    'CREATE INDEX IF NOT EXISTS idx_customers_next_followup ON customers(next_followup)',
    'CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status)',
    'CREATE INDEX IF NOT EXISTS idx_vehicles_brand ON vehicles(brand)',
    'CREATE INDEX IF NOT EXISTS idx_vehicles_plate ON vehicles(plate)',
    'CREATE INDEX IF NOT EXISTS idx_deals_customer ON deals(customer_id)',
    'CREATE INDEX IF NOT EXISTS idx_deals_vehicle ON deals(vehicle_id)',
    'CREATE INDEX IF NOT EXISTS idx_deals_date ON deals(deal_date)',
    'CREATE INDEX IF NOT EXISTS idx_deals_type ON deals(deal_type)',
    'CREATE INDEX IF NOT EXISTS idx_followups_customer ON followups(customer_id)',
    'CREATE INDEX IF NOT EXISTS idx_followups_next_date ON followups(next_date)',
    'CREATE INDEX IF NOT EXISTS idx_line_bindings_customer ON line_bindings(customer_id)',
    'CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at)',
]


def init_master_db() -> bool:
    """初始化主資料庫"""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    
    for table_name, sql in MASTER_TABLES.items():
        c.execute(sql)
    
    conn.commit()
    conn.close()
    return True


def init_tenant_database(tenant_code, admin_phone='0900000000', 
                         admin_password='1234', admin_name='老闆'):
    """初始化租戶資料庫"""
    db_path = os.path.join(config.DATA_DIR, f'tenant_{tenant_code}.db')
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 建立所有表
    for table_name, sql in TENANT_TABLES.items():
        c.execute(sql)
    
    # 建立索引
    for idx_sql in TENANT_INDEXES:
        c.execute(idx_sql)
    
    # 建立管理員帳號
    pwd_hash = hashlib.sha256(admin_password.encode()).hexdigest()
    try:
        c.execute('''INSERT INTO users (name, phone, password, role, permissions)
                     VALUES (?, ?, ?, 'admin', '["all"]')''',
                  (admin_name, admin_phone, pwd_hash))
    except:
        pass  # 已存在則跳過
    
    conn.commit()
    conn.close()
    
    return db_path


def migrate_database(db_path, version):
    """資料庫遷移（版本升級用）"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 取得當前版本
    c.execute("SELECT value FROM settings WHERE key = 'db_version'")
    row = c.fetchone()
    current_version = int(row['value']) if row else 0
    
    migrations = {
        # 版本號: 遷移 SQL 列表
        1: [
            "ALTER TABLE customers ADD COLUMN gender TEXT",
            "ALTER TABLE customers ADD COLUMN birthday TEXT",
        ],
        2: [
            "ALTER TABLE vehicles ADD COLUMN vin TEXT",
        ],
        # 未來版本在此添加
    }
    
    for v in range(current_version + 1, version + 1):
        if v in migrations:
            for sql in migrations[v]:
                try:
                    c.execute(sql)
                except Exception as e:
                    print(f"Migration {v} warning: {e}")
    
    # 更新版本號
    c.execute('''INSERT OR REPLACE INTO settings (key, value, updated_at) 
                 VALUES ('db_version', ?, CURRENT_TIMESTAMP)''', (str(version),))
    
    conn.commit()
    conn.close()
    
    return True


# 📚 知識點
# -----------
# 1. 資料庫 Schema 集中管理：
#    - 所有表結構放在一個檔案
#    - 方便查看整體結構
#    - 版本升級時容易追蹤變更
#
# 2. FOREIGN KEY（外鍵）：
#    - 建立表之間的關聯
#    - customer_id REFERENCES customers(id)
#    - 確保資料一致性（不能引用不存在的記錄）
#
# 3. DEFAULT 值：
#    - 欄位預設值
#    - DEFAULT CURRENT_TIMESTAMP：插入時自動填入當前時間
#    - DEFAULT '[]'：預設空 JSON 陣列
#
# 4. 資料庫遷移（Migration）：
#    - 版本升級時修改表結構
#    - ALTER TABLE 添加新欄位
#    - 記錄 db_version 追蹤當前版本
#
# 5. INDEX（索引）：
#    - 加速查詢，但會增加寫入成本
#    - 常用於 WHERE、ORDER BY、JOIN 的欄位
#    - 選擇性高的欄位（如 phone）效果更好
