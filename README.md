# 車行寶 CRM v5.1

> 中古車商專用客戶關係管理系統  
> 北斗七星文創數位 × 織明

## 📋 功能特色

### 核心功能
- 👥 客戶管理：客戶資料、跟進記錄、等級分類
- 🚗 車輛庫存：收購登記、庫存管理、成本追蹤
- 💰 交易記錄：買賣登記、利潤計算、報表分析
- 📊 數據報表：銷售統計、庫存分析、客戶分析

### 整合服務
- 📱 LINE 整合：客戶綁定、訊息推播
- 💳 ECPay 金流：訂閱付款
- 📨 Telegram 通知：系統警報

### 進階功能
- 📈 車價估算：自動估價、市場行情
- 📤 Excel 匯出入：批量資料處理
- 🔒 安全防護：CSRF、Rate Limit、XSS
- 📝 完整日誌：請求日誌、審計日誌
- ⏰ 排程任務：自動備份、清理任務

## 🏗️ 架構說明

```
cardeal_v5/
├── main.py              # 應用入口
├── config.py            # 基本配置
├── config_manager.py    # 進階配置管理
├── deploy.sh            # 部署腳本
│
├── models/              # 資料層
│   ├── database.py      # 資料庫連線
│   ├── schema.py        # 表結構定義
│   ├── tenant.py        # 租戶管理
│   ├── session.py       # Session 管理
│   └── db_utils.py      # 資料庫工具
│
├── services/            # 服務層
│   ├── line_service.py       # LINE 整合
│   ├── ecpay_service.py      # ECPay 金流
│   ├── telegram_service.py   # Telegram 通知
│   ├── backup_service.py     # 備份服務
│   ├── excel_service.py      # Excel 處理
│   ├── price_service.py      # 車價估算
│   ├── security_service.py   # 安全服務
│   ├── cache_service.py      # 快取服務
│   ├── logger_service.py     # 日誌服務
│   ├── monitor_service.py    # 監控服務
│   └── scheduler_service.py  # 排程服務
│
├── handlers/            # 處理層
│   ├── base.py          # 基礎工具
│   ├── middleware.py    # 中間件
│   ├── router.py        # 路由分發
│   └── *_handler.py     # 各功能處理器
│
├── templates/           # 頁面模板
├── static/              # 靜態資源
├── tests/               # 測試
└── docs/                # 文件
```

## 🚀 快速開始

### 環境需求
- Python 3.8+
- SQLite 3

### 安裝步驟

```bash
# 1. 安裝並初始化
chmod +x deploy.sh
./deploy.sh install

# 2. 設定環境變數（可選）
export LINE_CHANNEL_SECRET=your_secret
export TELEGRAM_BOT_TOKEN=your_token

# 3. 啟動服務
./deploy.sh start
```

### 開發模式

```bash
./deploy.sh dev
# 訪問 http://localhost:8000
```

## ⚙️ 環境變數

| 變數名 | 說明 | 預設值 |
|--------|------|--------|
| ENV | 環境 | development |
| HOST | 監聽地址 | 0.0.0.0 |
| PORT | 監聽埠號 | 10000 |
| DEBUG | 除錯模式 | true |
| DATA_DIR | 資料目錄 | ./data |

## 📡 API 端點

### 認證
- `POST /api/login` - 登入
- `POST /api/register` - 註冊
- `POST /api/logout` - 登出

### 客戶
- `GET /api/customers` - 列表
- `POST /api/customers` - 新增
- `POST /api/customers/{id}/update` - 更新

### 車輛
- `GET /api/vehicles` - 列表
- `POST /api/vehicles` - 新增

### 系統
- `GET /api/health` - 健康檢查
- `GET /api/stats` - 統計數據

## 🔒 安全功能

- CSRF 防護
- Rate Limit
- PBKDF2 密碼雜湊
- XSS 防護
- CSP 安全策略

## 🧪 測試

```bash
./deploy.sh test
# 或
make test
```

## 🐳 Docker 部署

### 使用 Docker Compose（推薦）

```bash
# 1. 複製環境變數範例
cp .env.example .env

# 2. 編輯 .env 填入實際值
nano .env

# 3. 啟動
docker-compose up -d

# 4. 查看日誌
docker-compose logs -f

# 5. 停止
docker-compose down
```

### 使用 Docker

```bash
# 建置映像
docker build -t cardeal-crm .

# 啟動容器
docker run -d \
  --name cardeal \
  -p 10000:10000 \
  -v $(pwd)/data:/app/data \
  cardeal-crm
```

## 🔄 CI/CD

專案已配置 GitHub Actions：

- **CI**（ci.yml）：語法檢查 → 測試 → 建置
- **CD**（cd.yml）：標籤觸發 → 部署到 Render

### 觸發部署

```bash
# 建立版本標籤觸發部署
git tag v5.1.1
git push origin v5.1.1
```

## 📝 更新日誌

### v5.1.0 (2026-02-02)
- 🛡️ 安全服務（CSRF、Rate Limit、XSS 防護）
- 💾 快取服務（LRU Cache + TTL）
- 🔄 中間件（GZIP、CORS、CSP）
- 📊 監控服務（健康檢查、效能指標）
- ⏰ 排程任務（自動備份、清理）
- 📈 圖表 API（銷售、庫存、客戶分析）
- 🔔 提醒服務（跟進到期、冷淡客戶）
- 📦 批量操作（批量刪除、更新、調價）
- 🖼️ 圖片上傳（壓縮、縮圖）
- 🐳 Docker 化（Dockerfile + Compose）
- 🔄 CI/CD（GitHub Actions）
- 📝 日誌系統（JSON 格式、輪替）
- 🧪 測試框架（pytest）
- 📚 API 文件

---

🐝 ☯ 織明
