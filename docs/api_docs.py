"""
車行寶 CRM v5.1 - API 文件生成器
北斗七星文創數位 × 織明

執行：python docs/api_docs.py > API.md
"""
import json
from datetime import datetime

# ===== API 定義 =====

API_ENDPOINTS = {
    'auth': {
        'name': '認證 API',
        'description': '使用者登入、註冊、登出',
        'endpoints': [
            {
                'method': 'POST',
                'path': '/api/login',
                'name': '登入',
                'auth': False,
                'request': {
                    'code': {'type': 'string', 'required': True, 'desc': '店家代碼'},
                    'phone': {'type': 'string', 'required': True, 'desc': '手機號碼'},
                    'password': {'type': 'string', 'required': True, 'desc': '密碼'},
                },
                'response': {
                    'success': True,
                    'token': 'jwt-token-string',
                    'user_id': 1,
                    'user_name': '使用者名稱',
                    'tenant_id': 1,
                    'tenant_name': '店家名稱',
                }
            },
            {
                'method': 'POST',
                'path': '/api/register',
                'name': '註冊',
                'auth': False,
                'request': {
                    'code': {'type': 'string', 'required': True, 'desc': '店家代碼（3-20字元，小寫英數字）'},
                    'name': {'type': 'string', 'required': True, 'desc': '店家名稱'},
                    'phone': {'type': 'string', 'required': True, 'desc': '管理員手機'},
                    'password': {'type': 'string', 'required': True, 'desc': '密碼（至少4字元）'},
                },
                'response': {
                    'success': True,
                    'tenant_id': 1,
                }
            },
            {
                'method': 'POST',
                'path': '/api/logout',
                'name': '登出',
                'auth': True,
                'request': {},
                'response': {'success': True}
            },
            {
                'method': 'GET',
                'path': '/api/me',
                'name': '取得當前使用者',
                'auth': True,
                'request': {},
                'response': {
                    'success': True,
                    'user': {
                        'user_id': 1,
                        'user_name': '使用者名稱',
                        'role': 'admin',
                        'tenant_name': '店家名稱',
                    }
                }
            },
        ]
    },
    'customers': {
        'name': '客戶 API',
        'description': '客戶資料的 CRUD 操作',
        'endpoints': [
            {
                'method': 'GET',
                'path': '/api/customers',
                'name': '客戶列表',
                'auth': True,
                'request': {
                    'search': {'type': 'string', 'required': False, 'desc': '搜尋關鍵字'},
                    'status': {'type': 'string', 'required': False, 'desc': '狀態（active/deleted）'},
                    'level': {'type': 'string', 'required': False, 'desc': '等級（vip/normal/potential/cold）'},
                    'limit': {'type': 'int', 'required': False, 'desc': '每頁筆數（預設50）'},
                    'offset': {'type': 'int', 'required': False, 'desc': '偏移量'},
                },
                'response': {
                    'success': True,
                    'customers': [{'id': 1, 'name': '...'}],
                    'total': 100,
                }
            },
            {
                'method': 'GET',
                'path': '/api/customers/{id}',
                'name': '客戶詳情',
                'auth': True,
                'request': {},
                'response': {
                    'success': True,
                    'customer': {'id': 1, 'name': '...', 'followups': [], 'deals': []},
                }
            },
            {
                'method': 'POST',
                'path': '/api/customers',
                'name': '新增客戶',
                'auth': True,
                'request': {
                    'name': {'type': 'string', 'required': True, 'desc': '客戶姓名'},
                    'phone': {'type': 'string', 'required': False, 'desc': '手機號碼'},
                    'email': {'type': 'string', 'required': False, 'desc': 'Email'},
                    'source': {'type': 'string', 'required': False, 'desc': '來源'},
                    'level': {'type': 'string', 'required': False, 'desc': '等級'},
                    'notes': {'type': 'string', 'required': False, 'desc': '備註'},
                },
                'response': {
                    'success': True,
                    'id': 1,
                }
            },
            {
                'method': 'POST',
                'path': '/api/customers/{id}/update',
                'name': '更新客戶',
                'auth': True,
                'request': {
                    'name': {'type': 'string', 'required': False, 'desc': '客戶姓名'},
                    'phone': {'type': 'string', 'required': False, 'desc': '手機號碼'},
                    'level': {'type': 'string', 'required': False, 'desc': '等級'},
                },
                'response': {'success': True}
            },
            {
                'method': 'POST',
                'path': '/api/customers/{id}/delete',
                'name': '刪除客戶',
                'auth': True,
                'request': {},
                'response': {'success': True}
            },
        ]
    },
    'vehicles': {
        'name': '車輛 API',
        'description': '車輛庫存的 CRUD 操作',
        'endpoints': [
            {
                'method': 'GET',
                'path': '/api/vehicles',
                'name': '車輛列表',
                'auth': True,
                'request': {
                    'search': {'type': 'string', 'required': False, 'desc': '搜尋關鍵字'},
                    'status': {'type': 'string', 'required': False, 'desc': '狀態（in_stock/reserved/sold）'},
                    'brand': {'type': 'string', 'required': False, 'desc': '品牌'},
                },
                'response': {
                    'success': True,
                    'vehicles': [{'id': 1, 'brand': 'Toyota', 'model': 'Altis'}],
                    'total': 50,
                }
            },
            {
                'method': 'POST',
                'path': '/api/vehicles',
                'name': '新增車輛',
                'auth': True,
                'request': {
                    'brand': {'type': 'string', 'required': True, 'desc': '品牌'},
                    'model': {'type': 'string', 'required': True, 'desc': '型號'},
                    'year': {'type': 'int', 'required': False, 'desc': '年份'},
                    'plate': {'type': 'string', 'required': False, 'desc': '車牌'},
                    'mileage': {'type': 'int', 'required': False, 'desc': '里程'},
                    'purchase_price': {'type': 'int', 'required': False, 'desc': '購入價'},
                    'repair_cost': {'type': 'int', 'required': False, 'desc': '整備費'},
                    'asking_price': {'type': 'int', 'required': False, 'desc': '定價'},
                },
                'response': {'success': True, 'id': 1}
            },
        ]
    },
    'deals': {
        'name': '交易 API',
        'description': '交易記錄管理',
        'endpoints': [
            {
                'method': 'GET',
                'path': '/api/deals',
                'name': '交易列表',
                'auth': True,
                'request': {
                    'deal_type': {'type': 'string', 'required': False, 'desc': '類型（buy/sell）'},
                    'start_date': {'type': 'string', 'required': False, 'desc': '開始日期'},
                    'end_date': {'type': 'string', 'required': False, 'desc': '結束日期'},
                },
                'response': {
                    'success': True,
                    'deals': [{'id': 1, 'deal_type': 'sell', 'amount': 600000}],
                }
            },
            {
                'method': 'POST',
                'path': '/api/deals',
                'name': '新增交易',
                'auth': True,
                'request': {
                    'deal_type': {'type': 'string', 'required': True, 'desc': '類型（buy/sell）'},
                    'customer_id': {'type': 'int', 'required': True, 'desc': '客戶 ID'},
                    'vehicle_id': {'type': 'int', 'required': True, 'desc': '車輛 ID'},
                    'amount': {'type': 'int', 'required': True, 'desc': '金額'},
                    'deal_date': {'type': 'string', 'required': False, 'desc': '交易日期'},
                },
                'response': {'success': True, 'id': 1}
            },
        ]
    },
    'reports': {
        'name': '報表 API',
        'description': '統計與報表',
        'endpoints': [
            {
                'method': 'GET',
                'path': '/api/stats',
                'name': '統計數據',
                'auth': True,
                'request': {},
                'response': {
                    'success': True,
                    'stats': {
                        'customer_count': 100,
                        'vehicle_in_stock': 20,
                        'revenue_this_month': 1200000,
                        'profit_this_month': 150000,
                    }
                }
            },
            {
                'method': 'GET',
                'path': '/api/reports/sales',
                'name': '銷售報表',
                'auth': True,
                'request': {
                    'start': {'type': 'string', 'required': False, 'desc': '開始日期'},
                    'end': {'type': 'string', 'required': False, 'desc': '結束日期'},
                },
                'response': {
                    'success': True,
                    'report': {'daily': {}, 'totals': {}}
                }
            },
        ]
    },
}

