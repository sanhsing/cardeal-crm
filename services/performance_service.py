"""
車行寶 CRM v5.1 - 性能優化服務
北斗七星文創數位 × 織明

功能：
1. 資料庫連接池
2. 查詢優化與分析
3. 索引建議
4. 批量操作優化
5. 慢查詢檢測
"""
import sqlite3
import time
import threading
import queue
import logging
from functools import wraps
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager

logger = logging.getLogger(__name__)


# ============================================================
# 1. 資料庫連接池
# ============================================================

class ConnectionPool:
    """SQLite 連接池
    
    雖然 SQLite 是單檔案資料庫，連接池仍能：
    - 減少連接建立開銷
    - 控制並發連接數
    - 統一連接配置
    """
    
    def __init__(self, db_path: str, max_connections: int = 10, timeout: float = 30.0):
        """
        Args:
            db_path: 資料庫路徑
            max_connections: 最大連接數
            timeout: 取得連接的超時時間
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool = queue.Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._created = 0
        self._in_use = 0
        
        # 統計
        self.stats = {
            'total_requests': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'timeouts': 0
        }
    
    def _create_connection(self) -> sqlite3.Connection:
        """創建新連接"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=self.timeout
        )
        conn.row_factory = sqlite3.Row
        
        # 優化配置
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-64000")  # 64MB
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB
        
        return conn
    
    def get_connection(self) -> sqlite3.Connection:
        """取得連接"""
        self.stats['total_requests'] += 1
        
        try:
            # 嘗試從池中取得
            conn = self._pool.get_nowait()
            self.stats['pool_hits'] += 1
            self._in_use += 1
            return conn
        except queue.Empty:
            pass
        
        # 池中無可用連接
        with self._lock:
            if self._created < self.max_connections:
                # 創建新連接
                conn = self._create_connection()
                self._created += 1
                self._in_use += 1
                self.stats['pool_misses'] += 1
                return conn
        
        # 達到最大連接數，等待
        try:
            conn = self._pool.get(timeout=self.timeout)
            self.stats['pool_hits'] += 1
            self._in_use += 1
            return conn
        except queue.Empty:
            self.stats['timeouts'] += 1
            raise TimeoutError("無法取得資料庫連接")
    
    def return_connection(self, conn: sqlite3.Connection):
        """歸還連接"""
        self._in_use -= 1
        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            # 池已滿，關閉連接
            conn.close()
            with self._lock:
                self._created -= 1
    
    @contextmanager
    def connection(self):
        """連接上下文管理器"""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            self.return_connection(conn)
    
    def get_stats(self) -> Dict:
        """取得統計資訊"""
        return {
            **self.stats,
            'pool_size': self._pool.qsize(),
            'in_use': self._in_use,
            'created': self._created,
            'hit_rate': round(self.stats['pool_hits'] / max(self.stats['total_requests'], 1) * 100, 2)
        }
    
    def close_all(self):
        """關閉所有連接"""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except queue.Empty:
                break
        self._created = 0


# 全域連接池
_pools: Dict[str, ConnectionPool] = {}
_pools_lock = threading.Lock()


def get_pool(db_path: str, max_connections: int = 10) -> ConnectionPool:
    """取得或創建連接池"""
    with _pools_lock:
        if db_path not in _pools:
            _pools[db_path] = ConnectionPool(db_path, max_connections)
        return _pools[db_path]


# ============================================================
# 2. 查詢效能分析
# ============================================================

@dataclass
class QueryStats:
    """查詢統計"""
    sql: str
    execution_time: float
    rows_affected: int
    timestamp: datetime = field(default_factory=datetime.now)
    explain_plan: str = ""


