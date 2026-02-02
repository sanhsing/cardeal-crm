"""
車行寶 CRM v5.2 - 監控服務
北斗七星文創數位 × 織明

功能：
1. 系統指標收集
2. 請求追蹤
3. 效能分析
4. 健康檢查
5. 警報機制
"""
import os
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import deque
import logging

logger = logging.getLogger(__name__)


# ============================================================
# 1. 指標定義
# ============================================================

@dataclass
class Metric:
    """指標數據"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags
        }


@dataclass
class RequestTrace:
    """請求追蹤"""
    request_id: str
    method: str
    path: str
    start_time: float
    end_time: float = 0
    status_code: int = 0
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0
    
    def to_dict(self) -> Dict:
        return {
            'request_id': self.request_id,
            'method': self.method,
            'path': self.path,
            'duration_ms': round(self.duration_ms, 2),
            'status_code': self.status_code,
            'error': self.error
        }


# ============================================================
# 2. 指標收集器
# ============================================================

class MetricsCollector:
    """指標收集器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics: Dict[str, deque] = {}
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def record(self, name: str, value: float, tags: Dict[str, str] = None):
        """記錄指標"""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = deque(maxlen=self.max_history)
            
            metric = Metric(name=name, value=value, tags=tags or {})
            self._metrics[name].append(metric)
    
    def increment(self, name: str, value: int = 1):
        """計數器增加"""
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value
    
    def gauge(self, name: str, value: float):
        """設置即時值"""
        with self._lock:
            self._gauges[name] = value
    
    def get_counter(self, name: str) -> int:
        """獲取計數器值"""
        return self._counters.get(name, 0)
    
    def get_gauge(self, name: str) -> float:
        """獲取即時值"""
        return self._gauges.get(name, 0.0)
    
    def get_metrics(self, name: str, limit: int = 100) -> List[Dict]:
        """獲取指標歷史"""
        metrics = self._metrics.get(name, [])
        return [m.to_dict() for m in list(metrics)[-limit:]]
    
    def get_summary(self, name: str) -> Dict:
        """獲取指標摘要"""
        metrics = self._metrics.get(name, [])
        if not metrics:
            return {'count': 0}
        
        values = [m.value for m in metrics]
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': values[-1] if values else 0
        }
    
    def get_all_summaries(self) -> Dict:
        """獲取所有指標摘要"""
        return {
            name: self.get_summary(name)
            for name in self._metrics.keys()
        }


# 全域指標收集器
metrics = MetricsCollector()


# ============================================================
# 3. 請求追蹤器
# ============================================================

class RequestTracer:
    """請求追蹤器"""
    
    def __init__(self, max_traces: int = 500):
        self.max_traces = max_traces
        self._traces: deque = deque(maxlen=max_traces)
        self._active: Dict[str, RequestTrace] = {}
        self._lock = threading.Lock()
    
    def start(self, request_id: str, method: str, path: str) -> RequestTrace:
        """開始追蹤"""
        trace = RequestTrace(
            request_id=request_id,
            method=method,
            path=path,
            start_time=time.time()
        )
        with self._lock:
            self._active[request_id] = trace
        return trace
    
    def end(self, request_id: str, status_code: int, error: str = None):
        """結束追蹤"""
        with self._lock:
            trace = self._active.pop(request_id, None)
            if trace:
                trace.end_time = time.time()
                trace.status_code = status_code
                trace.error = error
                self._traces.append(trace)
                
                # 記錄指標
                metrics.record('request_duration_ms', trace.duration_ms, {
                    'method': trace.method,
                    'path': trace.path
                })
                metrics.increment('request_total')
                if status_code >= 400:
                    metrics.increment('request_errors')
    
    def get_recent(self, limit: int = 50) -> List[Dict]:
        """獲取最近的追蹤"""
        return [t.to_dict() for t in list(self._traces)[-limit:]]
    
    def get_slow_requests(self, threshold_ms: float = 500, limit: int = 20) -> List[Dict]:
        """獲取慢請求"""
        slow = [t for t in self._traces if t.duration_ms >= threshold_ms]
        return [t.to_dict() for t in sorted(slow, key=lambda x: -x.duration_ms)[:limit]]
    
    def get_stats(self) -> Dict:
        """獲取統計"""
        traces = list(self._traces)
        if not traces:
            return {'total': 0}
        
        durations = [t.duration_ms for t in traces]
        errors = sum(1 for t in traces if t.status_code >= 400)
        
        return {
            'total': len(traces),
            'errors': errors,
            'error_rate': round(errors / len(traces) * 100, 2),
            'avg_duration_ms': round(sum(durations) / len(durations), 2),
            'max_duration_ms': round(max(durations), 2),
            'p95_duration_ms': round(sorted(durations)[int(len(durations) * 0.95)], 2) if len(durations) >= 20 else None
        }


