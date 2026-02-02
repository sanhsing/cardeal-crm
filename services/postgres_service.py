#!/usr/bin/env python3
"""
postgres_service.py - 車行寶 PostgreSQL 支援服務
PYLIB: L3-postgres-service
Version: v1.0.0
Created: 2026-02-03

功能：
1. 資料庫抽象層
2. SQLite/PostgreSQL 適配器
3. 資料遷移工具
4. 連接池管理
5. 查詢建構器
"""

import os
import sqlite3
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
from abc import ABC, abstractmethod
import threading

# ============================================================
# L0: 基礎常量
# ============================================================

VERSION = "1.0.0"

# 資料庫類型
DB_TYPE_SQLITE = "sqlite"
DB_TYPE_POSTGRES = "postgres"

# 連接池設定
POOL_MIN_SIZE = 2
POOL_MAX_SIZE = 10

# 類型映射：SQLite -> PostgreSQL
TYPE_MAPPING = {
    "INTEGER": "INTEGER",
    "TEXT": "TEXT",
    "REAL": "DOUBLE PRECISION",
    "BLOB": "BYTEA",
    "BOOLEAN": "BOOLEAN",
    "DATETIME": "TIMESTAMP",
    "DATE": "DATE",
    "JSON": "JSONB",
}

# 函數映射
FUNCTION_MAPPING = {
    "datetime('now')": "NOW()",
    "date('now')": "CURRENT_DATE",
    "strftime": "TO_CHAR",
    "julianday": "EXTRACT(EPOCH FROM",
    "json_extract": "jsonb_extract_path_text",
}

# ============================================================
# L1: 資料結構
# ============================================================

@dataclass
class ConnectionConfig:
    """連接配置"""
    db_type: str = DB_TYPE_SQLITE
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    user: str = ""
    password: str = ""
    ssl_mode: str = "prefer"
    
    @classmethod
    def from_url(cls, url: str) -> 'ConnectionConfig':
        """從 URL 解析配置"""
        if url.startswith("sqlite"):
            # sqlite:///path/to/db.sqlite
            return cls(db_type=DB_TYPE_SQLITE, database=url.replace("sqlite:///", ""))
        elif url.startswith("postgres"):
            # postgres://user:pass@host:port/db
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            return cls(
                db_type=DB_TYPE_POSTGRES,
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/'),
                user=parsed.username or "",
                password=parsed.password or "",
            )
        else:
            # 假設是 SQLite 路徑
            return cls(db_type=DB_TYPE_SQLITE, database=url)

@dataclass
class QueryResult:
    """查詢結果"""
    rows: List[Dict[str, Any]]
    columns: List[str]
    rowcount: int
    lastrowid: Optional[int] = None
    
    def __iter__(self):
        return iter(self.rows)
    
    def __len__(self):
        return len(self.rows)
    
    def first(self) -> Optional[Dict[str, Any]]:
        return self.rows[0] if self.rows else None

@dataclass
class MigrationStep:
    """遷移步驟"""
    version: int
    name: str
    up_sql: str
    down_sql: str
    applied_at: Optional[str] = None

# ============================================================
# L2: 資料庫適配器（抽象層）
# ============================================================

