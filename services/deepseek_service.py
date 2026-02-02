"""
車行寶 CRM v5.1 - DeepSeek AI 整合服務
北斗七星文創數位 × 織明

功能：
1. 智能車價分析
2. 客戶意向深度分析
3. 銷售話術生成
4. 市場趨勢預測

XTF任務鏈：D
"""
import json
import os
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, List, Optional, Any


# ===== 配置 =====

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_MODEL = 'deepseek-chat'

# 備用：OpenAI 相容
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'


class AIProvider:
    """AI 服務提供者"""
    
    def __init__(self, provider: str = 'deepseek') -> None:
        """
        Args:
            provider: 'deepseek' | 'openai'
        """
        self.provider = provider
        
        if provider == 'deepseek':
            self.api_key = DEEPSEEK_API_KEY
            self.api_url = DEEPSEEK_API_URL
            self.model = DEEPSEEK_MODEL
        else:
            self.api_key = OPENAI_API_KEY
            self.api_url = OPENAI_API_URL
            self.model = 'gpt-3.5-turbo'
    
    def chat(self, messages: List[Dict], temperature: float = 0.7, 
             max_tokens: int = 1000) -> Dict:
        """發送聊天請求
        
        Args:
            messages: [{'role': 'user', 'content': '...'}]
            temperature: 創造性 0-2
            max_tokens: 最大 token 數
        
        Returns:
            {'success': True, 'content': '...', 'usage': {...}}
        """
        if not self.api_key:
            return {
                'success': False,
                'error': f'{self.provider} API Key 未設定'
            }
        
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            return {
                'success': True,
                'content': result['choices'][0]['message']['content'],
                'usage': result.get('usage', {})
            }
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            return {'success': False, 'error': f'API 錯誤: {e.code}', 'detail': error_body}
        except urllib.error.URLError as e:
            return {'success': False, 'error': f'網路錯誤: {e.reason}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# ===== 全域 AI 實例 =====
ai = AIProvider('deepseek')


def set_provider(provider: str) -> None:
    """切換 AI 提供者"""
    global ai
    ai = AIProvider(provider)


# ============================================================
# 1. 智能車價分析
# ============================================================

def analyze_vehicle_price(vehicle: Dict, market_data: Dict = None) -> Dict:
    """智能車價分析
    
    Args:
        vehicle: 車輛資訊
        market_data: 市場數據（可選）
    
    Returns:
        {
            'estimated_price': {'low': int, 'mid': int, 'high': int},
            'analysis': str,
            'selling_points': [str],
            'concerns': [str],
            'market_position': str
        }
    """
    prompt = f"""你是一位專業的中古車估價師，請分析以下車輛的合理售價。

車輛資訊：
- 品牌型號：{vehicle.get('brand', '')} {vehicle.get('model', '')}
- 年份：{vehicle.get('year', '')} 年
- 里程：{vehicle.get('mileage', 0):,} 公里
- 顏色：{vehicle.get('color', '未知')}
- 配備：{vehicle.get('features', '標準配備')}
- 車況：{vehicle.get('condition_note', '正常')}

{f"市場參考：近期同款成交均價 ${market_data.get('avg_price', 0):,}" if market_data else ""}

請提供：
1. 建議售價範圍（最低、中間、最高）
2. 價格分析說明
3. 賣點（3點）
4. 注意事項（如有）
5. 市場定位（搶手/正常/冷門）

請用 JSON 格式回答，包含：estimated_price, analysis, selling_points, concerns, market_position"""

    result = ai.chat([
        {'role': 'system', 'content': '你是專業中古車估價師，回答請用繁體中文，格式為 JSON。'},
        {'role': 'user', 'content': prompt}
    ], temperature=0.3)
    
    if not result['success']:
        return result
    
    try:
        # 嘗試解析 JSON
        content = result['content']
        # 移除可能的 markdown 標記
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]
        
        data = json.loads(content.strip())
        data['success'] = True
        data['usage'] = result.get('usage', {})
        return data
    except json.JSONDecodeError:
        return {
            'success': True,
            'analysis': result['content'],
            'estimated_price': None,
            'raw_response': True
        }


