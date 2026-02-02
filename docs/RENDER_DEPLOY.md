# Render 部署指南

## 📋 概述

車行寶 CRM v5.2 部署到 Render 的完整步驟。

---

## 🚀 快速部署（Blueprint）

### 方法 1：一鍵部署

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### 方法 2：手動部署

1. Fork 或上傳代碼到 GitHub
2. 登入 [Render Dashboard](https://dashboard.render.com/)
3. New → Web Service
4. 連接 GitHub 倉庫
5. 設定如下

---

## ⚙️ 部署設定

### 基本設定

| 項目 | 值 |
|------|-----|
| Name | cardeal-crm |
| Region | Singapore |
| Branch | main |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python main.py` |

### 環境變數（必要）

| Key | 說明 | 範例 |
|-----|------|------|
| `ENV` | 環境 | `production` |
| `DEBUG` | 除錯 | `false` |
| `PORT` | 埠號 | `10000` |
| `SECRET_KEY` | 密鑰 | 自動生成或自訂 |

### 環境變數（AI 功能）

| Key | 說明 |
|-----|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `OPENAI_API_KEY` | OpenAI API Key（備用） |
| `AI_PROVIDER` | `deepseek` 或 `openai` |

### 環境變數（LINE 整合）

| Key | 說明 |
|-----|------|
| `LINE_CHANNEL_SECRET` | LINE Channel Secret |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Access Token |

### 環境變數（推播通知）

| Key | 值 |
|-----|-----|
| `VAPID_PUBLIC_KEY` | `BBLB6VwPWNCwcmYeN_XFa-q9_QT3EDuLNGjgB6k9vyedDr2MPLW410Ng_FVZcmjb8xhiTeAkhbyg20iZEpqex0w` |
| `VAPID_PRIVATE_KEY` | `4AK33k_-3A_okq860_KjdxBs10n2Xq39EMXKs0sYRMM` |
| `VAPID_SUBJECT` | `mailto:admin@your-domain.com` |

---

## 📝 部署步驟

### Step 1: 準備代碼

```bash
# 解壓縮
unzip cardeal_v5.2_p12_20260202.zip -d cardeal-crm
cd cardeal-crm

# 初始化 Git
git init
git add .
git commit -m "車行寶 CRM v5.2"
```

### Step 2: 推送到 GitHub

```bash
# 建立 GitHub 倉庫後
git remote add origin https://github.com/YOUR_USERNAME/cardeal-crm.git
git push -u origin main
```

### Step 3: 連接 Render

1. 登入 Render Dashboard
2. New → Web Service
3. 選擇剛建立的 GitHub 倉庫
4. 填寫設定（見上方表格）
5. 點擊「Create Web Service」

### Step 4: 設定環境變數

1. 在 Service 頁面 → Environment
2. 添加必要的環境變數
3. 點擊「Save Changes」

### Step 5: 部署

Render 會自動部署，等待完成即可。

---

## 🔍 驗證部署

### 健康檢查

```bash
curl https://cardeal-crm.onrender.com/api/system/health
```

預期回應：
```json
{
  "success": true,
  "status": "healthy",
  "checks": {
    "database": "ok",
    "disk": "ok"
  }
}
```

### 測試登入

1. 訪問 `https://cardeal-crm.onrender.com`
2. 預設測試帳號：
   - 帳號：`demo`
   - 密碼：`demo1234`

---

## 🔧 LINE Webhook 設定

部署後，在 LINE Developers Console 設定：

```
Webhook URL: https://cardeal-crm.onrender.com/api/webhook/line
```

---

## ⚠️ 注意事項

### Free Plan 限制

- 15 分鐘無請求會休眠
- 每月 750 小時免費
- 磁碟空間有限

### 數據持久化

- Free Plan 重新部署會清除數據
- 建議使用外部數據庫或升級 Plan

### 喚醒服務

可設定 UptimeRobot 定期 ping：
```
https://cardeal-crm.onrender.com/api/system/health
```

---

## 📚 相關資源

- [Render 文檔](https://render.com/docs)
- [Python on Render](https://render.com/docs/deploy-python)
- [環境變數設定](https://render.com/docs/environment-variables)
