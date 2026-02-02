#!/usr/bin/env python3
"""
車行寶 CRM v5.1 - 主入口
北斗七星文創數位 × 織明

用法：
    python main.py

環境變數：
    PORT: 伺服器埠號（預設 10000）
    DATA_DIR: 資料目錄（預設 ./data）
"""
import os
import sys
import threading
import time
from http.server import HTTPServer
from datetime import datetime

# 確保模組路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from models import init_master_db
from handlers.router import Router
from services import backup_service, telegram_service
from services.scheduler_service import scheduler, register_default_tasks

def init_data_dir():
    """初始化資料目錄"""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.BACKUP_DIR, exist_ok=True)
    os.makedirs(os.path.join(config.DATA_DIR, 'uploads'), exist_ok=True)

def init_demo_tenant():
    """初始化演示租戶"""
    from models import get_tenant_by_code, create_tenant
    
    if not get_tenant_by_code('demo'):
        result = create_tenant(
            code='demo',
            name='演示車行',
            admin_phone='0912345678',
            admin_password='demo1234',
            admin_name='演示帳號'
        )
        if result['success']:
            print(f"✅ 演示帳號建立完成")
            print(f"   店家代碼：demo")
            print(f"   手機號碼：0912345678")
            print(f"   密碼：demo1234")

def main():
    """主程式"""
    print("=" * 50)
    print(f"🚗 {config.APP_NAME} v{config.VERSION}")
    print(f"   北斗七星文創數位 × 織明")
    print("=" * 50)
    
    # 初始化
    print("\n📦 初始化系統...")
    init_data_dir()
    init_master_db()
    init_demo_tenant()
    
    # 啟動排程服務
    register_default_tasks()
    scheduler.start()
    print("✅ 排程服務已啟動")
    
    # 啟動伺服器
    server = HTTPServer((config.HOST, config.PORT), Router)
    
    print(f"\n🌐 伺服器啟動於 http://{config.HOST}:{config.PORT}")
    print(f"   本機存取：http://localhost:{config.PORT}")
    print(f"   健康檢查：http://localhost:{config.PORT}/api/health")
    print("\n按 Ctrl+C 停止伺服器")
    print("-" * 50)
    
    # 發送啟動通知
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        telegram_service.send_message(
            f"🚗 *{config.APP_NAME} v{config.VERSION}*\n\n"
            f"伺服器已啟動\n"
            f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏳ 正在停止服務...")
        scheduler.stop()
        server.shutdown()
        print("👋 伺服器已停止")

if __name__ == '__main__':
    main()