# ============================================================
# 2. 客戶意向深度分析
# ============================================================

def analyze_customer_deep(customer: Dict, interactions: List[Dict]) -> Dict:
    """客戶意向深度分析
    
    Args:
        customer: 客戶資訊
        interactions: 互動記錄列表
    
    Returns:
        {
            'intent_score': int,
            'intent_level': str,
            'personality': str,
            'preferences': [str],
            'recommended_approach': str,
            'next_steps': [str]
        }
    """
    # 整理互動摘要
    interaction_summary = []
    for i in interactions[:10]:  # 最多取 10 筆
        interaction_summary.append(
            f"- {i.get('created_at', '')}: {i.get('log_type', '')} - {i.get('content', '')}"
        )
    
    prompt = f"""你是一位資深汽車銷售顧問，請分析以下客戶的購買意向。

客戶資訊：
- 姓名：{customer.get('name', '未知')}
- 等級：{customer.get('level', 'normal')}
- 來源：{customer.get('source', '未知')}
- 建檔日期：{customer.get('created_at', '')}

互動記錄：
{chr(10).join(interaction_summary) if interaction_summary else '無記錄'}

請分析：
1. 購買意向分數（0-100）
2. 意向等級（hot/warm/cold）
3. 客戶類型特徵
4. 偏好推測
5. 建議應對策略
6. 下一步行動建議（3點）

請用 JSON 格式回答。"""

    result = ai.chat([
        {'role': 'system', 'content': '你是專業汽車銷售顧問，擅長客戶心理分析，回答用繁體中文 JSON 格式。'},
        {'role': 'user', 'content': prompt}
    ], temperature=0.4)
    
    if not result['success']:
        return result
    
    try:
        content = result['content']
        if '```' in content:
            content = content.split('```')[1].split('```')[0]
            if content.startswith('json'):
                content = content[4:]
        
        data = json.loads(content.strip())
        data['success'] = True
        return data
    except json.JSONDecodeError:
        return {
            'success': True,
            'analysis': result['content'],
            'raw_response': True
        }


# ============================================================
# 3. 銷售話術生成
# ============================================================

def generate_sales_script(vehicle: Dict, customer: Dict = None, 
                          scenario: str = 'general') -> Dict:
    """生成銷售話術
    
    Args:
        vehicle: 車輛資訊
        customer: 客戶資訊（可選）
        scenario: 情境 ('general', 'objection', 'closing', 'followup')
    
    Returns:
        {
            'scripts': [
                {'type': str, 'title': str, 'content': str}
            ]
        }
    """
    scenario_prompts = {
        'general': '一般介紹話術，包含開場、特點、價值',
        'objection': '異議處理話術，針對價格、車況等常見疑慮',
        'closing': '促成話術，推動客戶做決定',
        'followup': '跟進話術，維繫關係、喚起興趣'
    }
    
    customer_context = ""
    if customer:
        customer_context = f"""
客戶背景：
- 類型：{customer.get('level', 'normal')}
- 來源：{customer.get('source', '未知')}
- 備註：{customer.get('note', '無')}
"""

    prompt = f"""你是一位頂尖汽車銷售培訓師，請為以下車輛生成專業銷售話術。

車輛資訊：
- 品牌型號：{vehicle.get('brand', '')} {vehicle.get('model', '')}
- 年份：{vehicle.get('year', '')} 年
- 里程：{vehicle.get('mileage', 0):,} 公里
- 售價：${vehicle.get('asking_price', 0):,}
{customer_context}

情境需求：{scenario_prompts.get(scenario, scenario_prompts['general'])}

請生成 3-5 段話術，每段包含：
- type：類型（opening/features/value/objection/closing）
- title：標題
- content：話術內容（口語化、有說服力）

請用 JSON 格式回答，格式：{{"scripts": [...]}}"""

    result = ai.chat([
        {'role': 'system', 'content': '你是汽車銷售培訓專家，話術要接地氣、有說服力，用繁體中文。'},
        {'role': 'user', 'content': prompt}
    ], temperature=0.7)
    
    if not result['success']:
        return result
    
    try:
        content = result['content']
        if '```' in content:
            content = content.split('```')[1].split('```')[0]
            if content.startswith('json'):
                content = content[4:]
        
        data = json.loads(content.strip())
        data['success'] = True
        return data
    except json.JSONDecodeError:
        return {
            'success': True,
            'scripts': [{'type': 'general', 'title': '話術', 'content': result['content']}],
            'raw_response': True
        }


