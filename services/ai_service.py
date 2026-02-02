"""
車行寶 CRM v5.1 - AI 智能服務模組
北斗七星文創數位 × 織明

功能：
1. 客戶意向分析（購買可能性預測）
2. 銷售話術建議
3. 智能車輛推薦
4. 庫存預警分析
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from models import get_connection


# ============================================================
# 1. 客戶意向分析
# ============================================================

def analyze_customer_intent(db_path: str, customer_id: int) -> Dict:
    """分析客戶購買意向
    
    評分維度：
    - 互動頻率（近30天聯繫次數）
    - 看車次數
    - 詢價行為
    - 客戶等級
    - 最近互動時間
    
    Returns:
        {
            score: 0-100,
            level: 'hot'/'warm'/'cold',
            factors: {...},
            suggestion: '...'
        }
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 取得客戶基本資訊
    c.execute('''
        SELECT id, name, level, source, created_at,
               (SELECT MAX(created_at) FROM customer_logs WHERE customer_id = customers.id) as last_contact
        FROM customers WHERE id = ?
    ''', (customer_id,))
    customer = c.fetchone()
    
    if not customer:
        conn.close()
        return {'success': False, 'error': '客戶不存在'}
    
    # 計算各維度分數
    scores = {}
    
    # 1. 互動頻率（近30天）
    c.execute('''
        SELECT COUNT(*) as count FROM customer_logs 
        WHERE customer_id = ? AND created_at >= date('now', '-30 days')
    ''', (customer_id,))
    contact_count = c.fetchone()['count']
    scores['interaction'] = min(30, contact_count * 5)  # 最高30分
    
    # 2. 看車記錄
    c.execute('''
        SELECT COUNT(*) as count FROM customer_logs 
        WHERE customer_id = ? AND log_type = 'view_vehicle'
    ''', (customer_id,))
    view_count = c.fetchone()['count']
    scores['vehicle_views'] = min(20, view_count * 4)  # 最高20分
    
    # 3. 詢價記錄
    c.execute('''
        SELECT COUNT(*) as count FROM customer_logs 
        WHERE customer_id = ? AND log_type = 'price_inquiry'
    ''', (customer_id,))
    inquiry_count = c.fetchone()['count']
    scores['price_inquiry'] = min(25, inquiry_count * 5)  # 最高25分
    
    # 4. 客戶等級
    level_scores = {'vip': 15, 'normal': 10, 'potential': 5, 'cold': 0}
    scores['customer_level'] = level_scores.get(customer['level'], 5)
    
    # 5. 最近互動時間
    if customer['last_contact']:
        last_contact = datetime.fromisoformat(customer['last_contact'])
        days_since = (datetime.now() - last_contact).days
        if days_since <= 3:
            scores['recency'] = 10
        elif days_since <= 7:
            scores['recency'] = 7
        elif days_since <= 14:
            scores['recency'] = 4
        else:
            scores['recency'] = 0
    else:
        scores['recency'] = 0
    
    conn.close()
    
    # 計算總分
    total_score = sum(scores.values())
    
    # 判斷意向等級
    if total_score >= 70:
        intent_level = 'hot'
        suggestion = '高意向客戶！建議立即跟進，提供專屬優惠促成交易'
    elif total_score >= 40:
        intent_level = 'warm'
        suggestion = '中等意向，建議持續保持聯繫，了解需求並推薦合適車款'
    else:
        intent_level = 'cold'
        suggestion = '意向較低，建議定期發送促銷資訊，維持關係'
    
    return {
        'success': True,
        'customer_id': customer_id,
        'customer_name': customer['name'],
        'score': total_score,
        'level': intent_level,
        'factors': {
            'interaction': {'score': scores['interaction'], 'max': 30, 'desc': '互動頻率'},
            'vehicle_views': {'score': scores['vehicle_views'], 'max': 20, 'desc': '看車次數'},
            'price_inquiry': {'score': scores['price_inquiry'], 'max': 25, 'desc': '詢價次數'},
            'customer_level': {'score': scores['customer_level'], 'max': 15, 'desc': '客戶等級'},
            'recency': {'score': scores['recency'], 'max': 10, 'desc': '最近互動'}
        },
        'suggestion': suggestion
    }


