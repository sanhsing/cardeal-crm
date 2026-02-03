#!/usr/bin/env python3
"""
車行寶 CRM - 重設 Demo 租戶
部署 v5.3 後在 Render Shell 執行一次：
    python reset_demo.py

動作：
  1. 重設 demo 密碼為 demo1234
  2. 清空 demo 資料庫中的業務資料
  3. 重新載入 seed_demo 展示資料
"""
import os
import sys
import sqlite3
import hashlib

DATA_DIR = os.environ.get('DATA_DIR', './data')
MASTER_DB = os.path.join(DATA_DIR, 'master.db')
DEMO_DB = os.path.join(DATA_DIR, 'tenant_demo.db')

def reset_demo():
    # === 1. 重設 master.db 中的 demo 密碼 ===
    if not os.path.exists(MASTER_DB):
        print("❌ master.db 不存在")
        return

    pwd_hash = hashlib.sha256('demo1234'.encode()).hexdigest()
    conn = sqlite3.connect(MASTER_DB)
    c = conn.cursor()

    # 找到 demo tenant
    c.execute("SELECT id FROM tenants WHERE code='demo'")
    row = c.fetchone()
    if not row:
        print("❌ demo 租戶不存在，請先正常啟動一次")
        conn.close()
        return

    tenant_id = row[0]
    print(f"✅ 找到 demo 租戶 (id={tenant_id})")
    conn.close()

    # === 2. 清空 demo 業務資料 ===
    if not os.path.exists(DEMO_DB):
        print(f"❌ {DEMO_DB} 不存在")
        return

    conn = sqlite3.connect(DEMO_DB)
    c = conn.cursor()

    # 重設管理員密碼
    c.execute("UPDATE users SET password=?, phone='0912345678', name='演示帳號' WHERE id=1",
              (pwd_hash,))
    print("✅ 管理員密碼已重設為 demo1234")

    # 清空業務表（保留 users id=1）
    tables_to_clear = ['customers', 'vehicles', 'deals', 'followups',
                       'activity_logs', 'settings']
    for t in tables_to_clear:
        try:
            c.execute(f"DELETE FROM {t}")
            print(f"   🗑 {t} 已清空")
        except:
            pass

    # 清除多餘 user
    c.execute("DELETE FROM users WHERE id > 1")
    print("   🗑 多餘 users 已清除")

    conn.commit()
    conn.close()

    # === 3. 重新載入 seed 資料 ===
    try:
        from seed_demo import seed_demo_data
        seed_demo_data(DEMO_DB)
        print("\n🎉 Demo 重設完成！")
        print("   店家代碼：demo")
        print("   手機號碼：0912345678")
        print("   密碼：demo1234")
        print("   （員工密碼也是 demo1234）")
    except Exception as e:
        print(f"❌ seed_demo 載入失敗: {e}")

if __name__ == '__main__':
    reset_demo()
