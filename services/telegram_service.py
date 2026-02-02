"""
車行寶 CRM v5.0 - Telegram 服務模組
北斗七星文創數位 × 織明
"""
import json
import urllib.request
import urllib.parse
import config

def send_message(text: str, parse_mode: str = 'Markdown') -> bool:
    """發送 Telegram 通知"""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return False
    
    url = f'https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage'
    
    data = urllib.parse.urlencode({
        'chat_id': config.TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': parse_mode
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result.get('ok', False)
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def notify_new_tenant(tenant_name: str, tenant_code: str):
    """通知新租戶註冊"""
    text = f"""🏪 *新店家註冊*

店家：{tenant_name}
代碼：`{tenant_code}`
時間：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    return send_message(text)

def notify_payment(tenant_name: str, plan: str, amount: int):
    """通知付款成功"""
    text = f"""💰 *訂閱付款成功*

店家：{tenant_name}
方案：{plan}
金額：${amount:,}
時間：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    return send_message(text)

def notify_backup(tenant_count: int, success: bool, details: str = ''):
    """通知備份結果"""
    status = "✅ 成功" if success else "❌ 失敗"
    text = f"""🗄️ *自動備份 {status}*

租戶數：{tenant_count}
{details}
時間：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    return send_message(text)

def notify_error(error_type: str, message: str, details: str = ''):
    """通知錯誤"""
    text = f"""⚠️ *系統錯誤*

類型：{error_type}
訊息：{message}
{f'詳情：{details}' if details else ''}
時間：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    return send_message(text)
