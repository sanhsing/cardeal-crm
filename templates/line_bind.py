"""車行寶 CRM v5.0 - LINE 綁定頁面"""
def render(tenant_id, token):
    return f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LINE 帳號綁定 - 車行寶</title>
    <style>
        body {{ 
            font-family: 'Noto Sans TC', sans-serif; 
            background: #06c755; 
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }}
        .card {{
            background: white;
            padding: 40px;
            border-radius: 16px;
            text-align: center;
            max-width: 400px;
            margin: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .logo {{ font-size: 4rem; margin-bottom: 1rem; }}
        h1 {{ color: #1e3a5f; margin-bottom: 0.5rem; }}
        p {{ color: #666; margin-bottom: 2rem; }}
        .btn {{
            display: inline-block;
            background: #06c755;
            color: white;
            padding: 14px 40px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 500;
            transition: background 0.3s;
        }}
        .btn:hover {{ background: #05a648; }}
        .note {{ font-size: 0.85rem; color: #999; margin-top: 1.5rem; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">💬</div>
        <h1>LINE 帳號綁定</h1>
        <p>綁定後，您將收到交易通知、優惠資訊等訊息</p>
        <a href="https://line.me/R/ti/p/@yourbot" class="btn">確認綁定</a>
        <p class="note">綁定即表示您同意我們的服務條款與隱私政策</p>
    </div>
</body>
</html>'''
