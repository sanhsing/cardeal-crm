"""
車行寶 CRM v5.1 - API 文檔與健康檢查
北斗七星文創數位 × 織明

功能：
1. API 文檔自動生成
2. 健康檢查增強
3. 系統狀態監控
"""
import sqlite3
import time
import os
import json
from datetime import datetime
from typing import Dict, List, Optional


# ============================================================
# 1. API 文檔自動生成
# ============================================================

class APIDocGenerator:
    """API 文檔生成器"""
    
    def __init__(self):
        self.endpoints = []
    
    def register(self, method: str, path: str, handler: str,
                 description: str = "", params: Dict = None,
                 response: Dict = None, auth_required: bool = True):
        """註冊 API 端點"""
        self.endpoints.append({
            'method': method,
            'path': path,
            'handler': handler,
            'description': description,
            'params': params or {},
            'response': response or {},
            'auth_required': auth_required
        })
    
    def generate_markdown(self) -> str:
        """生成 Markdown 格式文檔"""
        lines = [
            "# 車行寶 CRM API 文檔",
            "",
            f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 目錄",
            ""
        ]
        
        # 按類別分組
        categories = {}
        for ep in self.endpoints:
            path_parts = ep['path'].split('/')
            category = path_parts[2] if len(path_parts) > 2 else 'other'
            if category not in categories:
                categories[category] = []
            categories[category].append(ep)
        
        # 目錄
        for cat in sorted(categories.keys()):
            lines.append(f"- [{cat.upper()}](#{cat})")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 詳細文檔
        for cat in sorted(categories.keys()):
            lines.append(f"## {cat.upper()}")
            lines.append("")
            
            for ep in categories[cat]:
                lines.append(f"### `{ep['method']}` {ep['path']}")
                lines.append("")
                lines.append(ep['description'] or "*無描述*")
                lines.append("")
                
                # 認證
                if ep['auth_required']:
                    lines.append("🔒 **需要認證**")
                    lines.append("")
                
                # 參數
                if ep['params']:
                    lines.append("**參數:**")
                    lines.append("")
                    lines.append("| 名稱 | 類型 | 必填 | 說明 |")
                    lines.append("|------|------|:----:|------|")
                    for name, info in ep['params'].items():
                        required = "✓" if info.get('required') else ""
                        lines.append(f"| {name} | {info.get('type', 'string')} | {required} | {info.get('description', '')} |")
                    lines.append("")
                
                # 響應
                if ep['response']:
                    lines.append("**響應:**")
                    lines.append("")
                    lines.append("```json")
                    lines.append(json.dumps(ep['response'], indent=2, ensure_ascii=False))
                    lines.append("```")
                    lines.append("")
                
                lines.append("---")
                lines.append("")
        
        return "\n".join(lines)
    
    def generate_openapi(self) -> Dict:
        """生成 OpenAPI 3.0 格式"""
        paths = {}
        
        for ep in self.endpoints:
            path = ep['path']
            method = ep['method'].lower()
            
            if path not in paths:
                paths[path] = {}
            
            operation = {
                'summary': ep['description'],
                'responses': {
                    '200': {
                        'description': '成功',
                        'content': {
                            'application/json': {
                                'schema': {'type': 'object'}
                            }
                        }
                    }
                }
            }
            
            # 參數
            if ep['params']:
                operation['parameters'] = []
                for name, info in ep['params'].items():
                    operation['parameters'].append({
                        'name': name,
                        'in': 'query',
                        'required': info.get('required', False),
                        'schema': {'type': info.get('type', 'string')},
                        'description': info.get('description', '')
                    })
            
            # 認證
            if ep['auth_required']:
                operation['security'] = [{'bearerAuth': []}]
            
            paths[path][method] = operation
        
        return {
            'openapi': '3.0.0',
            'info': {
                'title': '車行寶 CRM API',
                'version': '5.1.0',
                'description': '車行寶 CRM 系統 API 文檔'
            },
            'servers': [
                {'url': '/api', 'description': '生產環境'}
            ],
            'paths': paths,
            'components': {
                'securitySchemes': {
                    'bearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer'
                    }
                }
            }
        }


# 預設 API 文檔
_api_doc = APIDocGenerator()

