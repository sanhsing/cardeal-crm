#!/usr/bin/env python3
"""
車行寶 CRM v5.2 - API 連接測試
北斗七星文創數位 × 織明

用法：python scripts/test_apis.py
"""
import os
import sys
import json
import urllib.request
import urllib.error

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_deepseek():
    """測試 DeepSeek API"""
    print("\n" + "=" * 50)
    print("🤖 測試 DeepSeek API")
    print("=" * 50)
    
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    
    if not api_key:
        print("❌ DEEPSEEK_API_KEY 未設定")
        print("   請在 .env 或環境變數中設定")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # 發送測試請求
    url = 'https://api.deepseek.com/v1/chat/completions'
    data = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': '回覆 OK'}],
        'max_tokens': 10
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result['choices'][0]['message']['content']
            print(f"✅ API 響應：{content}")
            print(f"✅ 模型：{result.get('model', 'unknown')}")
            return True
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        print(f"❌ HTTP 錯誤 {e.code}")
        print(f"   {error_body[:200]}")
        return False
    except Exception as e:
        print(f"❌ 錯誤：{e}")
        return False


def test_line():
    """測試 LINE API"""
    print("\n" + "=" * 50)
    print("💬 測試 LINE Messaging API")
    print("=" * 50)
    
    channel_secret = os.environ.get('LINE_CHANNEL_SECRET', '')
    access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
    
    if not channel_secret:
        print("❌ LINE_CHANNEL_SECRET 未設定")
        return False
    
    if not access_token:
        print("❌ LINE_CHANNEL_ACCESS_TOKEN 未設定")
        return False
    
    print(f"✅ Channel Secret: {channel_secret[:10]}...")
    print(f"✅ Access Token: {access_token[:20]}...")
    
    # 測試 Bot Info API
    url = 'https://api.line.me/v2/bot/info'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Bot 名稱：{result.get('displayName', 'unknown')}")
            print(f"✅ Bot ID：{result.get('userId', 'unknown')[:20]}...")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 錯誤 {e.code}")
        return False
    except Exception as e:
        print(f"❌ 錯誤：{e}")
        return False


def test_telegram():
    """測試 Telegram API"""
    print("\n" + "=" * 50)
    print("📱 測試 Telegram Bot API")
    print("=" * 50)
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN 未設定")
        return False
    
    print(f"✅ Bot Token: {bot_token[:20]}...")
    
    if chat_id:
        print(f"✅ Chat ID: {chat_id}")
    
    # 測試 getMe API
    url = f'https://api.telegram.org/bot{bot_token}/getMe'
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('ok'):
                bot = result.get('result', {})
                print(f"✅ Bot 名稱：{bot.get('first_name', 'unknown')}")
                print(f"✅ Bot Username：@{bot.get('username', 'unknown')}")
                return True
            else:
                print(f"❌ API 錯誤：{result}")
                return False
                
    except Exception as e:
        print(f"❌ 錯誤：{e}")
        return False


def test_vapid():
    """測試 VAPID 配置"""
    print("\n" + "=" * 50)
    print("🔔 測試 VAPID 推播配置")
    print("=" * 50)
    
    public_key = os.environ.get('VAPID_PUBLIC_KEY', '')
    private_key = os.environ.get('VAPID_PRIVATE_KEY', '')
    
    if not public_key:
        print("❌ VAPID_PUBLIC_KEY 未設定")
        print("   請運行：python scripts/generate_vapid.py")
        return False
    
    if not private_key:
        print("❌ VAPID_PRIVATE_KEY 未設定")
        return False
    
    print(f"✅ Public Key: {public_key[:30]}...")
    print(f"✅ Private Key: {private_key[:10]}...")
    print(f"✅ Key 長度：公鑰 {len(public_key)} / 私鑰 {len(private_key)}")
    
    return True


def main():
    print("=" * 50)
    print("🔧 車行寶 v5.2 API 連接測試")
    print("=" * 50)
    
    results = {
        'DeepSeek AI': test_deepseek(),
        'LINE': test_line(),
        'Telegram': test_telegram(),
        'VAPID': test_vapid(),
    }
    
    print("\n" + "=" * 50)
    print("📊 測試結果")
    print("=" * 50)
    
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\n通過：{passed}/{total}")
    
    if passed < total:
        print("\n💡 提示：")
        print("   1. 確保 .env 檔案已正確配置")
        print("   2. 或在命令行設定環境變數")
        print("   3. 參考 .env.example 範例")


if __name__ == '__main__':
    main()
