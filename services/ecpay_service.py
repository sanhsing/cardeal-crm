"""
車行寶 CRM v5.0 - 綠界金流服務模組
北斗七星文創數位 × 織明
"""
import hashlib
import urllib.parse
from datetime import datetime
import config
from models import get_connection

def check_mac_value(params: dict) -> str:
    """計算 ECPay CheckMacValue"""
    # 排除 CheckMacValue 本身
    filtered = {k: v for k, v in params.items() if k != 'CheckMacValue'}
    
    # 按照字母排序
    sorted_params = sorted(filtered.items(), key=lambda x: x[0])
    
    # 組合字串
    param_str = '&'.join([f'{k}={v}' for k, v in sorted_params])
    
    # 加上 HashKey 和 HashIV
    raw = f"HashKey={config.ECPAY_HASH_KEY}&{param_str}&HashIV={config.ECPAY_HASH_IV}"
    
    # URL encode
    encoded = urllib.parse.quote_plus(raw).lower()
    
    # SHA256
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest().upper()

def create_order(tenant_id: int, plan_code: str, return_url: str, notify_url: str) -> dict:
    """建立付款訂單"""
    plan = config.PLANS.get(plan_code)
    if not plan:
        return {'success': False, 'error': '無效的方案'}
    
    # 產生訂單編號
    merchant_trade_no = f"CD{datetime.now().strftime('%Y%m%d%H%M%S')}{tenant_id:04d}"
    trade_date = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    
    # 記錄訂單
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    c.execute('''INSERT INTO subscriptions (tenant_id, plan_code, amount, merchant_trade_no, status)
                 VALUES (?, ?, ?, ?, 'pending')''',
              (tenant_id, plan_code, plan['price'], merchant_trade_no))
    conn.commit()
    conn.close()
    
    # 組合參數
    params = {
        'MerchantID': config.ECPAY_MERCHANT_ID,
        'MerchantTradeNo': merchant_trade_no,
        'MerchantTradeDate': trade_date,
        'PaymentType': 'aio',
        'TotalAmount': plan['price'],
        'TradeDesc': urllib.parse.quote(f'車行寶CRM {plan["name"]}'),
        'ItemName': plan['name'],
        'ReturnURL': notify_url,
        'OrderResultURL': return_url,
        'ChoosePayment': 'ALL',
        'EncryptType': 1,
    }
    
    params['CheckMacValue'] = check_mac_value(params)
    
    return {
        'success': True,
        'action_url': f'{config.ECPAY_API_URL}/Cashier/AioCheckOut/V5',
        'params': params,
        'merchant_trade_no': merchant_trade_no
    }

def process_notify(post_data: dict) -> dict:
    """處理 ECPay 回調通知"""
    # 驗證 CheckMacValue
    received_mac = post_data.get('CheckMacValue', '')
    calculated_mac = check_mac_value(post_data)
    
    if received_mac != calculated_mac:
        return {'success': False, 'error': 'CheckMacValue 驗證失敗'}
    
    merchant_trade_no = post_data.get('MerchantTradeNo', '')
    rtn_code = post_data.get('RtnCode', '')
    trade_no = post_data.get('TradeNo', '')
    
    # 更新訂單狀態
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    
    if rtn_code == '1':  # 付款成功
        # 取得訂單資訊
        c.execute('SELECT tenant_id, plan_code FROM subscriptions WHERE merchant_trade_no = ?',
                  (merchant_trade_no,))
        order = c.fetchone()
        
        if order:
            tenant_id = order['tenant_id']
            plan_code = order['plan_code']
            plan = config.PLANS.get(plan_code, {})
            
            # 計算到期日
            from datetime import timedelta
            expires_at = datetime.now() + timedelta(days=plan.get('days', 30))
            
            # 更新訂閱
            c.execute('''UPDATE subscriptions 
                         SET status = 'paid', trade_no = ?, paid_at = CURRENT_TIMESTAMP, expires_at = ?
                         WHERE merchant_trade_no = ?''',
                      (trade_no, expires_at.isoformat(), merchant_trade_no))
            
            # 更新租戶方案
            c.execute('''UPDATE tenants SET plan = ?, plan_expires = ? WHERE id = ?''',
                      (plan_code.replace('_monthly', '').replace('_yearly', ''), 
                       expires_at.isoformat(), tenant_id))
            
            conn.commit()
            
            # 發送通知
            from services import telegram_service
            c.execute('SELECT name FROM tenants WHERE id = ?', (tenant_id,))
            tenant = c.fetchone()
            if tenant:
                telegram_service.notify_payment(tenant['name'], plan.get('name', ''), plan.get('price', 0))
    else:
        # 付款失敗
        c.execute('''UPDATE subscriptions SET status = 'failed' WHERE merchant_trade_no = ?''',
                  (merchant_trade_no,))
        conn.commit()
    
    conn.close()
    return {'success': True, 'message': '1|OK'}

def get_subscription_status(tenant_id: int) -> dict:
    """取得訂閱狀態"""
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    
    c.execute('''SELECT plan, plan_expires FROM tenants WHERE id = ?''', (tenant_id,))
    tenant = c.fetchone()
    
    if not tenant:
        conn.close()
        return {'plan': 'free', 'expires': None, 'is_active': True}
    
    plan = tenant['plan'] or 'free'
    expires = tenant['plan_expires']
    
    is_active = True
    if expires:
        is_active = datetime.fromisoformat(expires) > datetime.now()
    
    conn.close()
    return {
        'plan': plan,
        'expires': expires,
        'is_active': is_active,
        'features': config.PLANS.get(f'{plan}_monthly', {}).get('features', [])
    }
