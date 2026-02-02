"""
車行寶 CRM v5.1 - 資料庫工具模組
北斗七星文創數位 × 織明

功能：資料庫診斷、優化、維護
"""
from typing import Dict, List, Any, Optional, Union, Callable

import os
import sqlite3
from datetime import datetime
from .database import get_connection

# ===== 資料庫診斷 =====

def analyze_database(db_path: str) -> Dict[str, Any]:
    """分析資料庫狀態"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    result = {
        'path': db_path,
        'size_bytes': os.path.getsize(db_path) if os.path.exists(db_path) else 0,
        'tables': {},
        'indexes': [],
        'integrity': True
    }
    
    # 取得所有表格
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in c.fetchall()]
    
    for table in tables:
        # 表格資訊
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        
        c.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in c.fetchall()]
        
        result['tables'][table] = {
            'row_count': count,
            'columns': columns
        }
    
    # 取得所有索引
    c.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    for row in c.fetchall():
        result['indexes'].append({
            'name': row[0],
            'table': row[1]
        })
    
    # 完整性檢查
    c.execute("PRAGMA integrity_check")
    integrity = c.fetchone()[0]
    result['integrity'] = (integrity == 'ok')
    result['integrity_message'] = integrity
    
    conn.close()
    
    # 格式化大小
    size = result['size_bytes']
    if size > 1024 * 1024:
        result['size'] = f"{size / (1024 * 1024):.2f} MB"
    elif size > 1024:
        result['size'] = f"{size / 1024:.2f} KB"
    else:
        result['size'] = f"{size} B"
    
    return result


def explain_query(db_path: str, sql: str, params: tuple = ()) -> Dict[str, Any]:
    """分析查詢執行計劃"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute(f"EXPLAIN QUERY PLAN {sql}", params)
    plan = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return {
        'sql': sql,
        'plan': plan,
        'suggestions': _analyze_query_plan(plan)
    }


def _analyze_query_plan(plan: List[Tuple]) -> Dict[str, Any]:
    """分析查詢計劃並給出建議"""
    suggestions = []
    
    for step in plan:
        detail = step.get('detail', '')
        
        if 'SCAN TABLE' in detail and 'USING INDEX' not in detail:
            table = detail.replace('SCAN TABLE ', '').split()[0]
            suggestions.append(f"⚠️ 表 {table} 進行全表掃描，考慮添加索引")
        
        if 'SEARCH' in detail and 'USING INDEX' in detail:
            # 使用了索引，很好
            pass
        
        if 'TEMP B-TREE' in detail:
            suggestions.append("⚠️ 使用了臨時 B-Tree（排序/GROUP BY），可能較慢")
    
    if not suggestions:
        suggestions.append("✅ 查詢計劃看起來不錯")
    
    return suggestions


# ===== 資料庫優化 =====

def optimize_database(db_path: str) -> Dict[str, Any]:
    """優化資料庫"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    results = []
    
    # 更新統計資訊
    c.execute("ANALYZE")
    results.append("✅ 已更新統計資訊 (ANALYZE)")
    
    # 重建索引
    c.execute("REINDEX")
    results.append("✅ 已重建索引 (REINDEX)")
    
    conn.commit()
    conn.close()
    
    return {
        'success': True,
        'actions': results
    }


def vacuum_database(db_path: str) -> Dict[str, Any]:
    """壓縮資料庫（回收空間）"""
    original_size = os.path.getsize(db_path)
    
    conn = sqlite3.connect(db_path)
    conn.execute("VACUUM")
    conn.close()
    
    new_size = os.path.getsize(db_path)
    saved = original_size - new_size
    
    return {
        'success': True,
        'original_size': original_size,
        'new_size': new_size,
        'saved_bytes': saved,
        'saved_percent': round(saved / original_size * 100, 2) if original_size > 0 else 0
    }


# ===== 索引管理 =====

def create_index(db_path: str, table: str, columns: List[str], unique: bool = False) -> bool:
    """建立索引"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    if isinstance(columns, str):
        columns = [columns]
    
    index_name = f"idx_{table}_{'_'.join(columns)}"
    columns_str = ', '.join(columns)
    unique_str = 'UNIQUE' if unique else ''
    
    try:
        c.execute(f"CREATE {unique_str} INDEX IF NOT EXISTS {index_name} ON {table}({columns_str})")
        conn.commit()
        return {'success': True, 'index': index_name}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


