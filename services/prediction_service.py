#!/usr/bin/env python3
"""
prediction_service.py - 車行寶 AI 銷售預測服務
PYLIB: L3-prediction-service
Version: v1.0.0
Created: 2026-02-03

功能：
1. 銷售趨勢預測
2. 客戶成交概率
3. 庫存周轉預測
4. 價格建議
5. 需求預測
"""

import math
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import sqlite3

# ============================================================
# L0: 基礎常量
# ============================================================

VERSION = "1.0.0"

# 預測模型參數
FORECAST_HORIZONS = {
    "week": 7,
    "month": 30,
    "quarter": 90,
}

# 客戶狀態權重（用於成交概率計算）
STATUS_WEIGHTS = {
    "potential": 0.1,
    "contacted": 0.2,
    "interested": 0.4,
    "negotiating": 0.7,
    "deal": 1.0,
    "lost": 0.0,
}

# 季節性因子（月份 -> 係數）
SEASONALITY = {
    1: 0.85,   # 農曆新年前淡季
    2: 0.75,   # 農曆新年
    3: 1.05,   # 開春旺季
    4: 1.10,
    5: 1.00,
    6: 0.95,
    7: 0.90,   # 暑假淡季
    8: 0.90,
    9: 1.05,   # 開學旺季
    10: 1.10,
    11: 1.15,  # 年底旺季
    12: 1.20,
}

# ============================================================
# L1: 資料結構
# ============================================================

@dataclass
class TimeSeriesPoint:
    """時序數據點"""
    date: str
    value: float
    
@dataclass
class Forecast:
    """預測結果"""
    horizon: str
    predictions: List[TimeSeriesPoint]
    confidence_lower: List[float]
    confidence_upper: List[float]
    trend: str  # "up", "down", "stable"
    growth_rate: float
    
@dataclass
class CustomerProbability:
    """客戶成交概率"""
    customer_id: int
    name: str
    probability: float
    factors: Dict[str, float]
    recommendation: str

@dataclass
class PriceRecommendation:
    """價格建議"""
    vehicle_id: int
    current_price: float
    recommended_price: float
    price_range: Tuple[float, float]
    days_on_lot: int
    similar_sold: List[Dict]

@dataclass
class DemandForecast:
    """需求預測"""
    brand: str
    model: str
    predicted_demand: int
    confidence: float
    trend: str

# ============================================================
# L2: 預測演算法
# ============================================================

class SimpleMovingAverage:
    """簡單移動平均"""
    
    @staticmethod
    def forecast(data: List[float], window: int = 7, horizon: int = 7) -> List[float]:
        """預測未來值"""
        if len(data) < window:
            window = len(data)
        
        if not data:
            return [0.0] * horizon
        
        predictions = []
        working_data = list(data)
        
        for _ in range(horizon):
            avg = sum(working_data[-window:]) / window
            predictions.append(avg)
            working_data.append(avg)
        
        return predictions


class ExponentialSmoothing:
    """指數平滑法"""
    
    @staticmethod
    def forecast(data: List[float], alpha: float = 0.3, horizon: int = 7) -> List[float]:
        """預測未來值（簡單指數平滑）"""
        if not data:
            return [0.0] * horizon
        
        # 初始化
        level = data[0]
        
        # 擬合歷史數據
        for value in data[1:]:
            level = alpha * value + (1 - alpha) * level
        
        # 預測
        return [level] * horizon
    
    @staticmethod
    def forecast_with_trend(
        data: List[float], 
        alpha: float = 0.3, 
        beta: float = 0.1,
        horizon: int = 7
    ) -> List[float]:
        """Holt 雙參數指數平滑（含趨勢）"""
        if len(data) < 2:
            return [data[0] if data else 0.0] * horizon
        
        # 初始化
        level = data[0]
        trend = data[1] - data[0]
        
        # 擬合
        for value in data[1:]:
            prev_level = level
            level = alpha * value + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend
        
        # 預測
        predictions = []
        for i in range(1, horizon + 1):
            predictions.append(level + i * trend)
        
        return predictions


