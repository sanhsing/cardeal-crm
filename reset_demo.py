#!/usr/bin/env python3
"""
車行寶 CRM - 重設 Demo 租戶 (Render 修正版)
在 Render Shell 執行：python reset_demo.py
"""
import os, sys, sqlite3, hashlib, glob

def find_data_dir():
    for d in ['./data', '/opt/render/project/src/data', os.environ.get('DATA_DIR',''), '../data']:
        if d and os.path.isdir(d):
            return d
    return None

def reset_demo():
    print("🔍 搜索資料目錄...")
    cwd = os.getcwd()
    print(f"   CWD: {cwd}")

    data_dir = find_data_dir()
    if not data_dir:
        print("❌ 找不到 data 目錄，列出當前目錄：")
        for f in sorted(os.listdir('.')):
            print(f"     {f}")
        return

    print(f"✅ 資料目錄: {data_dir}")
    for f in sorted(os.listdir(data_dir)):
        size = os.path.getsize(os.path.join(data_dir, f))
        print(f"     {f} ({size:,} bytes)")

    # 搜索所有 .db 找含 tenants 表的
    master = None
    for db_file in glob.glob(os.path.join(data_dir, '*.db')):
        try:
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in c.fetchall()]
            if 'tenants' in tables:
                c.execute("SELECT id, code, name FROM tenants")
                tenants = c.fetchall()
                print(f"\n✅ Master DB: {db_file}")
                for t in tenants:
                    print(f"   tenant: id={t[0]} code={t[1]} name={t[2]}")
                master = db_file
            conn.close()
            if master:
                break
        except:
            pass

    if not master:
        print("❌ 找不到含 tenants 表的資料庫")
        return

    # 找 demo tenant db
    demo_db = os.path.join(data_dir, 'tenant_demo.db')
    if not os.path.exists(demo_db):
        for f in os.listdir(data_dir):
            if 'demo' in f.lower() and f.endswith('.db'):
                demo_db = os.path.join(data_dir, f)
                break
        else:
            print("❌ 找不到 demo 的 db 檔案")
            return

    print(f"✅ Demo DB: {demo_db}")

    # 重設密碼
    pwd_hash = hashlib.sha256('demo1234'.encode()).hexdigest()
    conn = sqlite3.connect(demo_db)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    demo_tables = [r[0] for r in c.fetchall()]
    print(f"   Tables: {demo_tables}")

    c.execute("UPDATE users SET password=?, phone='0912345678', name='演示帳號' WHERE id=1", (pwd_hash,))
    print("✅ 管理員密碼 → demo1234")

    for t in ['customers','vehicles','deals','followups','activity_logs','settings']:
        if t in demo_tables:
            try:
                c.execute(f"DELETE FROM {t}")
                print(f"   🗑 {t} 已清空")
            except Exception as e:
                print(f"   ⚠️ {t}: {e}")

    c.execute("DELETE FROM users WHERE id > 1")
    print("   🗑 多餘 users 已清除")
    conn.commit()
    conn.close()

    # 載入 seed 資料
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from seed_demo import seed_demo_data
        seed_demo_data(demo_db)
        print("\n🎉 Demo 重設完成！")
        print("   店家代碼：demo")
        print("   手機號碼：0912345678")
        print("   密碼：demo1234")
    except Exception as e:
        print(f"❌ seed_demo 載入失敗: {e}")
        import traceback; traceback.print_exc()

if __name__ == '__main__':
    reset_demo()
