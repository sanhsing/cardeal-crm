# cardeal v5.3 Release Notes (Draft)

**Status**: DRAFT  
**Target**: v5.3.0  
**Base**: v5.2_p11p15 + hotfix2_fixed (config.py)  
**Date**: 2026-02-03

## 1. Scope (What changed)

### 1.1 Frontend decoupling (安全基線)
- 將前端資產移至 `static/`，後端不再以 Python 字串拼接輸出 HTML/JS。
- 前端 JavaScript 禁止使用 template literal（反引號 `），避免 AI 修補造成 parse error。

### 1.2 pylib 初始落地（資產化）
- 新增 `pylib/atoms`：無 IO、無 config、無 DB 的可複用原子工具。
- 新增 `pylib/units`：單一責任的業務規則層（pure functions），用於降低 services/models 的耦合與風險。

## 2. Non-goals (What did NOT change)
- 未新增任何商業功能或新的業務流程。
- 未變更資料庫 schema（若有變更請於此處補充）。
- 未調整對外 API 合約（若有變更請於此處補充）。

## 3. Risk controls & governance
- 以 Dry Run Gate 1-4 作為部署前硬性條件。
- Hard Stop：任何前端 Console parse error → No-Go。

## 4. Migration / Deployment notes
- 建議 Render 進行 full rebuild（避免 build cache）。
- 若已啟用 Service Worker，需更新版本號或暫時停用以避免舊快取。

## 5. Verification checklist (Release)
- [ ] Gate 1: Python 啟動、無語法錯誤、config 完整
- [ ] Gate 2: API 回 JSON、static 提供 HTML/JS
- [ ] Gate 3: Browser Console 無 SyntaxError
- [ ] Gate 4: 無痕視窗 + full rebuild 驗證

## 6. Rollback plan
- 回退至 `v5.2_p11p15 + hotfix2_fixed` tag。
- 清除 Service Worker / browser cache 後再驗證回退結果。

---
*Owner: G0 (北斗) — AI outputs are advisory only.*
