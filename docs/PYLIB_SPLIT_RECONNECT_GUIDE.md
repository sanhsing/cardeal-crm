# pylib 拆解與回接指南（I/J/K）

本文件目的：把 cardeal 的業務邏輯穩定抽離為 `pylib` 資產，並在不破壞現有功能的前提下，逐步回接到應用層（app/models/services）。

---

## 1. 分層定義

### 1.1 atoms（原子）
**只做最小、可重複使用的純函數/小工具**

- ✅ 可 import 標準庫
- ✅ 可被任何專案使用
- ❌ 不得 import app / config / db / http
- ❌ 不得讀寫檔案、環境變數

**檢核**：單檔可單元測試；輸入相同→輸出相同（或明確可控）。

### 1.2 units（單一責任規則）
**把「業務規則」集中化，但仍保持純邏輯**

- ✅ 可以 import atoms
- ✅ 接受資料（dict/row/list）作為輸入
- ❌ 不得觸碰 ORM / DB session
- ❌ 不得觸碰 Flask request/response
- ❌ 不得直接讀取 config（由上層注入）

**檢核**：unit 的函數簽名可以在 REPL 裡直接呼叫，不需要啟動服務。

### 1.3 composites（編排）
**把多個 unit 串起來，但不寫細節邏輯**
- ✅ 可呼叫 units
- ✅ 做資料流整合
- ❌ 不得寫規則本體

---

## 2. 拆解策略（最安全的順序）

優先順序：**規則 → 計算 → payload → DB 相關最後拆**

1) 方案/權限（permissions）  
2) 報表/彙總（metrics/summary）  
3) 通知 payload 組裝（payload builder）  
4) DB/ORM 相關（最後）

理由：越靠近「規則」，越純、越可測、越不會影響既有系統。

---

## 3. 具體拆解流程（每次只做一小刀）

### Step A：找出一段可被抽離的「規則片段」
特徵：
- if/else 很多
- 依 plan/status 決定功能
- 依輸入組裝 payload
- 依 rows 計算數字

### Step B：把規則改寫為純函數（unit）
- 把外部依賴（config/db/http）改為參數傳入
- 若參數很多，使用 dataclass 作為 input model

### Step C：新增 pytest 測試（先寫測試再回接）
- 覆蓋：正常路徑 + 1 個邊界案例
- 測試目標：防止 AI/未來修改造成 silent break

### Step D：在 app 層回接
- 原本散落的規則 → 改成呼叫 unit
- 禁止在 app 層重寫同一條規則（避免雙源）

### Step E：封存（audit）
在 `audits/` 寫入一段：
- 拆了什麼
- 回接點在哪
- 測試覆蓋哪些案例

---

## 4. 本次新增的單元（I/J）

### 4.1 `pylib/units/metrics_rules.py`
- `compute_summary(rows, status_key='status', amount_key='amount', ...)`
- 輸入：已載入的 rows（list[dict-like]）
- 輸出：`Summary` dataclass（可序列化）

用途：把 dashboard/報表的「計算」與「資料取得」分離。

### 4.2 `pylib/units/payload_rules.py`
- `build_notification(title, body, url, level, meta)`
- `to_webpush(payload)` / `to_email(payload)`

用途：把「通知內容」與「發送管道」分離；避免在 services 內拼字串、混合 SDK 呼叫。

---

## 5. 最小測試集（pytest）

原則：測「資產庫穩定性」，不測整個 app。

- atoms：工具函數的基本不變性
- units：核心規則的預期輸出
- 每個 unit 至少 2 個測試：正常 + 邊界

---

## 6. 回接範例（建議樣式）

### 6.1 metrics 回接（服務層）
```python
from pylib.units.metrics_rules import compute_summary

rows = repo.list_invoices(tenant_id=tid)  # 仍在 app 層
summary = compute_summary(rows, amount_key="amount", status_key="status")
return jsonify({
  "total": summary.total,
  "active": summary.active,
  "amount_sum": summary.amount_sum,
})
```

### 6.2 payload 回接（通知層）
```python
from pylib.units.payload_rules import build_notification, to_webpush

p = build_notification(
  title="Backup completed",
  body="Daily backup finished.",
  level="info",
  meta={"tenant": tenant_code},
)
webpush_body = to_webpush(p)
push_service.send(subscription, webpush_body)  # 仍在 app 層
```

---

## 7. 禁止事項（治理底線）

- ❌ 在 app 內重寫 unit 的規則（造成雙源）
- ❌ unit 內讀取 env/config/db
- ❌ 為了方便把 IO 放進 pylib（污染資產庫）

---

## 8. 版本化（pylib 作為資產）

當 pylib 開始跨專案使用，必須：
- 以 `pyproject.toml` 管理版本
- 任何破壞性變更（函數簽名改）提升 minor/major
- 透過 pytest 確保回歸

---