# ============================================================
# 4. 市場趨勢預測
# ============================================================

def predict_market_trend(brand: str = None, segment: str = None) -> Dict:
    """市場趨勢預測
    
    Args:
        brand: 品牌（可選）
        segment: 車型區隔（如 SUV, Sedan）
    
    Returns:
        {
            'trend': str,
            'factors': [str],
            'recommendations': [str],
            'hot_models': [str]
        }
    """
    context = []
    if brand:
        context.append(f"品牌：{brand}")
    if segment:
        context.append(f"車型：{segment}")
    
    prompt = f"""你是一位汽車市場分析師，請分析台灣中古車市場趨勢。

{'分析範圍：' + '、'.join(context) if context else '整體市場分析'}

請提供：
1. 市場趨勢（漲/穩/跌）及原因
2. 影響因素（3-5點）
3. 經營建議（3點）
4. 熱門車款推薦（3-5款）

請用 JSON 格式回答。"""

    result = ai.chat([
        {'role': 'system', 'content': '你是汽車市場分析專家，熟悉台灣中古車市場，用繁體中文回答。'},
        {'role': 'user', 'content': prompt}
    ], temperature=0.5)
    
    if not result['success']:
        return result
    
    try:
        content = result['content']
        if '```' in content:
            content = content.split('```')[1].split('```')[0]
            if content.startswith('json'):
                content = content[4:]
        
        data = json.loads(content.strip())
        data['success'] = True
        return data
    except json.JSONDecodeError:
        return {
            'success': True,
            'analysis': result['content'],
            'raw_response': True
        }


# ============================================================
# 5. 快速問答
# ============================================================

def quick_ask(question: str, context: str = None) -> Dict:
    """快速問答
    
    Args:
        question: 問題
        context: 上下文（可選）
    
    Returns:
        {'success': True, 'answer': str}
    """
    system_prompt = """你是車行寶 AI 助手，專門協助中古車行業務。
回答要：簡潔、專業、實用。用繁體中文。"""
    
    messages = [{'role': 'system', 'content': system_prompt}]
    
    if context:
        messages.append({'role': 'user', 'content': f"背景資訊：{context}"})
        messages.append({'role': 'assistant', 'content': '好的，我了解了。請問有什麼問題？'})
    
    messages.append({'role': 'user', 'content': question})
    
    result = ai.chat(messages, temperature=0.5, max_tokens=500)
    
    if result['success']:
        return {
            'success': True,
            'answer': result['content'],
            'usage': result.get('usage', {})
        }
    
    return result


# ============================================================
# 6. API 狀態檢查
# ============================================================

def check_api_status() -> Dict:
    """檢查 API 狀態"""
    result = ai.chat([
        {'role': 'user', 'content': '請回答：OK'}
    ], temperature=0, max_tokens=10)
    
    return {
        'success': result['success'],
        'provider': ai.provider,
        'model': ai.model,
        'status': 'online' if result['success'] else 'offline',
        'error': result.get('error')
    }


# 📚 知識點
# -----------
# 1. DeepSeek API：
#    - 與 OpenAI 相容的介面
#    - 支援繁體中文
#    - 成本較低
#
# 2. JSON 格式輸出：
#    - 在 prompt 中明確要求 JSON
#    - temperature 較低提高穩定性
#    - 容錯處理：解析失敗返回原文
#
# 3. 多提供者支援：
#    - 可切換 DeepSeek/OpenAI
#    - 統一介面
#    - 環境變數配置
#
# 4. 提示工程：
#    - 角色設定（System prompt）
#    - 結構化輸入
#    - 明確輸出格式要求