class QueryAnalyzer:
    """查詢分析器"""
    
    def __init__(self, slow_threshold: float = 0.5):
        """
        Args:
            slow_threshold: 慢查詢閾值（秒）
        """
        self.slow_threshold = slow_threshold
        self.query_history: List[QueryStats] = []
        self.slow_queries: List[QueryStats] = []
        self._lock = threading.Lock()
        self.max_history = 1000
    
    def record_query(self, sql: str, execution_time: float, rows_affected: int = 0):
        """記錄查詢"""
        stats = QueryStats(
            sql=sql[:500],  # 截斷過長 SQL
            execution_time=execution_time,
            rows_affected=rows_affected
        )
        
        with self._lock:
            self.query_history.append(stats)
            if len(self.query_history) > self.max_history:
                self.query_history.pop(0)
            
            if execution_time >= self.slow_threshold:
                self.slow_queries.append(stats)
                if len(self.slow_queries) > 100:
                    self.slow_queries.pop(0)
                logger.warning(f"慢查詢 ({execution_time:.3f}s): {sql[:100]}...")
    
    def get_slow_queries(self, limit: int = 20) -> List[Dict]:
        """取得慢查詢列表"""
        with self._lock:
            return [
                {
                    'sql': q.sql,
                    'time': round(q.execution_time, 3),
                    'rows': q.rows_affected,
                    'timestamp': q.timestamp.isoformat()
                }
                for q in sorted(self.slow_queries, key=lambda x: x.execution_time, reverse=True)[:limit]
            ]
    
    def get_statistics(self) -> Dict:
        """取得查詢統計"""
        with self._lock:
            if not self.query_history:
                return {'total': 0}
            
            times = [q.execution_time for q in self.query_history]
            return {
                'total': len(self.query_history),
                'slow_count': len(self.slow_queries),
                'avg_time': round(sum(times) / len(times), 4),
                'max_time': round(max(times), 4),
                'min_time': round(min(times), 4),
                'p95_time': round(sorted(times)[int(len(times) * 0.95)] if times else 0, 4)
            }


# 全域查詢分析器
_query_analyzer = QueryAnalyzer()


