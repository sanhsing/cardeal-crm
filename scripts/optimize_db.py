#!/usr/bin/env python3
"""
車行寶 CRM v5.1 - 資料庫優化腳本
北斗七星文創數位 × 織明

功能：索引優化、VACUUM、ANALYZE、查詢分析
"""
import os
import sys
import sqlite3
from datetime import datetime

# 加入專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from models import get_connection

# ===== 新增索引建議 =====

ADDITIONAL_INDEXES = [
    # 複合索引（常見查詢組合）
    'CREATE INDEX IF NOT EXISTS idx_customers_status_level ON customers(status, level)',
    'CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at)',
    'CREATE INDEX IF NOT EXISTS idx_vehicles_status_brand ON vehicles(status, brand)',
    'CREATE INDEX IF NOT EXISTS idx_vehicles_purchase_date ON vehicles(purchase_date)',
    'CREATE INDEX IF NOT EXISTS idx_deals_type_status ON deals(deal_type, status)',
    'CREATE INDEX IF NOT EXISTS idx_deals_created_at ON deals(created_at)',
    'CREATE INDEX IF NOT EXISTS idx_followups_result ON followups(result)',
    'CREATE INDEX IF NOT EXISTS idx_vehicle_images_vehicle ON vehicle_images(vehicle_id)',
]


def get_all_tenant_dbs():
    """取得所有租戶資料庫"""
    dbs = []
    for f in os.listdir(config.DATA_DIR):
        if f.startswith('tenant_') and f.endswith('.db'):
            dbs.append(os.path.join(config.DATA_DIR, f))
    return dbs


def optimize_database(db_path):
    """優化單個資料庫"""
    print(f"\n{'='*50}")
    print(f"📦 優化資料庫: {os.path.basename(db_path)}")
    print(f"{'='*50}")
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 1. 取得資料庫大小
    size_before = os.path.getsize(db_path)
    print(f"\n📊 優化前大小: {size_before / 1024:.2f} KB")
    
    # 2. 檢查完整性
    print("\n🔍 檢查完整性...")
    c.execute("PRAGMA integrity_check")
    result = c.fetchone()[0]
    if result == 'ok':
        print("   ✅ 資料庫完整")
    else:
        print(f"   ⚠️ 完整性問題: {result}")
    
    # 3. 建立新索引
    print("\n📈 建立新索引...")
    for idx_sql in ADDITIONAL_INDEXES:
        try:
            c.execute(idx_sql)
            idx_name = idx_sql.split('EXISTS ')[1].split(' ON')[0]
            print(f"   ✅ {idx_name}")
        except Exception as e:
            pass  # 索引可能已存在
    conn.commit()
    
    # 4. 更新統計資訊
    print("\n📊 更新統計資訊 (ANALYZE)...")
    c.execute("ANALYZE")
    conn.commit()
    
    # 5. 回收空間
    print("\n🧹 回收空間 (VACUUM)...")
    c.execute("VACUUM")
    conn.commit()
    
    # 6. 檢查結果
    size_after = os.path.getsize(db_path)
    saved = size_before - size_after
    
    print(f"\n📊 優化後大小: {size_after / 1024:.2f} KB")
    if saved > 0:
        print(f"   節省: {saved / 1024:.2f} KB ({saved * 100 / size_before:.1f}%)")
    
    # 7. 顯示索引統計
    print("\n📋 索引列表:")
    c.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name")
    for row in c.fetchall():
        if row[0]:  # 排除 None
            print(f"   • {row[1]}.{row[0]}")
    
    # 8. 顯示表統計
    print("\n📋 表統計:")
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = c.fetchall()
    for (table_name,) in tables:
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = c.fetchone()[0]
        print(f"   • {table_name}: {count} 筆")
    
    conn.close()
    
    return {
        'db': os.path.basename(db_path),
        'size_before': size_before,
        'size_after': size_after,
        'saved': saved
    }


def analyze_slow_queries(db_path):
    """分析可能的慢查詢（模擬）"""
    print(f"\n{'='*50}")
    print(f"🔍 查詢分析建議")
    print(f"{'='*50}")
    
    suggestions = [
        {
            'scenario': '查詢特定狀態的客戶',
            'bad': "SELECT * FROM customers WHERE status = 'active'",
            'good': "-- 已有 idx_customers_status 索引 ✅"
        },
        {
            'scenario': '查詢特定品牌的在庫車輛',
            'bad': "SELECT * FROM vehicles WHERE status = 'in_stock' AND brand = 'Toyota'",
            'good': "-- 建議使用複合索引 idx_vehicles_status_brand ✅"
        },
        {
            'scenario': '查詢本月交易',
            'bad': "SELECT * FROM deals WHERE deal_date >= '2026-02-01'",
            'good': "-- 已有 idx_deals_date 索引 ✅"
        },
        {
            'scenario': '分頁查詢客戶',
            'bad': "SELECT * FROM customers ORDER BY created_at DESC LIMIT 20 OFFSET 100",
            'good': "-- 使用游標分頁代替 OFFSET（大資料量時更快）"
        }
    ]
    
    for s in suggestions:
        print(f"\n📌 {s['scenario']}")
        print(f"   {s['good']}")


def main():
    """主程式"""
    print("="*50)
    print("🛠️  車行寶 CRM 資料庫優化工具")
    print("="*50)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 取得所有資料庫
    dbs = get_all_tenant_dbs()
    
    if not dbs:
        print("\n⚠️  沒有找到租戶資料庫")
        return
    
    print(f"\n找到 {len(dbs)} 個租戶資料庫")
    
    # 優化所有資料庫
    results = []
    for db_path in dbs:
        result = optimize_database(db_path)
        results.append(result)
    
    # 查詢分析建議
    analyze_slow_queries(dbs[0] if dbs else None)
    
    # 總結
    print(f"\n{'='*50}")
    print("📊 優化總結")
    print(f"{'='*50}")
    
    total_saved = sum(r['saved'] for r in results)
    print(f"總共節省: {total_saved / 1024:.2f} KB")
    print(f"優化資料庫數: {len(results)}")
    
    print("\n✅ 優化完成")


if __name__ == '__main__':
    main()


# 📚 知識點
# -----------
# 1. VACUUM：
#    - 重建資料庫檔案
#    - 回收刪除資料的空間
#    - 整理碎片化
#
# 2. ANALYZE：
#    - 更新統計資訊
#    - 幫助查詢優化器選擇最佳計畫
#
# 3. 複合索引：
#    - 多欄位索引
#    - 順序很重要（最左前綴）
#    - (status, level) 可用於 WHERE status = ?
#
# 4. 覆蓋索引：
#    - 索引包含查詢所需所有欄位
#    - 不需回表查詢
#
# 5. 游標分頁 vs OFFSET：
#    - OFFSET 需要跳過所有前面的資料
#    - 游標分頁（WHERE id > ?）更高效