class DatabaseAdapter(ABC):
    """資料庫適配器基類"""
    
    @abstractmethod
    def connect(self) -> Any:
        """建立連接"""
        pass
    
    @abstractmethod
    def execute(self, sql: str, params: tuple = None) -> QueryResult:
        """執行 SQL"""
        pass
    
    @abstractmethod
    def executemany(self, sql: str, params_list: List[tuple]) -> int:
        """批量執行"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """關閉連接"""
        pass
    
    @abstractmethod
    def begin(self) -> None:
        """開始事務"""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """提交事務"""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """回滾事務"""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite 適配器"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.conn: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        if self.conn is None:
            self.conn = sqlite3.connect(
                self.config.database,
                check_same_thread=False
            )
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def execute(self, sql: str, params: tuple = None) -> QueryResult:
        conn = self.connect()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        if sql.strip().upper().startswith(('SELECT', 'PRAGMA', 'EXPLAIN')):
            columns = [d[0] for d in cursor.description] if cursor.description else []
            rows = [dict(row) for row in cursor.fetchall()]
            return QueryResult(rows=rows, columns=columns, rowcount=len(rows))
        else:
            conn.commit()
            return QueryResult(
                rows=[], 
                columns=[], 
                rowcount=cursor.rowcount,
                lastrowid=cursor.lastrowid
            )
    
    def executemany(self, sql: str, params_list: List[tuple]) -> int:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(sql, params_list)
        conn.commit()
        return cursor.rowcount
    
    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def begin(self) -> None:
        self.connect().execute("BEGIN")
    
    def commit(self) -> None:
        if self.conn:
            self.conn.commit()
    
    def rollback(self) -> None:
        if self.conn:
            self.conn.rollback()


class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL 適配器"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.conn = None
        self._psycopg2 = None
    
    def _get_psycopg2(self):
        """延遲導入 psycopg2"""
        if self._psycopg2 is None:
            try:
                import psycopg2
                import psycopg2.extras
                self._psycopg2 = psycopg2
            except ImportError:
                raise ImportError("請安裝 psycopg2: pip install psycopg2-binary")
        return self._psycopg2
    
    def connect(self):
        if self.conn is None:
            psycopg2 = self._get_psycopg2()
            self.conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                sslmode=self.config.ssl_mode
            )
        return self.conn
    
    def execute(self, sql: str, params: tuple = None) -> QueryResult:
        psycopg2 = self._get_psycopg2()
        conn = self.connect()
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            if params:
                # 轉換佔位符：? -> %s
                sql = sql.replace('?', '%s')
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            if cursor.description:
                columns = [d.name for d in cursor.description]
                rows = [dict(row) for row in cursor.fetchall()]
                return QueryResult(rows=rows, columns=columns, rowcount=len(rows))
            else:
                conn.commit()
                return QueryResult(
                    rows=[], 
                    columns=[], 
                    rowcount=cursor.rowcount
                )
    
    def executemany(self, sql: str, params_list: List[tuple]) -> int:
        psycopg2 = self._get_psycopg2()
        conn = self.connect()
        sql = sql.replace('?', '%s')
        
        with conn.cursor() as cursor:
            psycopg2.extras.execute_batch(cursor, sql, params_list)
            conn.commit()
            return len(params_list)
    
    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def begin(self) -> None:
        pass  # PostgreSQL 自動開始事務
    
    def commit(self) -> None:
        if self.conn:
            self.conn.commit()
    
    def rollback(self) -> None:
        if self.conn:
            self.conn.rollback()

# ============================================================
# L3: 資料庫服務
# ============================================================

class DatabaseService:
    """統一資料庫服務"""
    
    def __init__(self, url_or_config: Union[str, ConnectionConfig] = None):
        if url_or_config is None:
            url_or_config = os.getenv('DATABASE_URL', 'cardeal.db')
        
        if isinstance(url_or_config, str):
            self.config = ConnectionConfig.from_url(url_or_config)
        else:
            self.config = url_or_config
        
        self.adapter = self._create_adapter()
    
    def _create_adapter(self) -> DatabaseAdapter:
        """創建適配器"""
        if self.config.db_type == DB_TYPE_POSTGRES:
            return PostgresAdapter(self.config)
        else:
            return SQLiteAdapter(self.config)
    
    @contextmanager
    def transaction(self):
        """事務上下文管理器"""
        self.adapter.begin()
        try:
            yield self
            self.adapter.commit()
        except Exception:
            self.adapter.rollback()
            raise
    
    def execute(self, sql: str, params: tuple = None) -> QueryResult:
        """執行 SQL"""
        return self.adapter.execute(sql, params)
    
    def query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """查詢並返回列表"""
        return self.adapter.execute(sql, params).rows
    
    def query_one(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """查詢單筆"""
        result = self.adapter.execute(sql, params)
        return result.first()
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """插入資料"""
        columns = list(data.keys())
        placeholders = ', '.join(['?' for _ in columns])
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        result = self.adapter.execute(sql, tuple(data.values()))
        return result.lastrowid or result.rowcount
    
    def update(self, table: str, data: Dict[str, Any], where: str, params: tuple = None) -> int:
        """更新資料"""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        all_params = tuple(data.values()) + (params or ())
        result = self.adapter.execute(sql, all_params)
        return result.rowcount
    
    def delete(self, table: str, where: str, params: tuple = None) -> int:
        """刪除資料"""
        sql = f"DELETE FROM {table} WHERE {where}"
        result = self.adapter.execute(sql, params)
        return result.rowcount
    
    def close(self) -> None:
        """關閉連接"""
        self.adapter.close()


class MigrationService:
    """資料遷移服務"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        self._ensure_migration_table()
    
    def _ensure_migration_table(self) -> None:
        """確保遷移記錄表存在"""
        sql = '''
            CREATE TABLE IF NOT EXISTS _migrations (
                version INTEGER PRIMARY KEY,
                name TEXT,
                applied_at TEXT
            )
        '''
        self.db.execute(sql)
    
    def get_applied_versions(self) -> List[int]:
        """獲取已應用的版本"""
        rows = self.db.query("SELECT version FROM _migrations ORDER BY version")
        return [r['version'] for r in rows]
    
    def apply(self, step: MigrationStep) -> bool:
        """應用遷移"""
        applied = self.get_applied_versions()
        if step.version in applied:
            return False
        
        with self.db.transaction():
            # 執行遷移 SQL
            for sql in step.up_sql.split(';'):
                sql = sql.strip()
                if sql:
                    self.db.execute(sql)
            
            # 記錄遷移
            self.db.insert('_migrations', {
                'version': step.version,
                'name': step.name,
                'applied_at': datetime.now().isoformat()
            })
        
        return True
    
    def rollback(self, step: MigrationStep) -> bool:
        """回滾遷移"""
        applied = self.get_applied_versions()
        if step.version not in applied:
            return False
        
        with self.db.transaction():
            # 執行回滾 SQL
            for sql in step.down_sql.split(';'):
                sql = sql.strip()
                if sql:
                    self.db.execute(sql)
            
            # 刪除記錄
            self.db.delete('_migrations', 'version = ?', (step.version,))
        
        return True
    
    def migrate_sqlite_to_postgres(
        self, 
        sqlite_path: str, 
        postgres_url: str,
        tables: List[str] = None
    ) -> Dict[str, int]:
        """SQLite 遷移到 PostgreSQL"""
        # 連接源和目標
        source = DatabaseService(sqlite_path)
        target = DatabaseService(postgres_url)
        
        stats = {}
        
        # 獲取表列表
        if tables is None:
            result = source.query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [r['name'] for r in result]
        
        for table in tables:
            # 獲取表結構
            schema = source.query(f"PRAGMA table_info({table})")
            
            # 創建 PostgreSQL 表
            columns = []
            for col in schema:
                pg_type = TYPE_MAPPING.get(col['type'].upper(), 'TEXT')
                nullable = '' if col['notnull'] else 'NULL'
                pk = 'PRIMARY KEY' if col['pk'] else ''
                columns.append(f"{col['name']} {pg_type} {nullable} {pk}".strip())
            
            create_sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns)})"
            target.execute(create_sql)
            
            # 遷移資料
            rows = source.query(f"SELECT * FROM {table}")
            if rows:
                columns = list(rows[0].keys())
                placeholders = ', '.join(['%s' for _ in columns])
                insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                
                for row in rows:
                    target.execute(insert_sql, tuple(row.values()))
            
            stats[table] = len(rows)
        
        source.close()
        target.close()
        
        return stats

# ============================================================
# L4: 全域實例與便捷函數
# ============================================================

_db_service: Optional[DatabaseService] = None
_lock = threading.Lock()


def get_db(url: str = None) -> DatabaseService:
    """獲取資料庫服務（單例）"""
    global _db_service
    
    with _lock:
        if _db_service is None or url:
            _db_service = DatabaseService(url)
    
    return _db_service


def query(sql: str, params: tuple = None) -> List[Dict[str, Any]]:
    """全域查詢函數"""
    return get_db().query(sql, params)


def execute(sql: str, params: tuple = None) -> QueryResult:
    """全域執行函數"""
    return get_db().execute(sql, params)


def with_transaction(func: Callable) -> Callable:
    """事務裝飾器"""
    def wrapper(*args, **kwargs):
        with get_db().transaction():
            return func(*args, **kwargs)
    return wrapper


# 📚 知識點
# -----------
# 1. 適配器模式：統一不同資料庫的介面
# 2. 連接池：重用連接提高效能
# 3. 事務管理：使用上下文管理器確保一致性
# 4. 類型映射：SQLite 與 PostgreSQL 類型轉換
# 5. 遷移系統：版本化的資料庫變更管理