class LinearRegression:
    """簡單線性回歸"""
    
    @staticmethod
    def fit(x: List[float], y: List[float]) -> Tuple[float, float]:
        """擬合線性模型，返回 (斜率, 截距)"""
        n = len(x)
        if n < 2:
            return (0.0, y[0] if y else 0.0)
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)
        
        denom = n * sum_xx - sum_x * sum_x
        if denom == 0:
            return (0.0, sum_y / n)
        
        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n
        
        return (slope, intercept)
    
    @staticmethod
    def predict(slope: float, intercept: float, x: float) -> float:
        """預測"""
        return slope * x + intercept
    
    @staticmethod
    def forecast(data: List[float], horizon: int = 7) -> List[float]:
        """使用線性回歸預測"""
        x = list(range(len(data)))
        slope, intercept = LinearRegression.fit(x, data)
        
        predictions = []
        for i in range(len(data), len(data) + horizon):
            predictions.append(LinearRegression.predict(slope, intercept, i))
        
        return predictions


class ConfidenceInterval:
    """置信區間計算"""
    
    @staticmethod
    def calculate(
        predictions: List[float], 
        historical_std: float,
        confidence: float = 0.95
    ) -> Tuple[List[float], List[float]]:
        """計算置信區間"""
        # Z 值（95% 置信度）
        z = 1.96 if confidence == 0.95 else 1.645
        
        lower = []
        upper = []
        
        for i, pred in enumerate(predictions):
            # 隨時間推移，不確定性增加
            margin = z * historical_std * math.sqrt(1 + i * 0.1)
            lower.append(max(0, pred - margin))
            upper.append(pred + margin)
        
        return lower, upper

# ============================================================
# L3: 業務預測服務
# ============================================================

