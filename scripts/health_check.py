#!/usr/bin/env python3
"""
車行寶 CRM v5.1 - 健康檢查腳本
北斗七星文創數位 × 織明

用於：
- Docker 健康檢查
- 監控系統檢查
- 部署後驗證
"""
import os
import sys
import json
import urllib.request
import urllib.error

def check_health(host='localhost', port=10000, timeout=5):
    """檢查服務健康狀態"""
    url = f'http://{host}:{port}/api/health'
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode())
            
            if data.get('status') == 'ok':
                print(f"✅ 服務正常")
                print(f"   版本: {data.get('version')}")
                print(f"   環境: {data.get('env')}")
                
                checks = data.get('checks', {})
                for name, check in checks.items():
                    status = '✅' if check.get('healthy') else '⚠️'
                    print(f"   {status} {name}")
                
                return 0
            else:
                print(f"⚠️ 服務異常: {data.get('status')}")
                return 1
                
    except urllib.error.URLError as e:
        print(f"❌ 無法連接服務: {e}")
        return 2
    except json.JSONDecodeError:
        print(f"❌ 回應格式錯誤")
        return 3
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        return 4


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='車行寶 CRM 健康檢查')
    parser.add_argument('--host', default='localhost', help='服務主機')
    parser.add_argument('--port', type=int, default=10000, help='服務埠號')
    parser.add_argument('--timeout', type=int, default=5, help='超時秒數')
    
    args = parser.parse_args()
    
    exit_code = check_health(args.host, args.port, args.timeout)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