# 註冊所有 API
def _register_all_apis():
    """註冊所有 API 端點"""
    
    # ===== 認證 =====
    _api_doc.register('POST', '/api/auth/login', 'auth_handler',
        description='用戶登入',
        params={
            'username': {'type': 'string', 'required': True, 'description': '用戶名'},
            'password': {'type': 'string', 'required': True, 'description': '密碼'}
        },
        response={'success': True, 'token': 'xxx', 'user': {}},
        auth_required=False)
    
    _api_doc.register('POST', '/api/auth/logout', 'auth_handler',
        description='用戶登出')
    
    _api_doc.register('GET', '/api/auth/me', 'auth_handler',
        description='取得當前用戶資訊')
    
    # ===== 車輛 =====
    _api_doc.register('GET', '/api/vehicles', 'vehicle_handler',
        description='取得車輛列表',
        params={
            'status': {'type': 'string', 'description': '狀態篩選'},
            'brand': {'type': 'string', 'description': '品牌篩選'},
            'page': {'type': 'integer', 'description': '頁碼'},
            'limit': {'type': 'integer', 'description': '每頁數量'}
        })
    
    _api_doc.register('GET', '/api/vehicles/{id}', 'vehicle_handler',
        description='取得單一車輛詳情')
    
    _api_doc.register('POST', '/api/vehicles', 'vehicle_handler',
        description='新增車輛')
    
    _api_doc.register('PUT', '/api/vehicles/{id}', 'vehicle_handler',
        description='更新車輛')
    
    _api_doc.register('DELETE', '/api/vehicles/{id}', 'vehicle_handler',
        description='刪除車輛')
    
    # ===== 客戶 =====
    _api_doc.register('GET', '/api/customers', 'customer_handler',
        description='取得客戶列表')
    
    _api_doc.register('GET', '/api/customers/{id}', 'customer_handler',
        description='取得單一客戶詳情')
    
    _api_doc.register('POST', '/api/customers', 'customer_handler',
        description='新增客戶')
    
    _api_doc.register('PUT', '/api/customers/{id}', 'customer_handler',
        description='更新客戶')
    
    # ===== 交易 =====
    _api_doc.register('GET', '/api/deals', 'deal_handler',
        description='取得交易列表')
    
    _api_doc.register('POST', '/api/deals', 'deal_handler',
        description='新增交易')
    
    _api_doc.register('PUT', '/api/deals/{id}', 'deal_handler',
        description='更新交易')
    
    # ===== AI =====
    _api_doc.register('GET', '/api/ai/intent/{customer_id}', 'ai_report_handler',
        description='客戶意向分析',
        response={'success': True, 'score': 75, 'level': 'warm', 'suggestion': '...'})
    
    _api_doc.register('GET', '/api/ai/scripts/{vehicle_id}', 'ai_report_handler',
        description='銷售話術建議')
    
    _api_doc.register('GET', '/api/ai/recommend/{customer_id}', 'ai_report_handler',
        description='智能車輛推薦')
    
    _api_doc.register('GET', '/api/ai/alerts', 'ai_report_handler',
        description='庫存預警')
    
    _api_doc.register('GET', '/api/ai/predict', 'ai_report_handler',
        description='業績預測')
    
    # ===== 報表 =====
    _api_doc.register('GET', '/api/reports/daily', 'ai_report_handler',
        description='日報',
        params={'date': {'type': 'string', 'description': 'YYYY-MM-DD 格式'}})
    
    _api_doc.register('GET', '/api/reports/weekly', 'ai_report_handler',
        description='週報')
    
    _api_doc.register('GET', '/api/reports/monthly', 'ai_report_handler',
        description='月報',
        params={'month': {'type': 'string', 'description': 'YYYY-MM 格式'}})
    
    _api_doc.register('GET', '/api/reports/leaderboard', 'ai_report_handler',
        description='業績排行榜',
        params={'period': {'type': 'string', 'description': 'day/week/month/year'}})
    
    _api_doc.register('GET', '/api/reports/export', 'ai_report_handler',
        description='報表 Excel 匯出')
    
    # ===== 健康檢查 =====
    _api_doc.register('GET', '/api/health', 'health_handler',
        description='系統健康檢查',
        auth_required=False)
    
    _api_doc.register('GET', '/api/health/detailed', 'health_handler',
        description='詳細健康檢查')
    
    _api_doc.register('GET', '/api/metrics', 'health_handler',
        description='系統指標')

_register_all_apis()


def get_api_doc_markdown() -> str:
    """取得 Markdown 格式 API 文檔"""
    return _api_doc.generate_markdown()