class PredictionService:
    """預測服務"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """獲取資料庫連接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def forecast_sales(
        self, 
        horizon: str = "month",
        method: str = "exponential"
    ) -> Forecast:
        """銷售預測"""
        conn = self._get_connection()
        c = conn.cursor()
        
        # 獲取歷史銷售數據（過去 90 天）
        c.execute('''
            SELECT DATE(deal_date) as date, 
                   COUNT(*) as count,
                   SUM(sale_price) as amount
            FROM deals 
            WHERE deal_date >= date('now', '-90 days')
              AND status = 'completed'
            GROUP BY DATE(deal_date)
            ORDER BY date
        ''')
        
        rows = c.fetchall()
        conn.close()
        
        # 填充缺失日期
        amounts = []
        if rows:
            start_date = datetime.strptime(rows[0]['date'], '%Y-%m-%d')
            end_date = datetime.now()
            date_amounts = {r['date']: r['amount'] or 0 for r in rows}
            
            current = start_date
            while current <= end_date:
                date_str = current.strftime('%Y-%m-%d')
                amounts.append(date_amounts.get(date_str, 0))
                current += timedelta(days=1)
        
        if not amounts:
            amounts = [0] * 30
        
        # 預測
        days = FORECAST_HORIZONS.get(horizon, 30)
        
        if method == "exponential":
            predictions = ExponentialSmoothing.forecast_with_trend(amounts, horizon=days)
        elif method == "linear":
            predictions = LinearRegression.forecast(amounts, horizon=days)
        else:
            predictions = SimpleMovingAverage.forecast(amounts, horizon=days)
        
        # 應用季節性調整
        base_date = datetime.now()
        adjusted_predictions = []
        for i, pred in enumerate(predictions):
            future_date = base_date + timedelta(days=i+1)
            seasonality = SEASONALITY.get(future_date.month, 1.0)
            adjusted_predictions.append(max(0, pred * seasonality))
        
        # 計算置信區間
        if len(amounts) > 1:
            std = statistics.stdev(amounts)
        else:
            std = abs(amounts[0]) * 0.2 if amounts else 1
        
        lower, upper = ConfidenceInterval.calculate(adjusted_predictions, std)
        
        # 判斷趨勢
        if len(adjusted_predictions) >= 2:
            change = (adjusted_predictions[-1] - adjusted_predictions[0]) / max(adjusted_predictions[0], 1)
            if change > 0.05:
                trend = "up"
            elif change < -0.05:
                trend = "down"
            else:
                trend = "stable"
            growth_rate = change * 100
        else:
            trend = "stable"
            growth_rate = 0
        
        # 生成時序點
        prediction_points = []
        for i, pred in enumerate(adjusted_predictions):
            date = (datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d')
            prediction_points.append(TimeSeriesPoint(date=date, value=round(pred, 2)))
        
        return Forecast(
            horizon=horizon,
            predictions=prediction_points,
            confidence_lower=lower,
            confidence_upper=upper,
            trend=trend,
            growth_rate=round(growth_rate, 2)
        )
    
    def predict_customer_probability(self, customer_id: int = None) -> List[CustomerProbability]:
        """預測客戶成交概率"""
        conn = self._get_connection()
        c = conn.cursor()
        
        query = '''
            SELECT c.id, c.name, c.status, c.budget, c.source,
                   c.created_at,
                   (SELECT COUNT(*) FROM followups f WHERE f.customer_id = c.id) as followup_count,
                   (SELECT MAX(follow_date) FROM followups f WHERE f.customer_id = c.id) as last_followup
            FROM customers c
            WHERE c.status NOT IN ('deal', 'lost')
        '''
        
        if customer_id:
            query += f' AND c.id = {customer_id}'
        
        c.execute(query)
        customers = c.fetchall()
        conn.close()
        
        results = []
        for cust in customers:
            factors = {}
            
            # 1. 狀態因子
            status_factor = STATUS_WEIGHTS.get(cust['status'], 0.1)
            factors['status'] = status_factor
            
            # 2. 預算因子（有預算 +0.1）
            budget_factor = 0.1 if cust['budget'] and cust['budget'] > 0 else 0
            factors['budget'] = budget_factor
            
            # 3. 跟進因子
            followup_count = cust['followup_count'] or 0
            followup_factor = min(0.2, followup_count * 0.05)
            factors['followup'] = followup_factor
            
            # 4. 時間因子（越新的客戶概率越高）
            if cust['created_at']:
                try:
                    created = datetime.fromisoformat(cust['created_at'].replace('Z', '+00:00'))
                    days_old = (datetime.now() - created.replace(tzinfo=None)).days
                    time_factor = max(0, 0.2 - days_old * 0.005)
                except:
                    time_factor = 0.1
            else:
                time_factor = 0.1
            factors['recency'] = time_factor
            
            # 5. 來源因子
            high_quality_sources = ['referral', 'return', 'line']
            source_factor = 0.1 if cust['source'] in high_quality_sources else 0.05
            factors['source'] = source_factor
            
            # 計算總概率
            probability = min(0.95, sum(factors.values()))
            
            # 生成建議
            if probability >= 0.7:
                recommendation = "高優先級跟進，可能近期成交"
            elif probability >= 0.4:
                recommendation = "持續跟進，提供更多車輛選擇"
            else:
                recommendation = "需要更多接觸，了解客戶需求"
            
            results.append(CustomerProbability(
                customer_id=cust['id'],
                name=cust['name'],
                probability=round(probability, 2),
                factors={k: round(v, 2) for k, v in factors.items()},
                recommendation=recommendation
            ))
        
        # 按概率排序
        results.sort(key=lambda x: x.probability, reverse=True)
        
        return results
    
    def recommend_price(self, vehicle_id: int) -> Optional[PriceRecommendation]:
        """價格建議"""
        conn = self._get_connection()
        c = conn.cursor()
        
        # 獲取車輛資訊
        c.execute('''
            SELECT id, brand, model, year, price, mileage, created_at
            FROM vehicles
            WHERE id = ?
        ''', (vehicle_id,))
        
        vehicle = c.fetchone()
        if not vehicle:
            conn.close()
            return None
        
        # 計算在庫天數
        if vehicle['created_at']:
            try:
                created = datetime.fromisoformat(vehicle['created_at'].replace('Z', '+00:00'))
                days_on_lot = (datetime.now() - created.replace(tzinfo=None)).days
            except:
                days_on_lot = 0
        else:
            days_on_lot = 0
        
        # 查詢類似車輛的成交價
        c.execute('''
            SELECT v.brand, v.model, v.year, d.sale_price, v.mileage
            FROM deals d
            JOIN vehicles v ON d.vehicle_id = v.id
            WHERE v.brand = ? 
              AND v.year BETWEEN ? AND ?
              AND d.status = 'completed'
              AND d.deal_date >= date('now', '-180 days')
            ORDER BY d.deal_date DESC
            LIMIT 10
        ''', (vehicle['brand'], vehicle['year'] - 2, vehicle['year'] + 2))
        
        similar = c.fetchall()
        conn.close()
        
        if similar:
            prices = [s['sale_price'] for s in similar if s['sale_price']]
            avg_price = statistics.mean(prices) if prices else vehicle['price']
            std_price = statistics.stdev(prices) if len(prices) > 1 else avg_price * 0.1
        else:
            avg_price = vehicle['price']
            std_price = vehicle['price'] * 0.1
        
        # 根據在庫天數調整
        if days_on_lot > 90:
            price_adjustment = 0.95  # 降價 5%
        elif days_on_lot > 60:
            price_adjustment = 0.97
        elif days_on_lot > 30:
            price_adjustment = 0.99
        else:
            price_adjustment = 1.0
        
        recommended = avg_price * price_adjustment
        
        return PriceRecommendation(
            vehicle_id=vehicle['id'],
            current_price=vehicle['price'],
            recommended_price=round(recommended, 0),
            price_range=(round(avg_price - std_price, 0), round(avg_price + std_price, 0)),
            days_on_lot=days_on_lot,
            similar_sold=[dict(s) for s in similar[:5]]
        )
    
    def forecast_demand(self, top_n: int = 10) -> List[DemandForecast]:
        """需求預測（熱門品牌/車型）"""
        conn = self._get_connection()
        c = conn.cursor()
        
        # 分析歷史銷售
        c.execute('''
            SELECT v.brand, v.model, COUNT(*) as sold_count,
                   AVG(d.sale_price) as avg_price
            FROM deals d
            JOIN vehicles v ON d.vehicle_id = v.id
            WHERE d.status = 'completed'
              AND d.deal_date >= date('now', '-90 days')
            GROUP BY v.brand, v.model
            ORDER BY sold_count DESC
            LIMIT ?
        ''', (top_n,))
        
        sales = c.fetchall()
        conn.close()
        
        results = []
        for item in sales:
            sold_count = item['sold_count']
            
            # 簡單預測：歷史銷量 * 季節因子
            current_month = datetime.now().month
            seasonality = SEASONALITY.get(current_month, 1.0)
            
            predicted = int(sold_count * seasonality)
            
            # 趨勢判斷
            if seasonality > 1.05:
                trend = "up"
            elif seasonality < 0.95:
                trend = "down"
            else:
                trend = "stable"
            
            results.append(DemandForecast(
                brand=item['brand'],
                model=item['model'] or "綜合",
                predicted_demand=predicted,
                confidence=0.75,
                trend=trend
            ))
        
        return results

# ============================================================
# L4: API 接口與便捷函數
# ============================================================

_prediction_service: Optional[PredictionService] = None


def get_prediction_service(db_path: str = None) -> PredictionService:
    """獲取預測服務"""
    global _prediction_service
    if _prediction_service is None or db_path:
        import config
        _prediction_service = PredictionService(db_path or config.MASTER_DB)
    return _prediction_service


def forecast_sales(horizon: str = "month", method: str = "exponential") -> Dict[str, Any]:
    """銷售預測 API"""
    service = get_prediction_service()
    result = service.forecast_sales(horizon, method)
    return {
        'horizon': result.horizon,
        'predictions': [{'date': p.date, 'value': p.value} for p in result.predictions],
        'confidence_lower': result.confidence_lower,
        'confidence_upper': result.confidence_upper,
        'trend': result.trend,
        'growth_rate': result.growth_rate
    }


def predict_customer(customer_id: int = None) -> List[Dict[str, Any]]:
    """客戶成交概率 API"""
    service = get_prediction_service()
    results = service.predict_customer_probability(customer_id)
    return [
        {
            'customer_id': r.customer_id,
            'name': r.name,
            'probability': r.probability,
            'factors': r.factors,
            'recommendation': r.recommendation
        }
        for r in results
    ]


def recommend_price(vehicle_id: int) -> Optional[Dict[str, Any]]:
    """價格建議 API"""
    service = get_prediction_service()
    result = service.recommend_price(vehicle_id)
    if not result:
        return None
    return {
        'vehicle_id': result.vehicle_id,
        'current_price': result.current_price,
        'recommended_price': result.recommended_price,
        'price_range': result.price_range,
        'days_on_lot': result.days_on_lot,
        'similar_sold': result.similar_sold
    }


def forecast_demand(top_n: int = 10) -> List[Dict[str, Any]]:
    """需求預測 API"""
    service = get_prediction_service()
    results = service.forecast_demand(top_n)
    return [
        {
            'brand': r.brand,
            'model': r.model,
            'predicted_demand': r.predicted_demand,
            'confidence': r.confidence,
            'trend': r.trend
        }
        for r in results
    ]


# 📚 知識點
# -----------
# 1. 時序預測：移動平均、指數平滑、線性回歸
# 2. Holt 雙參數：考慮趨勢的指數平滑
# 3. 季節性調整：根據月份調整預測值
# 4. 置信區間：量化預測不確定性
# 5. 特徵工程：從原始數據提取預測因子