def batch_analyze_intent(db_path: str, limit: int = 50) -> List[Dict]:
    """批量分析客戶意向，返回熱門潛客"""
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''
        SELECT id FROM customers 
        WHERE status = 'active' 
        ORDER BY updated_at DESC 
        LIMIT ?
    ''', (limit,))
    
    customers = c.fetchall()
    conn.close()
    
    results = []
    for cust in customers:
        analysis = analyze_customer_intent(db_path, cust['id'])
        if analysis.get('success'):
            results.append(analysis)
    
    # 按意向分數排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results


# ============================================================
# 2. 銷售話術建議
# ============================================================

def get_sales_scripts(db_path: str, vehicle_id: int, customer_id: Optional[int] = None) -> Dict:
    """生成銷售話術建議
    
    根據車輛特點和客戶需求生成話術
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 取得車輛資訊
    c.execute('''
        SELECT brand, model, year, mileage, color, asking_price, 
               purchase_date, total_cost, features, condition_note
        FROM vehicles WHERE id = ?
    ''', (vehicle_id,))
    vehicle = c.fetchone()
    
    if not vehicle:
        conn.close()
        return {'success': False, 'error': '車輛不存在'}
    
    scripts = []
    
    # 1. 開場白
    age = datetime.now().year - int(vehicle['year'])
    if age <= 2:
        scripts.append({
            'type': 'opening',
            'title': '新車優勢',
            'script': f"這台 {vehicle['year']} 年的 {vehicle['brand']} {vehicle['model']}，"
                     f"才 {age} 年的車，車況非常新，幾乎跟新車一樣，但價格更實惠！"
        })
    elif age <= 5:
        scripts.append({
            'type': 'opening',
            'title': '黃金車齡',
            'script': f"這台 {vehicle['brand']} {vehicle['model']} 是 {vehicle['year']} 年份，"
                     f"正好是黃金車齡，該有的毛病都修過了，接下來會非常穩定。"
        })
    
    # 2. 里程話術
    mileage = int(vehicle['mileage'] or 0)
    yearly_avg = mileage / max(age, 1)
    if yearly_avg < 10000:
        scripts.append({
            'type': 'mileage',
            'title': '低里程優勢',
            'script': f"這台車里程只有 {mileage:,} 公里，平均一年才跑 {int(yearly_avg):,} 公里，"
                     f"屬於非常愛惜的用車方式，引擎和底盤都保養得很好。"
        })
    elif yearly_avg < 15000:
        scripts.append({
            'type': 'mileage',
            'title': '正常里程',
            'script': f"這台車里程 {mileage:,} 公里，平均一年 {int(yearly_avg):,} 公里，"
                     f"屬於正常使用，機件都在最佳狀態。"
        })
    
    # 3. 價格話術
    asking = vehicle['asking_price'] or 0
    cost = vehicle['total_cost'] or 0
    margin = asking - cost if cost > 0 else 0
    
    # 計算議價空間
    min_price = cost + (margin * 0.3) if margin > 0 else asking * 0.95
    
    scripts.append({
        'type': 'price',
        'title': '價格說明',
        'script': f"這台車開價 {asking:,} 元，這個價格已經是市場行情價了。"
                 f"如果您今天能決定，我可以幫您爭取一些優惠。",
        'internal_note': f"底價約 {int(min_price):,} 元，利潤空間 {int(margin):,} 元"
    })
    
    # 4. 品牌話術
    brand_scripts = {
        'toyota': "Toyota 的妥善率是業界公認最高的，養車成本低，二手也保值。",
        'honda': "Honda 的引擎技術是出了名的，省油又耐用，開個十幾年都沒問題。",
        'mazda': "Mazda 的操控和外型是日系車裡最有歐洲風味的，開起來很有樂趣。",
        'lexus': "Lexus 的品質和服務都是頂級的，買 Lexus 就是買一個放心。",
        'bmw': "BMW 的駕駛體驗是無可比擬的，真正懂車的人都會選 BMW。",
        'benz': "Mercedes-Benz 的品牌價值和舒適度，是成功人士的首選。"
    }
    brand_lower = vehicle['brand'].lower()
    if brand_lower in brand_scripts:
        scripts.append({
            'type': 'brand',
            'title': '品牌優勢',
            'script': brand_scripts[brand_lower]
        })
    
    # 5. 促成話術
    scripts.append({
        'type': 'closing',
        'title': '促成交易',
        'script': "這台車詢問度很高，已經有好幾組客人在看了。"
                 "如果您喜歡，建議今天先付訂金保留，避免被別人搶走。"
    })
    
    # 6. 異議處理
    scripts.append({
        'type': 'objection',
        'title': '價格異議處理',
        'script': "我理解您想要更好的價格，但這台車的車況和配備真的很超值。"
                 "這樣好了，我幫您問問老闆，看能不能再優惠一點。"
    })
    
    conn.close()
    
    return {
        'success': True,
        'vehicle': {
            'id': vehicle_id,
            'brand': vehicle['brand'],
            'model': vehicle['model'],
            'year': vehicle['year']
        },
        'scripts': scripts
    }


# ============================================================
# 3. 智能車輛推薦
# ============================================================

def recommend_vehicles(db_path: str, customer_id: int, limit: int = 5) -> Dict:
    """根據客戶歷史行為推薦車輛
    
    分析：
    - 過去看過的車款
    - 詢價記錄
    - 預算範圍
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 取得客戶偏好
    c.execute('''
        SELECT v.brand, v.model, v.year, v.asking_price
        FROM customer_logs cl
        JOIN vehicles v ON cl.vehicle_id = v.id
        WHERE cl.customer_id = ? 
          AND cl.log_type IN ('view_vehicle', 'price_inquiry')
        ORDER BY cl.created_at DESC
        LIMIT 10
    ''', (customer_id,))
    
    history = c.fetchall()
    
    if not history:
        # 無歷史記錄，推薦熱門車款
        c.execute('''
            SELECT v.*, COUNT(cl.id) as interest_count
            FROM vehicles v
            LEFT JOIN customer_logs cl ON v.id = cl.vehicle_id
            WHERE v.status = 'in_stock'
            GROUP BY v.id
            ORDER BY interest_count DESC
            LIMIT ?
        ''', (limit,))
        recommendations = c.fetchall()
        conn.close()
        
        return {
            'success': True,
            'type': 'popular',
            'reason': '根據熱門車款推薦',
            'recommendations': [dict(r) for r in recommendations]
        }
    
    # 分析偏好
    brands = {}
    price_sum = 0
    price_count = 0
    
    for h in history:
        brand = h['brand']
        brands[brand] = brands.get(brand, 0) + 1
        if h['asking_price']:
            price_sum += h['asking_price']
            price_count += 1
    
    # 取得偏好品牌
    preferred_brands = sorted(brands.keys(), key=lambda x: brands[x], reverse=True)[:3]
    
    # 計算預算範圍
    if price_count > 0:
        avg_price = price_sum / price_count
        min_price = avg_price * 0.7
        max_price = avg_price * 1.3
    else:
        min_price = 0
        max_price = 9999999
    
    # 推薦相似車款
    placeholders = ','.join(['?' for _ in preferred_brands])
    c.execute(f'''
        SELECT * FROM vehicles
        WHERE status = 'in_stock'
          AND brand IN ({placeholders})
          AND asking_price BETWEEN ? AND ?
        ORDER BY 
            CASE WHEN brand = ? THEN 0 ELSE 1 END,
            asking_price
        LIMIT ?
    ''', (*preferred_brands, min_price, max_price, preferred_brands[0] if preferred_brands else '', limit))
    
    recommendations = c.fetchall()
    conn.close()
    
    return {
        'success': True,
        'type': 'personalized',
        'reason': f"根據您偏好的 {', '.join(preferred_brands[:2])} 品牌推薦",
        'preferences': {
            'brands': preferred_brands,
            'price_range': {'min': int(min_price), 'max': int(max_price)}
        },
        'recommendations': [dict(r) for r in recommendations]
    }


# ============================================================
# 4. 庫存預警分析
# ============================================================

def analyze_inventory_alerts(db_path: str) -> Dict:
    """分析庫存預警
    
    預警類型：
    - 滯銷車輛（>90天未售）
    - 高詢問低成交
    - 價格偏離市場
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    alerts = []
    
    # 1. 滯銷車輛
    c.execute('''
        SELECT id, brand, model, year, asking_price, purchase_date,
               julianday('now') - julianday(purchase_date) as days_in_stock
        FROM vehicles
        WHERE status = 'in_stock'
          AND julianday('now') - julianday(purchase_date) > 90
        ORDER BY days_in_stock DESC
    ''')
    slow_moving = c.fetchall()
    
    for v in slow_moving:
        alerts.append({
            'type': 'slow_moving',
            'severity': 'high' if v['days_in_stock'] > 120 else 'medium',
            'vehicle_id': v['id'],
            'vehicle': f"{v['brand']} {v['model']} {v['year']}",
            'days_in_stock': int(v['days_in_stock']),
            'asking_price': v['asking_price'],
            'suggestion': f"庫存已 {int(v['days_in_stock'])} 天，建議降價 5-10% 促銷"
        })
    
    # 2. 高詢問低成交
    c.execute('''
        SELECT v.id, v.brand, v.model, v.year, v.asking_price,
               COUNT(cl.id) as inquiry_count
        FROM vehicles v
        LEFT JOIN customer_logs cl ON v.id = cl.vehicle_id AND cl.log_type = 'price_inquiry'
        WHERE v.status = 'in_stock'
        GROUP BY v.id
        HAVING inquiry_count >= 5
        ORDER BY inquiry_count DESC
    ''')
    high_inquiry = c.fetchall()
    
    for v in high_inquiry:
        alerts.append({
            'type': 'high_inquiry_no_sale',
            'severity': 'medium',
            'vehicle_id': v['id'],
            'vehicle': f"{v['brand']} {v['model']} {v['year']}",
            'inquiry_count': v['inquiry_count'],
            'asking_price': v['asking_price'],
            'suggestion': f"已有 {v['inquiry_count']} 次詢價但未成交，建議檢視定價或車況說明"
        })
    
    # 3. 即將到期車輛（如有貸款或租賃）
    c.execute('''
        SELECT id, brand, model, year, asking_price,
               julianday('now') - julianday(purchase_date) as days_in_stock
        FROM vehicles
        WHERE status = 'in_stock'
          AND julianday('now') - julianday(purchase_date) > 60
          AND julianday('now') - julianday(purchase_date) <= 90
        ORDER BY days_in_stock DESC
    ''')
    approaching = c.fetchall()
    
    for v in approaching:
        alerts.append({
            'type': 'approaching_threshold',
            'severity': 'low',
            'vehicle_id': v['id'],
            'vehicle': f"{v['brand']} {v['model']} {v['year']}",
            'days_in_stock': int(v['days_in_stock']),
            'suggestion': f"庫存 {int(v['days_in_stock'])} 天，即將進入滯銷期，建議加強推廣"
        })
    
    conn.close()
    
    # 統計
    summary = {
        'total_alerts': len(alerts),
        'high_severity': len([a for a in alerts if a['severity'] == 'high']),
        'medium_severity': len([a for a in alerts if a['severity'] == 'medium']),
        'low_severity': len([a for a in alerts if a['severity'] == 'low'])
    }
    
    return {
        'success': True,
        'summary': summary,
        'alerts': alerts
    }


# ============================================================
# 5. 業績預測
# ============================================================

def predict_monthly_sales(db_path: str) -> Dict:
    """預測本月業績
    
    基於：
    - 歷史同期數據
    - 當月已完成數據
    - 進行中的交易
    """
    conn = get_connection(db_path)
    c = conn.cursor()
    
    today = datetime.now()
    current_month = today.strftime('%Y-%m')
    days_passed = today.day
    days_in_month = 30  # 簡化
    
    # 當月已完成
    c.execute('''
        SELECT SUM(amount) as revenue, SUM(profit) as profit, COUNT(*) as count
        FROM deals
        WHERE deal_type = 'sell' AND status = 'completed'
          AND strftime('%Y-%m', deal_date) = ?
    ''', (current_month,))
    current = c.fetchone()
    current_revenue = current['revenue'] or 0
    current_profit = current['profit'] or 0
    current_count = current['count'] or 0
    
    # 進行中的交易
    c.execute('''
        SELECT SUM(amount) as revenue, COUNT(*) as count
        FROM deals
        WHERE status = 'pending'
    ''')
    pending = c.fetchone()
    pending_revenue = pending['revenue'] or 0
    pending_count = pending['count'] or 0
    
    # 歷史同期（去年同月）
    last_year_month = f"{today.year - 1}-{today.strftime('%m')}"
    c.execute('''
        SELECT SUM(amount) as revenue, SUM(profit) as profit, COUNT(*) as count
        FROM deals
        WHERE deal_type = 'sell' AND status = 'completed'
          AND strftime('%Y-%m', deal_date) = ?
    ''', (last_year_month,))
    historical = c.fetchone()
    
    conn.close()
    
    # 預測計算
    # 方法：線性外推 + 進行中交易的50%
    daily_avg = current_revenue / max(days_passed, 1)
    projected_revenue = daily_avg * days_in_month + pending_revenue * 0.5
    
    # 與去年比較
    historical_revenue = historical['revenue'] or 0
    if historical_revenue > 0:
        yoy_growth = (projected_revenue - historical_revenue) / historical_revenue * 100
    else:
        yoy_growth = 0
    
    return {
        'success': True,
        'current_month': current_month,
        'days_passed': days_passed,
        'current': {
            'revenue': current_revenue,
            'profit': current_profit,
            'count': current_count
        },
        'pending': {
            'revenue': pending_revenue,
            'count': pending_count
        },
        'prediction': {
            'revenue': int(projected_revenue),
            'daily_avg': int(daily_avg),
            'confidence': 'medium' if days_passed >= 15 else 'low'
        },
        'comparison': {
            'last_year_revenue': historical_revenue,
            'yoy_growth': round(yoy_growth, 1)
        }
    }


# 📚 知識點
# -----------
# 1. 意向評分模型：
#    - 多維度加權評分
#    - 每個維度設定上限避免單一維度主導
#    - 最終得分映射到等級
#
# 2. 推薦演算法：
#    - 基於歷史行為（協同過濾思想）
#    - 偏好萃取：品牌、價格範圍
#    - 冷啟動：使用熱門推薦
#
# 3. 預測方法：
#    - 線性外推（當月數據）
#    - 加入進行中交易的折扣預期
#    - 信心度根據已過天數調整
#
# 4. SQL 技巧：
#    - CASE WHEN 條件排序
#    - HAVING 過濾分組結果
#    - julianday() 計算天數差