def timed_query(func: Callable) -> Callable:
    """查詢計時裝飾器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.perf_counter() - start
            # 嘗試提取 SQL
            sql = args[1] if len(args) > 1 else kwargs.get('sql', str(func.__name__))
            _query_analyzer.record_query(str(sql), elapsed)
    return wrapper


# ============================================================
# 3. 索引分析與建議
# ============================================================

class IndexAdvisor:
    """索引建議器"""
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
    
    def analyze_table(self, table_name: str) -> Dict:
        """分析表格索引"""
        c = self.conn.cursor()
        
        # 取得現有索引
        c.execute(f"PRAGMA index_list('{table_name}')")
        indexes = [dict(row) for row in c.fetchall()]
        
        # 取得表格結構
        c.execute(f"PRAGMA table_info('{table_name}')")
        columns = [dict(row) for row in c.fetchall()]
        
        # 取得表格統計
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = c.fetchone()[0]
        
        # 分析索引覆蓋
        indexed_columns = set()
        for idx in indexes:
            c.execute(f"PRAGMA index_info('{idx['name']}')")
            for info in c.fetchall():
                indexed_columns.add(info[2])  # column name
        
        # 建議
        suggestions = []
        
        # 檢查主鍵
        pk_columns = [col['name'] for col in columns if col['pk']]
        
        # 檢查外鍵列（常見命名模式）
        for col in columns:
            name = col['name']
            if name.endswith('_id') and name not in indexed_columns and name not in pk_columns:
                suggestions.append({
                    'type': 'missing_fk_index',
                    'column': name,
                    'reason': '外鍵列建議建立索引',
                    'sql': f"CREATE INDEX idx_{table_name}_{name} ON {table_name}({name})"
                })
        
        # 檢查常見查詢列
        common_search_columns = ['status', 'created_at', 'updated_at', 'type', 'category']
        for col_name in common_search_columns:
            if any(c['name'] == col_name for c in columns) and col_name not in indexed_columns:
                suggestions.append({
                    'type': 'common_column',
                    'column': col_name,
                    'reason': '常見查詢列建議建立索引',
                    'sql': f"CREATE INDEX idx_{table_name}_{col_name} ON {table_name}({col_name})"
                })
        
        return {
            'table': table_name,
            'row_count': row_count,
            'indexes': indexes,
            'columns': [c['name'] for c in columns],
            'indexed_columns': list(indexed_columns),
            'suggestions': suggestions
        }
    
    def analyze_all_tables(self) -> List[Dict]:
        """分析所有表格"""
        c = self.conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in c.fetchall()]
        
        results = []
        for table in tables:
            try:
                results.append(self.analyze_table(table))
            except Exception as e:
                logger.error(f"分析表格 {table} 失敗: {e}")
        
        return results
    
    def get_all_suggestions(self) -> List[Dict]:
        """取得所有索引建議"""
        analyses = self.analyze_all_tables()
        all_suggestions = []
        for analysis in analyses:
            for suggestion in analysis.get('suggestions', []):
                suggestion['table'] = analysis['table']
                all_suggestions.append(suggestion)
        return all_suggestions


# ============================================================
# 4. 批量操作優化
# ============================================================

class BatchExecutor:
    """批量執行器"""
    
    def __init__(self, conn: sqlite3.Connection, batch_size: int = 1000):
        self.conn = conn
        self.batch_size = batch_size
    
    def bulk_insert(self, table: str, columns: List[str], data: List[tuple]) -> int:
        """批量插入
        
        Args:
            table: 表名
            columns: 欄位列表
            data: 數據列表
        
        Returns:
            插入的行數
        """
        if not data:
            return 0
        
        placeholders = ','.join(['?' for _ in columns])
        sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
        
        c = self.conn.cursor()
        total = 0
        
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            c.executemany(sql, batch)
            total += len(batch)
            
            if i % (self.batch_size * 10) == 0:
                self.conn.commit()
        
        self.conn.commit()
        return total
    
    def bulk_update(self, table: str, updates: List[Dict], key_column: str = 'id') -> int:
        """批量更新
        
        Args:
            table: 表名
            updates: 更新列表，每個元素包含 key 和要更新的欄位
            key_column: 主鍵欄位
        
        Returns:
            更新的行數
        """
        if not updates:
            return 0
        
        c = self.conn.cursor()
        total = 0
        
        for update in updates:
            key_value = update.pop(key_column, None)
            if key_value is None:
                continue
            
            set_clause = ','.join([f"{k}=?" for k in update.keys()])
            sql = f"UPDATE {table} SET {set_clause} WHERE {key_column}=?"
            
            c.execute(sql, (*update.values(), key_value))
            total += c.rowcount
            
            if total % self.batch_size == 0:
                self.conn.commit()
        
        self.conn.commit()
        return total
    
    def bulk_delete(self, table: str, ids: List[int], key_column: str = 'id') -> int:
        """批量刪除"""
        if not ids:
            return 0
        
        c = self.conn.cursor()
        total = 0
        
        for i in range(0, len(ids), self.batch_size):
            batch = ids[i:i + self.batch_size]
            placeholders = ','.join(['?' for _ in batch])
            sql = f"DELETE FROM {table} WHERE {key_column} IN ({placeholders})"
            c.execute(sql, batch)
            total += c.rowcount
        
        self.conn.commit()
        return total


# ============================================================
# 5. 效能監控
# ============================================================

class PerformanceMonitor:
    """效能監控器"""
    
    def __init__(self):
        self.metrics = {
            'requests': 0,
            'errors': 0,
            'total_time': 0,
            'db_time': 0
        }
        self._start_time = time.time()
        self._lock = threading.Lock()
    
    def record_request(self, duration: float, is_error: bool = False):
        """記錄請求"""
        with self._lock:
            self.metrics['requests'] += 1
            self.metrics['total_time'] += duration
            if is_error:
                self.metrics['errors'] += 1
    
    def record_db_time(self, duration: float):
        """記錄資料庫時間"""
        with self._lock:
            self.metrics['db_time'] += duration
    
    def get_metrics(self) -> Dict:
        """取得效能指標"""
        uptime = time.time() - self._start_time
        
        with self._lock:
            requests = self.metrics['requests']
            return {
                'uptime_seconds': round(uptime, 2),
                'total_requests': requests,
                'requests_per_second': round(requests / max(uptime, 1), 2),
                'avg_response_time': round(self.metrics['total_time'] / max(requests, 1) * 1000, 2),
                'error_rate': round(self.metrics['errors'] / max(requests, 1) * 100, 2),
                'db_time_pct': round(self.metrics['db_time'] / max(self.metrics['total_time'], 0.001) * 100, 2)
            }
    
    def reset(self):
        """重置指標"""
        with self._lock:
            self.metrics = {
                'requests': 0,
                'errors': 0,
                'total_time': 0,
                'db_time': 0
            }
            self._start_time = time.time()


# 全域效能監控器
_performance_monitor = PerformanceMonitor()


# ============================================================
# 慢查詢記錄器
# ============================================================

class SlowQueryLogger:
    """慢查詢記錄器"""
    
    def __init__(self, threshold_ms: float = 100.0):
        self.threshold_ms = threshold_ms
        self._logs: List[Dict] = []
        self._stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'avg_time_ms': 0.0,
            'max_time_ms': 0.0
        }
    
    def log(self, query: str, duration_ms: float, params: tuple = None):
        """記錄查詢"""
        self._stats['total_queries'] += 1
        
        # 更新平均時間
        total = self._stats['avg_time_ms'] * (self._stats['total_queries'] - 1)
        self._stats['avg_time_ms'] = (total + duration_ms) / self._stats['total_queries']
        
        # 更新最大時間
        if duration_ms > self._stats['max_time_ms']:
            self._stats['max_time_ms'] = duration_ms
        
        # 記錄慢查詢
        if duration_ms >= self.threshold_ms:
            self._stats['slow_queries'] += 1
            self._logs.append({
                'query': query[:200],
                'duration_ms': round(duration_ms, 2),
                'timestamp': datetime.now().isoformat(),
                'params': str(params)[:100] if params else None
            })
            
            # 只保留最近 100 條
            if len(self._logs) > 100:
                self._logs = self._logs[-100:]
    
    def get_stats(self) -> Dict:
        """獲取統計"""
        return {
            **self._stats,
            'slow_rate': round(
                self._stats['slow_queries'] / max(self._stats['total_queries'], 1) * 100, 2
            )
        }
    
    def get_logs(self, limit: int = 50) -> List[Dict]:
        """獲取慢查詢日誌"""
        return self._logs[-limit:]
    
    def clear(self):
        """清除日誌"""
        self._logs = []
        self._stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'avg_time_ms': 0.0,
            'max_time_ms': 0.0
        }


# 全域慢查詢記錄器
slow_query_logger = SlowQueryLogger(threshold_ms=100.0)


def get_performance_dashboard(db_path: str) -> Dict:
    """獲取性能儀表板數據"""
    import os
    import sqlite3
    
    dashboard = {
        'database': {},
        'queries': {},
        'connections': {},
        'recommendations': []
    }
    
    try:
        # 資料庫資訊
        if os.path.exists(db_path):
            stat = os.stat(db_path)
            dashboard['database'] = {
                'path': db_path,
                'size_mb': round(stat.st_size / 1024 / 1024, 2),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
            # 表統計
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            )
            dashboard['database']['table_count'] = cursor.fetchone()[0]
            
            # 索引統計
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
            )
            dashboard['database']['index_count'] = cursor.fetchone()[0]
            conn.close()
        
        # 查詢統計
        dashboard['queries'] = slow_query_logger.get_stats()
        
        # 連接池資訊
        pool = _pools.get(db_path)
        if pool:
            dashboard['connections'] = {
                'pool_size': pool.max_connections,
                'available': pool._pool.qsize() if hasattr(pool._pool, 'qsize') else 'N/A'
            }
        
        # 建議
        if dashboard['queries'].get('slow_rate', 0) > 10:
            dashboard['recommendations'].append('慢查詢比例過高，建議檢查索引')
        
        if dashboard['database'].get('size_mb', 0) > 500:
            dashboard['recommendations'].append('資料庫檔案較大，建議執行 VACUUM')
        
    except Exception as e:
        dashboard['error'] = str(e)
    
    return dashboard


def get_performance_metrics() -> Dict:
    """取得效能指標"""
    return {
        'performance': _performance_monitor.get_metrics(),
        'queries': _query_analyzer.get_statistics(),
        'slow_queries': _query_analyzer.get_slow_queries(10)
    }


# 📚 知識點
# -----------
# 1. 連接池設計：
#    - Queue 實現 FIFO
#    - 懶創建：需要時才創建連接
#    - 上限控制：避免過多連接
#
# 2. SQLite 優化 PRAGMA：
#    - WAL 模式：提高並發性能
#    - cache_size：增加快取
#    - mmap_size：記憶體映射
#
# 3. 查詢分析：
#    - P95 時間：95% 的查詢低於此時間
#    - 慢查詢記錄：定位性能瓶頸
#
# 4. 索引建議：
#    - 外鍵列應建索引
#    - 常見查詢列（status, created_at）
#    - 避免過度索引
#
# 5. 批量操作：
#    - executemany() 比循環 execute() 快
#    - 分批提交避免記憶體爆炸
#    - 定期 commit 平衡性能與安全