# ===== 文件生成 =====

def generate_markdown():
    """生成 Markdown 格式文件"""
    lines = []
    
    # 標題
    lines.append('# 車行寶 CRM API 文件')
    lines.append('')
    lines.append(f'> 版本：5.1.0 | 更新時間：{datetime.now().strftime("%Y-%m-%d")}')
    lines.append('')
    
    # 目錄
    lines.append('## 目錄')
    lines.append('')
    for key, group in API_ENDPOINTS.items():
        lines.append(f'- [{group["name"]}](#{key})')
    lines.append('')
    
    # 通用說明
    lines.append('## 通用說明')
    lines.append('')
    lines.append('### 認證')
    lines.append('需要認證的 API 需在 Header 帶上 Token：')
    lines.append('```')
    lines.append('Authorization: Bearer <token>')
    lines.append('```')
    lines.append('')
    lines.append('### 回應格式')
    lines.append('所有 API 回應皆為 JSON 格式，包含 `success` 欄位：')
    lines.append('```json')
    lines.append('// 成功')
    lines.append('{"success": true, "data": ...}')
    lines.append('')
    lines.append('// 失敗')
    lines.append('{"success": false, "error": "錯誤訊息"}')
    lines.append('```')
    lines.append('')
    
    # 各 API 群組
    for key, group in API_ENDPOINTS.items():
        lines.append(f'## {group["name"]} {{{key}}}')
        lines.append('')
        lines.append(group['description'])
        lines.append('')
        
        for ep in group['endpoints']:
            lines.append(f'### {ep["name"]}')
            lines.append('')
            lines.append(f'`{ep["method"]} {ep["path"]}`')
            lines.append('')
            lines.append(f'認證：{"需要" if ep["auth"] else "不需要"}')
            lines.append('')
            
            # 請求參數
            if ep['request']:
                lines.append('**請求參數：**')
                lines.append('')
                lines.append('| 參數 | 類型 | 必填 | 說明 |')
                lines.append('|------|------|:----:|------|')
                for param, info in ep['request'].items():
                    required = '是' if info.get('required') else '否'
                    lines.append(f'| {param} | {info["type"]} | {required} | {info["desc"]} |')
                lines.append('')
            
            # 回應範例
            lines.append('**回應範例：**')
            lines.append('')
            lines.append('```json')
            lines.append(json.dumps(ep['response'], indent=2, ensure_ascii=False))
            lines.append('```')
            lines.append('')
            lines.append('---')
            lines.append('')
    
    return '\n'.join(lines)


