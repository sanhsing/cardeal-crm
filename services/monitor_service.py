"""
車行寶 CRM v5.1 - 監控服務模組
北斗七星文創數位 × 織明

功能：效能指標收集、健康檢查、系統狀態監控
"""
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

import os
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import config

# ===== 指標收集器 =====

class MetricsCollector:
    """效能指標收集器"""
    
    def __init__(self) -> None:
        self.reset()
        self.lock = threading.Lock()
    
    def reset(self) -> None:
        """重設指標"""
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0
        self._response_times = []
        self._status_codes = defaultdict(int)
        self._endpoints = defaultdict(lambda: {'count': 0, 'total_time': 0})
    
    def record_request(self, path, status_code, duration_ms):
        """記錄請求指標"""
        with self.lock:
            self._request_count += 1
            self._response_times.append(duration_ms)
            self._status_codes[status_code] += 1
            
            if status_code >= 400:
                self._error_count += 1
            
            # 端點統計
            endpoint = self._normalize_path(path)
            self._endpoints[endpoint]['count'] += 1
            self._endpoints[endpoint]['total_time'] += duration_ms
    
    def _normalize_path(self, path: Any) -> Any:
        """正規化路徑（去除 ID）"""
        parts = path.split('/')
        normalized = []
        for part in parts:
            if part.isdigit():
                normalized.append('{id}')
            else:
                normalized.append(part)
        return '/'.join(normalized)
    
    def get_metrics(self) -> Dict[str, Any]:
        """取得指標"""
        with self.lock:
            uptime = time.time() - self._start_time
            
            # 計算回應時間統計
            if self._response_times:
                times = sorted(self._response_times)
                avg = sum(times) / len(times)
                p50 = times[len(times) // 2]
                p95 = times[int(len(times) * 0.95)] if len(times) >= 20 else times[-1]
                p99 = times[int(len(times) * 0.99)] if len(times) >= 100 else times[-1]
            else:
                avg = p50 = p95 = p99 = 0
            
            # 計算每分鐘請求數
            rpm = self._request_count / (uptime / 60) if uptime > 0 else 0
            
            # 錯誤率
            error_rate = self._error_count / self._request_count if self._request_count > 0 else 0
            
            # 端點排名
            top_endpoints = sorted(
                self._endpoints.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:10]
            
            return {
                'uptime_seconds': int(uptime),
                'uptime_human': self._format_uptime(uptime),
                'requests': {
                    'total': self._request_count,
                    'rpm': round(rpm, 2),
                    'errors': self._error_count,
                    'error_rate': round(error_rate * 100, 2),
                },
                'response_time_ms': {
                    'avg': round(avg, 2),
                    'p50': round(p50, 2),
                    'p95': round(p95, 2),
                    'p99': round(p99, 2),
                },
                'status_codes': dict(self._status_codes),
                'top_endpoints': [
                    {
                        'path': path,
                        'count': data['count'],
                        'avg_time': round(data['total_time'] / data['count'], 2)
                    }
                    for path, data in top_endpoints
                ]
            }
    
    def _format_uptime(self, seconds: Any) -> Any:
        """格式化運行時間"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f'{days}d')
        if hours > 0:
            parts.append(f'{hours}h')
        parts.append(f'{minutes}m')
        
        return ' '.join(parts)


# ===== 健康檢查 =====

class HealthChecker:
    """健康檢查器"""
    
    def __init__(self) -> None:
        self.checks = {}
        self.register_default_checks()
    
    def register_check(self, name: Any, check_func: Any) -> Any:
        """註冊檢查項目"""
        self.checks[name] = check_func
    
    def register_default_checks(self) -> Any:
        """註冊預設檢查"""
        self.register_check('disk', self._check_disk)
        self.register_check('memory', self._check_memory)
        self.register_check('database', self._check_database)
    
    def run_checks(self) -> None:
        """執行所有檢查"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                result = check_func()
                results[name] = result
                if not result.get('healthy', False):
                    overall_healthy = False
            except Exception as e:
                results[name] = {
                    'healthy': False,
                    'error': str(e)
                }
                overall_healthy = False
        
        return {
            'healthy': overall_healthy,
            'timestamp': datetime.now().isoformat(),
            'checks': results
        }
    
    def _check_disk(self) -> Dict[str, Any]:
        """檢查磁碟空間"""
        try:
            stat = os.statvfs(config.DATA_DIR)
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            used_percent = ((total - free) / total) * 100
            
            return {
                'healthy': used_percent < 90,
                'total_gb': round(total / (1024**3), 2),
                'free_gb': round(free / (1024**3), 2),
                'used_percent': round(used_percent, 2),
                'warning': used_percent >= 80
            }
        except:
            return {'healthy': True, 'note': 'Unable to check disk'}
    
    def _check_memory(self) -> Dict[str, Any]:
        """檢查記憶體"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = {}
                for line in f:
                    parts = line.split(':')
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = int(parts[1].strip().split()[0])
                        meminfo[key] = value
            
            total = meminfo.get('MemTotal', 0)
            free = meminfo.get('MemFree', 0) + meminfo.get('Buffers', 0) + meminfo.get('Cached', 0)
            used_percent = ((total - free) / total) * 100 if total > 0 else 0
            
            return {
                'healthy': used_percent < 90,
                'total_mb': round(total / 1024, 2),
                'free_mb': round(free / 1024, 2),
                'used_percent': round(used_percent, 2)
            }
        except:
            return {'healthy': True, 'note': 'Unable to check memory'}
    
    def _check_database(self) -> Dict[str, Any]:
        """檢查資料庫"""
        try:
            if not os.path.exists(config.MASTER_DB):
                return {'healthy': False, 'error': 'Database not found'}
            
            conn = sqlite3.connect(config.MASTER_DB)
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM tenants')
            tenant_count = c.fetchone()[0]
            
            # 完整性檢查
            c.execute('PRAGMA integrity_check')
            integrity = c.fetchone()[0]
            
            conn.close()
            
            return {
                'healthy': integrity == 'ok',
                'tenant_count': tenant_count,
                'integrity': integrity,
                'size_mb': round(os.path.getsize(config.MASTER_DB) / (1024**2), 2)
            }
        except Exception as e:
            return {'healthy': False, 'error': str(e)}


# ===== 系統狀態 =====

class SystemStatus:
    """系統狀態監控"""
    
    @staticmethod
    def get_status() -> Dict[str, Any]:
        """取得系統狀態"""
        return {
            'app': {
                'name': config.APP_NAME,
                'version': config.VERSION,
                'env': config.ENV,
                'debug': config.DEBUG,
            },
            'server': {
                'host': config.HOST,
                'port': config.PORT,
                'pid': os.getpid(),
            },
            'time': {
                'server_time': datetime.now().isoformat(),
                'timezone': time.tzname[0],
            },
            'python': {
                'version': '.'.join(map(str, __import__('sys').version_info[:3])),
            }
        }


# ===== 全域實例 =====

metrics = MetricsCollector()
health_checker = HealthChecker()


def get_health() -> Dict[str, Any]:
    """取得健康狀態"""
    return health_checker.run_checks()


def get_metrics() -> Dict[str, Any]:
    """取得效能指標"""
    return metrics.get_metrics()


def get_status() -> Dict[str, Any]:
    """取得系統狀態"""
    return SystemStatus.get_status()


def get_full_status() -> Dict[str, Any]:
    """取得完整狀態（健康 + 指標 + 系統）"""
    return {
        'health': get_health(),
        'metrics': get_metrics(),
        'system': get_status()
    }


# 📚 知識點
# -----------
# 1. 百分位數（Percentile）：
#    - p50：中位數，50% 的請求低於此值
#    - p95：95% 的請求低於此值
#    - p99：99% 的請求低於此值
#    - 比平均值更能反映真實體驗
#
# 2. os.statvfs()：
#    - 取得檔案系統統計
#    - f_blocks：總區塊數
#    - f_bavail：可用區塊數
#    - f_frsize：區塊大小
#
# 3. /proc/meminfo：
#    - Linux 記憶體資訊
#    - MemTotal、MemFree、Buffers、Cached
#    - 可用 = Free + Buffers + Cached
#
# 4. 健康檢查設計：
#    - 快速執行（不影響效能）
#    - 涵蓋關鍵資源
#    - 返回可操作的資訊
#
# 5. RPM (Requests Per Minute)：
#    - 每分鐘請求數
#    - 系統吞吐量指標
