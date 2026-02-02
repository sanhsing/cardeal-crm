"""
車行寶 CRM v5.1 - 系統管理 API Handler
北斗七星文創數位 × 織明

API 端點：
- /api/system/health - 健康檢查
- /api/system/status - 系統狀態
- /api/system/performance - 性能指標
- /api/system/security - 安全狀態
- /api/system/audit - 審計日誌
- /api/system/docs - API 文檔
"""
from typing import Dict, List, Any, Optional, Union, Callable

import json
import time
import os
from datetime import datetime
from handlers.base import BaseHandler
from services import (
    cache_service,
    security_service,
)
from services.security_middleware import (
    rate_limiter, audit_logger, ip_blacklist, 
    sql_injection_detector, security_middleware
)
from services.performance_service import (
    get_pool, slow_query_logger, QueryAnalyzer,
    get_performance_dashboard
)
import config


class SystemHandler(BaseHandler):
    """系統管理 API Handler"""
    
    def handle_request(self, method: str, path: str, params: dict = None):
        """處理請求"""
        params = params or {}
        
        # 健康檢查（公開）
        if path == '/api/system/health':
            return self._health_check()
        
        # 以下需要管理員權限
        # TODO: 添加權限檢查
        
        if path == '/api/system/status':
            return self._system_status()
        
        if path == '/api/system/performance':
            return self._performance_metrics()
        
        if path == '/api/system/security':
            return self._security_status()
        
        if path == '/api/system/audit':
            return self._audit_logs(params)
        
        if path == '/api/system/cache':
            if method == 'DELETE':
                return self._clear_cache()
            return self._cache_stats()
        
        if path == '/api/system/slow-queries':
            return self._slow_queries()
        
        if path == '/api/system/index-suggestions':
            return self._index_suggestions()
        
        if path == '/api/system/docs':
            return self._api_docs()
        
        return self.error_response(404, 'Not Found')
    
    # ============================================================
    # 健康檢查
    # ============================================================
    
    def _health_check(self):
        """健康檢查"""
        checks = {}
        overall_healthy = True
        
        # 1. 資料庫連接
        try:
            import sqlite3
            conn = sqlite3.connect(config.MASTER_DB)
            conn.execute("SELECT 1")
            conn.close()
            checks['database'] = {'status': 'ok'}
        except Exception as e:
            checks['database'] = {'status': 'error', 'message': str(e)}
            overall_healthy = False
        
        # 2. 快取服務
        try:
            cache_service.cache_set('health_check', 'ok', ttl=10)
            result = cache_service.cache_get('health_check')
            checks['cache'] = {'status': 'ok' if result == 'ok' else 'degraded'}
        except Exception as e:
            checks['cache'] = {'status': 'error', 'message': str(e)}
        
        # 3. 磁碟空間
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_pct = free / total * 100
            checks['disk'] = {
                'status': 'ok' if free_pct > 10 else 'warning',
                'free_pct': round(free_pct, 1)
            }
            if free_pct < 5:
                overall_healthy = False
        except Exception as e:
            checks['disk'] = {'status': 'unknown'}
        
        # 4. 記憶體（如果有 psutil）
        try:
            import psutil
            mem = psutil.virtual_memory()
            checks['memory'] = {
                'status': 'ok' if mem.percent < 90 else 'warning',
                'used_pct': mem.percent
            }
        except ImportError:
            checks['memory'] = {'status': 'unknown', 'message': 'psutil not installed'}
        
        return self.json_response({
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'version': '5.1.0',
            'checks': checks
        })
    
    # ============================================================
    # 系統狀態
    # ============================================================
    
    def _system_status(self):
        """完整系統狀態"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'version': '5.1.0',
            'uptime': self._get_uptime(),
        }
        
        # 資料庫統計
        try:
            analyzer = QueryAnalyzer(config.MASTER_DB)
            table_stats = analyzer.table_stats()
            total_rows = sum(t['rows'] for t in table_stats)
            analyzer.close()
            
            status['database'] = {
                'tables': len(table_stats),
                'total_rows': total_rows,
                'top_tables': table_stats[:5]
            }
        except Exception as e:
            status['database'] = {'error': str(e)}
        
        # 快取統計
        status['cache'] = cache_service.cache_stats()
        
        # 限流統計
        status['rate_limiter'] = {
            'rules': rate_limiter.rules
        }
        
        # 安全統計
        status['security'] = {
            'blocked_ips': len(ip_blacklist.get_blocked_list().get('permanent', [])),
            'temp_blocked': len(ip_blacklist.get_blocked_list().get('temporary', {}))
        }
        
        return self.json_response(status)
    
    def _get_uptime(self) -> str:
        """取得運行時間"""
        # 簡化版：返回啟動時間
        return datetime.now().isoformat()
    
    # ============================================================
    # 性能指標
    # ============================================================
    
    def _performance_metrics(self):
        """性能指標"""
        try:
            dashboard = get_performance_dashboard(config.MASTER_DB)
            return self.json_response({
                'success': True,
                'data': dashboard
            })
        except Exception as e:
            return self.json_response({
                'success': False,
                'error': str(e)
            })
    
    def _slow_queries(self):
        """慢查詢日誌"""
        return self.json_response({
            'success': True,
            'stats': slow_query_logger.get_stats(),
            'logs': slow_query_logger.get_logs(50)
        })
    
    def _index_suggestions(self):
        """索引建議"""
        try:
            analyzer = QueryAnalyzer(config.MASTER_DB)
            suggestions = analyzer.suggest_indexes()
            analyzer.close()
            
            return self.json_response({
                'success': True,
                'count': len(suggestions),
                'suggestions': suggestions
            })
        except Exception as e:
            return self.json_response({
                'success': False,
                'error': str(e)
            })
    
    # ============================================================
    # 安全狀態
    # ============================================================
    
    def _security_status(self):
        """安全狀態"""
        return self.json_response({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'rate_limiter': {
                'rules': rate_limiter.rules
            },
            'ip_blacklist': ip_blacklist.get_blocked_list(),
            'sql_injection': {
                'recent_attacks': sql_injection_detector.get_attack_logs(10)
            },
            'audit': audit_logger.get_stats()
        })
    
    def _audit_logs(self, params: dict):
        """審計日誌查詢"""
        event_type = params.get('event_type')
        user_id = params.get('user_id')
        risk_level = params.get('risk_level')
        limit = int(params.get('limit', 100))
        
        logs = audit_logger.query(
            event_type=event_type,
            user_id=int(user_id) if user_id else None,
            risk_level=risk_level,
            limit=limit
        )
        
        return self.json_response({
            'success': True,
            'count': len(logs),
            'stats': audit_logger.get_stats(),
            'logs': logs
        })
    
    # ============================================================
    # 快取管理
    # ============================================================
    
    def _cache_stats(self):
        """快取統計"""
        return self.json_response({
            'success': True,
            'stats': cache_service.cache_stats()
        })
    
    def _clear_cache(self):
        """清除快取"""
        cache_service.cache_clear()
        return self.json_response({
            'success': True,
            'message': '快取已清除'
        })
    
    # ============================================================
    # API 文檔
    # ============================================================
    
    def _api_docs(self):
        """API 文檔"""
        docs = {
            'version': '5.1.0',
            'base_url': '/api',
            'endpoints': [
                # 認證
                {'method': 'POST', 'path': '/api/auth/login', 'description': '用戶登入'},
                {'method': 'POST', 'path': '/api/auth/logout', 'description': '用戶登出'},
                {'method': 'POST', 'path': '/api/auth/register', 'description': '用戶註冊'},
                
                # 車輛
                {'method': 'GET', 'path': '/api/vehicles', 'description': '車輛列表'},
                {'method': 'POST', 'path': '/api/vehicles', 'description': '新增車輛'},
                {'method': 'GET', 'path': '/api/vehicles/{id}', 'description': '車輛詳情'},
                {'method': 'PUT', 'path': '/api/vehicles/{id}', 'description': '更新車輛'},
                {'method': 'DELETE', 'path': '/api/vehicles/{id}', 'description': '刪除車輛'},
                
                # 客戶
                {'method': 'GET', 'path': '/api/customers', 'description': '客戶列表'},
                {'method': 'POST', 'path': '/api/customers', 'description': '新增客戶'},
                {'method': 'GET', 'path': '/api/customers/{id}', 'description': '客戶詳情'},
                {'method': 'PUT', 'path': '/api/customers/{id}', 'description': '更新客戶'},
                
                # 交易
                {'method': 'GET', 'path': '/api/deals', 'description': '交易列表'},
                {'method': 'POST', 'path': '/api/deals', 'description': '新增交易'},
                {'method': 'GET', 'path': '/api/deals/{id}', 'description': '交易詳情'},
                
                # AI
                {'method': 'GET', 'path': '/api/ai/intent/{id}', 'description': '客戶意向分析'},
                {'method': 'GET', 'path': '/api/ai/scripts/{id}', 'description': '銷售話術'},
                {'method': 'GET', 'path': '/api/ai/recommend/{id}', 'description': '車輛推薦'},
                {'method': 'GET', 'path': '/api/ai/alerts', 'description': '庫存預警'},
                {'method': 'GET', 'path': '/api/ai/predict', 'description': '業績預測'},
                
                # 報表
                {'method': 'GET', 'path': '/api/reports/daily', 'description': '日報'},
                {'method': 'GET', 'path': '/api/reports/weekly', 'description': '週報'},
                {'method': 'GET', 'path': '/api/reports/monthly', 'description': '月報'},
                {'method': 'GET', 'path': '/api/reports/leaderboard', 'description': '排行榜'},
                {'method': 'GET', 'path': '/api/reports/export', 'description': 'Excel 匯出'},
                
                # 系統
                {'method': 'GET', 'path': '/api/system/health', 'description': '健康檢查'},
                {'method': 'GET', 'path': '/api/system/status', 'description': '系統狀態'},
                {'method': 'GET', 'path': '/api/system/performance', 'description': '性能指標'},
                {'method': 'GET', 'path': '/api/system/security', 'description': '安全狀態'},
                {'method': 'GET', 'path': '/api/system/audit', 'description': '審計日誌'},
            ]
        }
        
        return self.json_response(docs)


# 路由註冊
def register_routes(router):
    """註冊系統管理路由"""
    handler = SystemHandler()
    
    routes = [
        ('GET', '/api/system/health'),
        ('GET', '/api/system/status'),
        ('GET', '/api/system/performance'),
        ('GET', '/api/system/security'),
        ('GET', '/api/system/audit'),
        ('GET', '/api/system/cache'),
        ('DELETE', '/api/system/cache'),
        ('GET', '/api/system/slow-queries'),
        ('GET', '/api/system/index-suggestions'),
        ('GET', '/api/system/docs'),
    ]
    
    for method, path in routes:
        router.add_route(method, path, handler.handle_request)


# 📚 知識點
# -----------
# 1. 健康檢查設計：
#    - 多維度檢查：DB、快取、磁碟、記憶體
#    - 狀態分級：ok / warning / error
#    - 整體狀態判斷
#
# 2. 系統監控：
#    - 資料庫統計：表數、行數
#    - 快取統計：命中率、大小
#    - 安全統計：封鎖數、攻擊數
#
# 3. API 文檔：
#    - 自描述 API
#    - 結構化輸出
#    - 方便前端使用
#
# 4. 權限控制：
#    - 健康檢查公開（負載均衡用）
#    - 其他需要管理員權限