# 全域請求追蹤器
tracer = RequestTracer()


# ============================================================
# 4. 系統監控
# ============================================================

class SystemMonitor:
    """系統監控"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self._start_time = time.time()
    
    def get_uptime(self) -> Dict:
        """獲取運行時間"""
        uptime_seconds = time.time() - self._start_time
        return {
            'seconds': int(uptime_seconds),
            'human': self._format_duration(uptime_seconds)
        }
    
    def get_memory(self) -> Dict:
        """獲取記憶體使用"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem = process.memory_info()
            return {
                'rss_mb': round(mem.rss / 1024 / 1024, 2),
                'vms_mb': round(mem.vms / 1024 / 1024, 2)
            }
        except ImportError:
            return {'error': 'psutil not installed'}
    
    def get_cpu(self) -> Dict:
        """獲取 CPU 使用"""
        try:
            import psutil
            return {
                'percent': psutil.cpu_percent(interval=0.1),
                'count': psutil.cpu_count()
            }
        except ImportError:
            return {'error': 'psutil not installed'}
    
    def get_disk(self) -> Dict:
        """獲取磁碟使用"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return {
                'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
                'used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
                'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                'percent': disk.percent
            }
        except ImportError:
            return {'error': 'psutil not installed'}
    
    def get_database(self) -> Dict:
        """獲取資料庫狀態"""
        if not self.db_path or not os.path.exists(self.db_path):
            return {'error': 'Database not found'}
        
        try:
            stat = os.stat(self.db_path)
            conn = sqlite3.connect(self.db_path)
            
            # 表數量
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            )
            table_count = cursor.fetchone()[0]
            
            # 索引數量
            cursor = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
            )
            index_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'size_mb': round(stat.st_size / 1024 / 1024, 2),
                'tables': table_count,
                'indexes': index_count,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _format_duration(self, seconds: float) -> str:
        """格式化時間"""
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return ' '.join(parts)


# ============================================================
# 5. 監控儀表板
# ============================================================

def get_dashboard(db_path: str = None) -> Dict:
    """獲取監控儀表板"""
    monitor = SystemMonitor(db_path)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'uptime': monitor.get_uptime(),
        'system': {
            'memory': monitor.get_memory(),
            'cpu': monitor.get_cpu(),
            'disk': monitor.get_disk()
        },
        'database': monitor.get_database(),
        'requests': tracer.get_stats(),
        'metrics': {
            'request_total': metrics.get_counter('request_total'),
            'request_errors': metrics.get_counter('request_errors'),
            'summaries': metrics.get_all_summaries()
        }
    }


def get_health_check(db_path: str = None) -> Dict:
    """健康檢查"""
    checks = {}
    healthy = True
    
    # 資料庫檢查
    if db_path and os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            conn.execute("SELECT 1")
            conn.close()
            checks['database'] = 'ok'
        except Exception as e:
            checks['database'] = f'error: {e}'
            healthy = False
    else:
        checks['database'] = 'not configured'
    
    # 磁碟檢查
    try:
        import psutil
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            checks['disk'] = f'warning: {disk.percent}% used'
        else:
            checks['disk'] = 'ok'
    except ImportError:
        checks['disk'] = 'psutil not installed'
    
    # 記憶體檢查
    try:
        import psutil
        mem = psutil.virtual_memory()
        if mem.percent > 90:
            checks['memory'] = f'warning: {mem.percent}% used'
        else:
            checks['memory'] = 'ok'
    except ImportError:
        checks['memory'] = 'psutil not installed'
    
    return {
        'status': 'healthy' if healthy else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.now().isoformat()
    }


# 📚 知識點
# -----------
# 1. 指標類型：Counter（計數器）、Gauge（即時值）、Histogram（分布）
# 2. 請求追蹤：記錄每個請求的完整生命週期
# 3. P95/P99：百分位數，衡量請求延遲分布
# 4. 健康檢查：定期檢查系統各組件狀態
# 5. deque：固定長度隊列，自動淘汰舊數據
