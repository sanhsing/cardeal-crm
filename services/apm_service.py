"""
車行寶 CRM v5.2 - APM 應用效能監控服務
北斗七星文創數位 × 織明

功能：
1. 分散式追蹤 (Tracing)
2. 效能指標 (Metrics)
3. 日誌聚合 (Logging)
4. 錯誤追蹤 (Error Tracking)
5. 告警機制 (Alerting)
"""
import time
import uuid
import threading
import logging
import functools
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
from contextlib import contextmanager

logger = logging.getLogger(__name__)


# ============================================================
# 1. Span 定義（追蹤單元）
# ============================================================

@dataclass
class Span:
    """追蹤 Span"""
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    operation: str
    service: str = 'cardeal-crm'
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: str = 'ok'
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict] = field(default_factory=list)
    
    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0
    
    def set_tag(self, key: str, value: str) -> 'Span':
        """設置標籤"""
        self.tags[key] = value
        return self
    
    def log(self, event: str, **kwargs) -> 'Span':
        """記錄事件"""
        self.logs.append({
            'timestamp': datetime.now().isoformat(),
            'event': event,
            **kwargs
        })
        return self
    
    def finish(self, status: str = 'ok') -> None:
        """結束 Span"""
        self.end_time = time.time()
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_id': self.parent_id,
            'operation': self.operation,
            'service': self.service,
            'duration_ms': round(self.duration_ms, 2),
            'status': self.status,
            'tags': self.tags,
            'logs': self.logs,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat()
        }


# ============================================================
# 2. Tracer 追蹤器
# ============================================================

class Tracer:
    """分散式追蹤器"""
    
    def __init__(self, service_name: str = 'cardeal-crm', max_spans: int = 1000):
        self.service_name = service_name
        self.max_spans = max_spans
        self._spans: deque = deque(maxlen=max_spans)
        self._active_spans: Dict[str, Span] = {}
        self._current_trace: threading.local = threading.local()
        self._lock = threading.Lock()
    
    def start_span(
        self, 
        operation: str, 
        parent: Optional[Span] = None,
        tags: Dict[str, str] = None
    ) -> Span:
        """開始新 Span"""
        trace_id = parent.trace_id if parent else uuid.uuid4().hex[:16]
        span_id = uuid.uuid4().hex[:16]
        parent_id = parent.span_id if parent else None
        
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_id=parent_id,
            operation=operation,
            service=self.service_name,
            tags=tags or {}
        )
        
        with self._lock:
            self._active_spans[span_id] = span
        
        return span
    
    def finish_span(self, span: Span, status: str = 'ok') -> None:
        """結束 Span"""
        span.finish(status)
        
        with self._lock:
            self._active_spans.pop(span.span_id, None)
            self._spans.append(span)
    
    @contextmanager
    def trace(self, operation: str, **tags):
        """追蹤上下文管理器"""
        span = self.start_span(operation, tags=tags)
        try:
            yield span
            self.finish_span(span, 'ok')
        except Exception as e:
            span.set_tag('error', str(e))
            span.log('exception', message=str(e), type=type(e).__name__)
            self.finish_span(span, 'error')
            raise
    
    def get_traces(self, limit: int = 100) -> List[Dict]:
        """獲取追蹤記錄"""
        return [s.to_dict() for s in list(self._spans)[-limit:]]
    
    def get_trace(self, trace_id: str) -> List[Dict]:
        """獲取特定 Trace"""
        return [
            s.to_dict() for s in self._spans 
            if s.trace_id == trace_id
        ]


# 全域追蹤器
tracer = Tracer()


# ============================================================
# 3. Metrics 指標
# ============================================================