def generate_html():
    """生成 HTML 格式文件"""
    md_content = generate_markdown()
    
    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>車行寶 CRM API 文件</title>
    <style>
        body {{ font-family: 'Noto Sans TC', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1e3a5f; }}
        h2 {{ color: #2d4a6f; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
        h3 {{ color: #ee6c4d; }}
        code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }}
        pre {{ background: #1e293b; color: #e2e8f0; padding: 15px; border-radius: 8px; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 10px; text-align: left; }}
        th {{ background: #f8fafc; }}
        blockquote {{ border-left: 4px solid #ee6c4d; padding-left: 15px; color: #64748b; }}
    </style>
</head>
<body>
    <pre>{md_content}</pre>
</body>
</html>'''
    
    return html


if __name__ == '__main__':
    print(generate_markdown())


# 📚 知識點
# -----------
# 1. API 文件規範：
#    - 清楚的端點說明
#    - 請求/回應範例
#    - 錯誤碼說明
#
# 2. 資料驅動文件：
#    - API 定義存成資料結構
#    - 自動生成文件
#    - 保持文件與程式同步
#
# 3. json.dumps 格式化：
#    - indent=2：縮排2空格
#    - ensure_ascii=False：保留中文
#
# 4. Markdown 格式：
#    - 通用、易讀
#    - 可轉換為 HTML
#    - GitHub 友好
