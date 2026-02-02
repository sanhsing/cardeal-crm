# LINE Messaging API 設定指南

## 📋 概述

車行寶 CRM 整合 LINE Messaging API，提供：
- 自動回覆客戶訊息
- 推播通知
- 帳號綁定

---

## 🔧 設定步驟

### 1. 建立 LINE Developers 帳號

1. 訪問 [LINE Developers Console](https://developers.line.biz/console/)
2. 使用 LINE 帳號登入
3. 同意開發者條款

### 2. 建立 Provider

1. 點擊「Create」
2. 輸入 Provider 名稱（如：車行寶）
3. 點擊「Create」

### 3. 建立 Messaging API Channel

1. 在 Provider 下點擊「Create a new channel」
2. 選擇「Messaging API」
3. 填寫資訊：
   - Channel name: 車行寶 CRM
   - Channel description: 中古車行客戶管理系統
   - Category: 汽車
   - Subcategory: 中古車
4. 同意條款並建立

### 4. 取得憑證

在 Channel 設定頁面取得：

| 項目 | 位置 | 環境變數 |
|------|------|----------|
| Channel Secret | Basic settings | `LINE_CHANNEL_SECRET` |
| Channel Access Token | Messaging API | `LINE_CHANNEL_ACCESS_TOKEN` |

**注意**：Access Token 需要點擊「Issue」生成

### 5. 設定 Webhook

1. 在「Messaging API」頁籤
2. 找到「Webhook settings」
3. 設定 Webhook URL：

```
https://your-domain.com/api/webhook/line
```

例如 Render 部署後：
```
https://cardeal-crm.onrender.com/api/webhook/line
```

4. 開啟「Use webhook」
5. 點擊「Verify」測試連接

### 6. 關閉自動回覆

1. 在「Messaging API」頁籤
2. 找到「LINE Official Account features」
3. 點擊「Edit」
4. 關閉「Auto-reply messages」
5. 關閉「Greeting messages」

---

## 📝 環境變數設定

### 本地開發（.env）

```bash
LINE_CHANNEL_SECRET=your-channel-secret
LINE_CHANNEL_ACCESS_TOKEN=your-channel-access-token
LINE_LOGIN_CHANNEL_ID=your-login-channel-id
```

### Render 部署

在 Render Dashboard → Environment 添加：

| Key | Value |
|-----|-------|
| `LINE_CHANNEL_SECRET` | 從 LINE Developers 複製 |
| `LINE_CHANNEL_ACCESS_TOKEN` | 從 LINE Developers 複製 |

---

## 🔍 驗證設定

### 測試 API 連接

```bash
python scripts/test_apis.py
```

### 手動測試 Webhook

```bash
curl -X POST https://your-domain.com/api/webhook/line \
  -H "Content-Type: application/json" \
  -d '{"events":[]}'
```

### 測試回覆

1. 加入 LINE 官方帳號
2. 發送「你好」
3. 應收到歡迎訊息

---

## 📱 功能說明

### 支援的事件

| 事件 | 說明 | 處理 |
|------|------|------|
| message | 訊息 | 關鍵字回覆 |
| follow | 追蹤 | 歡迎訊息 |
| unfollow | 取消追蹤 | 記錄 |
| postback | 按鈕點擊 | 動作處理 |

### 關鍵字回覆

| 關鍵字 | 回覆 |
|--------|------|
| 你好/hi/hello | 歡迎訊息 |
| 幫助/help | 功能列表 |
| 查詢 | 查詢引導 |
| 綁定 | 綁定連結 |
| 客服 | 聯繫方式 |

---

## ⚠️ 常見問題

### Webhook 驗證失敗

1. 確認 URL 正確（含 https）
2. 確認伺服器已啟動
3. 確認 Channel Secret 正確

### 訊息未回覆

1. 確認 Webhook 已開啟
2. 確認自動回覆已關閉
3. 檢查伺服器日誌

### 簽名驗證失敗

1. 確認 Channel Secret 正確
2. 確認環境變數已載入

---

## 📚 參考資源

- [LINE Messaging API 文檔](https://developers.line.biz/en/docs/messaging-api/)
- [Webhook 事件類型](https://developers.line.biz/en/reference/messaging-api/#webhook-event-objects)
- [Reply API](https://developers.line.biz/en/reference/messaging-api/#send-reply-message)
