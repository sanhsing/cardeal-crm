# 車行寶 CRM v5.3 修復部署

## 根因分析
v5.2 hotfix2 重構 `handlers/base.py` 時加了類型提示，
但**移除了 3 個關鍵方法**：
- `require_auth()` - 認證守門
- `get_db_path()` - 取 DB 路徑
- `get_user_info()` - 取用戶資訊

→ 所有需登入的 API → AttributeError → **502**

## 修復內容
| 檔案 | 動作 | 說明 |
|:-----|:-----|:-----|
| `base.py` | → `handlers/base.py` | **核心修復**：補回 3 方法 |
| `main.py` | → `main.py` | v5.3：整合 seed_demo |
| `seed_demo.py` | → `seed_demo.py` | 50客戶/60車/50交易 展示資料 |
| `reset_demo.py` | → `reset_demo.py` | Render Shell 重設 demo |

## 部署步驟
```bash
# 1. 本地操作
cd E:\CardealCRM\cardeal_v5.2
copy handlers\base.py handlers\base_bak.py
copy 下載的base.py handlers\base.py
copy 下載的main.py main.py
copy 下載的seed_demo.py seed_demo.py
copy 下載的reset_demo.py reset_demo.py

# 2. 推送
git add -A
git commit -m "v5.3: fix require_auth + seed_demo"
git push origin main

# 3. Render Shell（部署完成後）
python reset_demo.py
```

## 帳號
| 欄位 | 值 |
|:-----|:---|
| 店家代碼 | demo |
| 手機號碼 | 0912345678 |
| 密碼 | demo1234 |