class MetricsRegistry:
    """指標註冊器"""
    
    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
    
    def counter(self, name: str, value: int = 1, labels: Dict[str, str] = None) -> None:
        """計數器"""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + value
    
    def gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """即時值"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
    
    def histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """直方圖"""
        key = self._make_key(name, labels)
        with self._lock:
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
            # 只保留最近 1000 個
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """生成指標 Key"""
        if not labels:
            return name
        label_str = ','.join(f'{k}={v}' for k, v in sorted(labels.items()))
        return f'{name}{{{label_str}}}'
    
    def get_all(self) -> Dict[str, Any]:
        """獲取所有指標"""
        with self._lock:
            result = {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {}
            }
            
            for key, values in self._histograms.items():
                if values:
                    sorted_vals = sorted(values)
                    result['histograms'][key] = {
                        'count': len(values),
                        'sum': sum(values),
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'p50': sorted_vals[len(values) // 2],
                        'p95': sorted_vals[int(len(values) * 0.95)] if len(values) >= 20 else None,
                        'p99': sorted_vals[int(len(values) * 0.99)] if len(values) >= 100 else None
                    }
            
            return result


# 全域指標註冊器
metrics = MetricsRegistry()


# ============================================================
# 4. 告警規則
# ============================================================

@dataclass
class AlertRule:
    """告警規則"""
    name: str
    metric: str
    condition: str  # >, <, >=, <=, ==
    threshold: float
    duration: int = 60  # 秒
    severity: str = 'warning'  # warning, critical
    callback: Optional[Callable] = None


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self._rules: List[AlertRule] = []
        self._alerts: deque = deque(maxlen=100)
        self._lock = threading.Lock()
    
    def add_rule(self, rule: AlertRule) -> None:
        """添加告警規則"""
        self._rules.append(rule)
    
    def check(self, metrics_data: Dict[str, Any]) -> List[Dict]:
        """檢查告警"""
        alerts = []
        
        for rule in self._rules:
            value = self._get_metric_value(metrics_data, rule.metric)
            if value is None:
                continue
            
            triggered = self._evaluate(value, rule.condition, rule.threshold)
            
            if triggered:
                alert = {
                    'rule': rule.name,
                    'metric': rule.metric,
                    'value': value,
                    'threshold': rule.threshold,
                    'severity': rule.severity,
                    'timestamp': datetime.now().isoformat()
                }
                alerts.append(alert)
                
                with self._lock:
                    self._alerts.append(alert)
                
                if rule.callback:
                    try:
                        rule.callback(alert)
                    except Exception as e:
                        logger.error(f"Alert callback error: {e}")
        
        return alerts
    
    def _get_metric_value(self, data: Dict, metric: str) -> Optional[float]:
        """獲取指標值"""
        parts = metric.split('.')
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current if isinstance(current, (int, float)) else None
    
    def _evaluate(self, value: float, condition: str, threshold: float) -> bool:
        """評估條件"""
        ops = {
            '>': lambda v, t: v > t,
            '<': lambda v, t: v < t,
            '>=': lambda v, t: v >= t,
            '<=': lambda v, t: v <= t,
            '==': lambda v, t: v == t,
        }
        return ops.get(condition, lambda v, t: False)(value, threshold)
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """獲取告警歷史"""
        return list(self._alerts)[-limit:]


# 全域告警管理器
alerts = AlertManager()


# ============================================================
# 5. 裝飾器
# ============================================================

def traced(operation: str = None):
    """追蹤裝飾器"""
    def decorator(func: Callable) -> Callable:
        op_name = operation or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.trace(op_name) as span:
                span.set_tag('function', func.__name__)
                result = func(*args, **kwargs)
                return result
        
        return wrapper
    return decorator


def timed(metric_name: str = None):
    """計時裝飾器"""
    def decorator(func: Callable) -> Callable:
        name = metric_name or f'{func.__module__}.{func.__name__}'
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                metrics.counter(f'{name}_total')
                return result
            except Exception:
                metrics.counter(f'{name}_errors')
                raise
            finally:
                duration = (time.time() - start) * 1000
                metrics.histogram(f'{name}_duration_ms', duration)
        
        return wrapper
    return decorator


# ============================================================
# 6. APM Dashboard
# ============================================================

def get_apm_dashboard() -> Dict[str, Any]:
    """獲取 APM 儀表板"""
    return {
        'timestamp': datetime.now().isoformat(),
        'traces': {
            'recent': tracer.get_traces(20),
            'count': len(tracer._spans)
        },
        'metrics': metrics.get_all(),
        'alerts': {
            'recent': alerts.get_alerts(10),
            'rules': len(alerts._rules)
        }
    }


# ============================================================
# 7. 預設告警規則
# ============================================================

def setup_default_alerts() -> None:
    """設置預設告警規則"""
    from services import telegram_service
    
    def notify_alert(alert: Dict) -> None:
        """通知告警"""
        msg = f"⚠️ 告警: {alert['rule']}\n"
        msg += f"指標: {alert['metric']} = {alert['value']}\n"
        msg += f"閾值: {alert['threshold']}\n"
        msg += f"等級: {alert['severity']}"
        telegram_service.send_message(msg)
    
    # 錯誤率告警
    alerts.add_rule(AlertRule(
        name='高錯誤率',
        metric='counters.request_errors',
        condition='>',
        threshold=100,
        severity='warning',
        callback=notify_alert
    ))
    
    # 響應時間告警
    alerts.add_rule(AlertRule(
        name='響應延遲',
        metric='histograms.request_duration_ms.p95',
        condition='>',
        threshold=1000,
        severity='warning',
        callback=notify_alert
    ))


# 📚 知識點
# -----------
# 1. Span：追蹤的基本單位，代表一個操作
# 2. Trace：由多個 Span 組成的調用鏈
# 3. Context Manager：使用 with 語句自動管理追蹤
# 4. Histogram：用於計算 P50/P95/P99 百分位數
# 5. Alert Rule：定義告警條件和回調