def drop_index(db_path: str, index_name: str) -> bool:
    """刪除索引"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    try:
        c.execute(f"DROP INDEX IF EXISTS {index_name}")
        conn.commit()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()


def suggest_indexes(db_path: str) -> List[Dict[str, Any]]:
    """建議需要的索引"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    suggestions = []
    
    # 檢查常用查詢欄位是否有索引
    common_patterns = [
        ('customers', 'phone', '電話查詢'),
        ('customers', 'status', '狀態篩選'),
        ('customers', 'next_followup', '跟進提醒'),
        ('vehicles', 'status', '車輛狀態'),
        ('vehicles', 'brand', '品牌篩選'),
        ('deals', 'deal_date', '日期查詢'),
        ('deals', 'customer_id', '客戶交易'),
    ]
    
    # 取得現有索引
    c.execute("SELECT name FROM sqlite_master WHERE type='index'")
    existing = set(row[0] for row in c.fetchall())
    
    for table, column, desc in common_patterns:
        index_name = f"idx_{table}_{column}"
        if index_name not in existing:
            suggestions.append({
                'table': table,
                'column': column,
                'reason': desc,
                'sql': f"CREATE INDEX {index_name} ON {table}({column})"
            })
    
    conn.close()
    
    return suggestions


# ===== 資料清理 =====

def cleanup_old_data(db_path, table, date_column, days_to_keep):
    """清理舊資料"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 先計算要刪除的數量
    c.execute(f'''SELECT COUNT(*) FROM {table} 
                  WHERE {date_column} < date("now", "-{days_to_keep} days")''')
    count = c.fetchone()[0]
    
    if count > 0:
        c.execute(f'''DELETE FROM {table} 
                      WHERE {date_column} < date("now", "-{days_to_keep} days")''')
        conn.commit()
    
    conn.close()
    
    return {
        'success': True,
        'deleted': count,
        'table': table
    }


def archive_data(db_path, archive_path, table, date_column, before_date):
    """歸檔舊資料"""
    # 連接來源和目標資料庫
    src_conn = get_connection(db_path)
    src_conn.execute(f"ATTACH DATABASE '{archive_path}' AS archive")
    c = src_conn.cursor()
    
    # 確保目標表存在（複製結構）
    c.execute(f"CREATE TABLE IF NOT EXISTS archive.{table} AS SELECT * FROM {table} WHERE 0")
    
    # 複製資料
    c.execute(f'''INSERT INTO archive.{table} 
                  SELECT * FROM {table} 
                  WHERE {date_column} < ?''', (before_date,))
    copied = c.rowcount
    
    # 刪除已歸檔的資料
    c.execute(f"DELETE FROM {table} WHERE {date_column} < ?", (before_date,))
    
    src_conn.commit()
    src_conn.execute("DETACH DATABASE archive")
    src_conn.close()
    
    return {
        'success': True,
        'archived': copied,
        'table': table,
        'archive_path': archive_path
    }


# ===== 資料匯出 =====

def export_table_to_sql(db_path, table) -> bytes:
    """匯出表格為 SQL"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 取得表結構
    c.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
    create_sql = c.fetchone()[0]
    
    # 取得資料
    c.execute(f"SELECT * FROM {table}")
    rows = c.fetchall()
    
    # 取得欄位名
    columns = [desc[0] for desc in c.description]
    
    conn.close()
    
    # 產生 SQL
    sql_lines = [f"-- Exported from {db_path} at {datetime.now().isoformat()}", ""]
    sql_lines.append(f"DROP TABLE IF EXISTS {table};")
    sql_lines.append(create_sql + ";")
    sql_lines.append("")
    
    for row in rows:
        values = []
        for v in row:
            if v is None:
                values.append("NULL")
            elif isinstance(v, str):
                values.append(f"'{v.replace(chr(39), chr(39)+chr(39))}'")
            else:
                values.append(str(v))
        
        sql_lines.append(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});")
    
    return '\n'.join(sql_lines)


# 📚 知識點
# -----------
# 1. EXPLAIN QUERY PLAN：
#    - SQLite 查詢分析工具
#    - 顯示查詢如何執行
#    - SCAN = 全表掃描（慢）
#    - SEARCH USING INDEX = 使用索引（快）
#
# 2. ANALYZE：
#    - 更新表格統計資訊
#    - 幫助查詢優化器做出更好決策
#    - 建議定期執行
#
# 3. VACUUM：
#    - 回收已刪除資料的空間
#    - 重組資料庫檔案
#    - 可能需要較長時間
#
# 4. REINDEX：
#    - 重建所有索引
#    - 解決索引碎片問題
#    - 提升查詢效能
#
# 5. ATTACH DATABASE：
#    - 同時連接多個資料庫
#    - 可跨庫查詢和複製
#    - 用於資料歸檔
#
# 6. 索引設計原則：
#    - 頻繁查詢的欄位加索引
#    - WHERE、ORDER BY、JOIN 欄位
#    - 不要過度索引（影響寫入）
