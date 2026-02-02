# Web Push 推播設定指南

## 📋 概述

車行寶 CRM 使用 Web Push 標準推播通知：
- 新客戶通知
- 交易提醒
- 庫存預警
- 系統公告

---

## 🔧 設定步驟

### 1. 生成 VAPID 金鑰

```bash
python scripts/generate_vapid.py
```

輸出範例：
```
VAPID_PUBLIC_KEY=BBLB6Vw...
VAPID_PRIVATE_KEY=4AK33k...
```

### 2. 設定環境變數

**本地開發（.env）**
```bash
VAPID_PUBLIC_KEY=BBLB6VwPWNCwcmYeN_XFa-q9_QT3EDuLNGjgB6k9vyedDr2MPLW410Ng_FVZcmjb8xhiTeAkhbyg20iZEpqex0w
VAPID_PRIVATE_KEY=4AK33k_-3A_okq860_KjdxBs10n2Xq39EMXKs0sYRMM
VAPID_SUBJECT=mailto:admin@your-domain.com
```

**Render 部署**
在 Environment 添加以上變數

### 3. 前端配置（已完成）

`static/js/pwa.js` 已配置 VAPID 公鑰

---

## 📱 API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/push/vapid-key` | GET | 取得公鑰 |
| `/api/push/subscribe` | POST | 訂閱推播 |
| `/api/push/unsubscribe` | POST | 取消訂閱 |
| `/api/push/send` | POST | 發送推播 |
| `/api/push/broadcast` | POST | 廣播推播 |
| `/api/push/stats` | GET | 訂閱統計 |

---

## 🔔 使用範例

### 前端訂閱

```javascript
// 請求通知權限並訂閱
await PWA.requestNotification();
```

### 後端發送推播

```python
from services import push_service

# 發送給指定用戶
push_service.send_push(
    db_path='data/cardeal.db',
    user_id=1,
    title='新客戶通知',
    body='張先生對 Toyota Altis 有興趣',
    url='/app#customers/1'
)

# 廣播給所有用戶
push_service.broadcast_push(
    db_path='data/cardeal.db',
    title='系統公告',
    body='新功能上線！',
    tenant_id=1  # 可選，指定店家
)
```

---

## ⚠️ 注意事項

1. **HTTPS 必要**：Web Push 只在 HTTPS 下運作
2. **用戶授權**：需要用戶同意通知權限
3. **金鑰安全**：私鑰不要外洩
4. **訂閱過期**：410 錯誤表示訂閱已失效，會自動清理

---

## 🔍 測試推播

### 瀏覽器測試

1. 打開網站（需 HTTPS）
2. 打開開發者工具 → Application → Service Workers
3. 在 Console 執行：`await PWA.requestNotification()`
4. 允許通知權限

### API 測試

```bash
# 發送測試推播
curl -X POST https://your-domain.com/api/push/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "title": "測試推播",
    "body": "這是一則測試通知"
  }'
```

---

## 📚 參考資源

- [Web Push Protocol](https://tools.ietf.org/html/rfc8030)
- [VAPID](https://tools.ietf.org/html/rfc8292)
- [Push API MDN](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