def get_api_doc_openapi() -> Dict:
    """取得 OpenAPI 格式文檔"""
    return _api_doc.generate_openapi()


# ============================================================
# 2. 健康檢查增強
# ============================================================

class HealthChecker:
    """健康檢查器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self._start_time = time.time()
    
    def check_database(self) -> Dict:
        """檢查資料庫"""
        if not self.db_path or not os.path.exists(self.db_path):
            return {'status': 'error', 'message': '資料庫不存在'}
        
        try:
            start = time.perf_counter()
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.execute("SELECT 1")
            conn.close()
            latency = (time.perf_counter() - start) * 1000
            
            return {
                'status': 'healthy',
                'latency_ms': round(latency, 2),
                'size_mb': round(os.path.getsize(self.db_path) / 1024 / 1024, 2)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def check_disk(self) -> Dict:
        """檢查磁碟空間"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            return {
                'status': 'healthy' if free > 1024 * 1024 * 100 else 'warning',
                'total_gb': round(total / 1024 / 1024 / 1024, 2),
                'used_gb': round(used / 1024 / 1024 / 1024, 2),
                'free_gb': round(free / 1024 / 1024 / 1024, 2),
                'used_pct': round(used / total * 100, 1)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def check_memory(self) -> Dict:
        """檢查記憶體"""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return {
                'status': 'healthy' if mem.percent < 90 else 'warning',
                'total_gb': round(mem.total / 1024 / 1024 / 1024, 2),
                'used_gb': round(mem.used / 1024 / 1024 / 1024, 2),
                'available_gb': round(mem.available / 1024 / 1024 / 1024, 2),
                'used_pct': mem.percent
            }
        except ImportError:
            return {'status': 'unknown', 'message': 'psutil 未安裝'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def check_cpu(self) -> Dict:
        """檢查 CPU"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            return {
                'status': 'healthy' if cpu_percent < 80 else 'warning',
                'usage_pct': cpu_percent,
                'cores': psutil.cpu_count()
            }
        except ImportError:
            return {'status': 'unknown', 'message': 'psutil 未安裝'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_uptime(self) -> Dict:
        """取得運行時間"""
        uptime_seconds = time.time() - self._start_time
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return {
            'seconds': int(uptime_seconds),
            'human': f"{days}d {hours}h {minutes}m"
        }
    
    def quick_check(self) -> Dict:
        """快速健康檢查"""
        db = self.check_database()
        
        return {
            'status': 'healthy' if db['status'] == 'healthy' else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'version': '5.1.0',
            'database': db['status']
        }
    
    def detailed_check(self) -> Dict:
        """詳細健康檢查"""
        checks = {
            'database': self.check_database(),
            'disk': self.check_disk(),
            'memory': self.check_memory(),
            'cpu': self.check_cpu()
        }
        
        # 整體狀態
        statuses = [c['status'] for c in checks.values()]
        if 'error' in statuses:
            overall = 'unhealthy'
        elif 'warning' in statuses:
            overall = 'degraded'
        else:
            overall = 'healthy'
        
        return {
            'status': overall,
            'timestamp': datetime.now().isoformat(),
            'version': '5.1.0',
            'uptime': self.get_uptime(),
            'checks': checks
        }


# ============================================================
# 3. 系統指標
# ============================================================

def get_system_metrics(db_path: str = None) -> Dict:
    """取得系統指標"""
    from services.performance_service import get_performance_metrics, get_pool
    
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'performance': get_performance_metrics()
    }
    
    # 連接池狀態
    if db_path:
        try:
            pool = get_pool(db_path)
            metrics['connection_pool'] = pool.get_stats()
        except:
            pass
    
    return metrics


# 📚 知識點
# -----------
# 1. OpenAPI 規範：
#    - 標準化 API 文檔格式
#    - 可自動生成客戶端
#    - Swagger UI 可視化
#
# 2. 健康檢查設計：
#    - /health 端點：快速檢查（供負載均衡器）
#    - /health/detailed：詳細診斷
#    - 分級狀態：healthy/degraded/unhealthy
#
# 3. psutil 系統監控：
#    - 跨平台系統資源監控
#    - CPU、記憶體、磁碟使用率
#    - 需額外安裝：pip install psutil
#
# 4. 運行時間計算：
#    - 記錄啟動時間
#    - 計算差值並格式化
#    - 常見於監控面板
