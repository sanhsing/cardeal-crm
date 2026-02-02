"""
車行寶 CRM v5.2 - 現代化登入頁面
北斗七星文創數位 × 織明
"""
from typing import Dict, Any

def get_login_html() -> str:
    """生成現代化登入頁面"""
    return '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登入 - 車行寶 CRM</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="stylesheet" href="/static/css/modern.css">
    <style>
        body {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--background);
            margin: 0;
            padding: var(--space-4);
        }
        
        .login-container {
            width: 100%;
            max-width: 420px;
        }
        
        .login-card {
            background: var(--surface);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-lg);
            overflow: hidden;
        }
        
        .login-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: var(--space-6);
            text-align: center;
            color: white;
        }
        
        .login-logo {
            font-size: 48px;
            margin-bottom: var(--space-3);
        }
        
        .login-title {
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 var(--space-2) 0;
        }
        
        .login-subtitle {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .login-form {
            padding: var(--space-6);
        }
        
        .form-group {
            margin-bottom: var(--space-5);
        }
        
        .form-label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: var(--space-2);
        }
        
        .form-input {
            width: 100%;
            padding: var(--space-3) var(--space-4);
            border: 2px solid var(--border);
            border-radius: var(--radius);
            font-size: 15px;
            transition: all 0.3s ease;
            box-sizing: border-box;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }
        
        .login-btn {
            width: 100%;
            padding: var(--space-4);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: var(--radius);
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .login-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }
        
        .login-footer {
            padding: var(--space-4) var(--space-6);
            background: var(--background);
            text-align: center;
            font-size: 13px;
            color: var(--text-secondary);
            border-top: 1px solid var(--border);
        }
        
        .login-footer a {
            color: #667eea;
            text-decoration: none;
        }
        
        .error-message {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
            padding: var(--space-3) var(--space-4);
            border-radius: var(--radius);
            font-size: 13px;
            margin-bottom: var(--space-4);
            display: none;
        }
        
        .theme-switch {
            position: fixed;
            top: var(--space-4);
            right: var(--space-4);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--surface);
            border: 1px solid var(--border);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all 0.3s ease;
        }
        
        .theme-switch:hover {
            transform: scale(1.1);
        }
        
        /* 動畫 */
        .login-card {
            animation: fadeIn 0.5s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <button class="theme-switch" onclick="toggleTheme()" title="切換主題">
        🌙
    </button>
    
    <div class="login-container">
        <div class="login-card glass-card">
            <div class="login-header">
                <div class="login-logo">🚗</div>
                <h1 class="login-title">車行寶 CRM</h1>
                <p class="login-subtitle">中古車行智能管理系統</p>
            </div>
            
            <form class="login-form" id="loginForm">
                <div class="error-message" id="errorMessage"></div>
                
                <div class="form-group">
                    <label class="form-label">車行代碼</label>
                    <input type="text" class="form-input" id="code" 
                           placeholder="輸入車行代碼" required autocomplete="off">
                </div>
                
                <div class="form-group">
                    <label class="form-label">手機號碼</label>
                    <input type="tel" class="form-input" id="phone" 
                           placeholder="09xx-xxx-xxx" required autocomplete="tel">
                </div>
                
                <div class="form-group">
                    <label class="form-label">密碼</label>
                    <input type="password" class="form-input" id="password" 
                           placeholder="輸入密碼" required autocomplete="current-password">
                </div>
                
                <button type="submit" class="login-btn" id="submitBtn">
                    登入系統
                </button>
            </form>
            
            <div class="login-footer">
                還沒有帳號？<a href="/register">立即註冊</a>
            </div>
        </div>
    </div>
    
    <script>
        // 主題切換
        function toggleTheme() {
            const html = document.documentElement;
            const isDark = html.getAttribute('data-theme') === 'dark';
            html.setAttribute('data-theme', isDark ? 'light' : 'dark');
            document.querySelector('.theme-switch').textContent = isDark ? '🌙' : '☀️';
            localStorage.setItem('theme', isDark ? 'light' : 'dark');
        }
        
        // 載入儲存的主題
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        document.querySelector('.theme-switch').textContent = savedTheme === 'dark' ? '☀️' : '🌙';
        
        // 登入表單處理
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const btn = document.getElementById('submitBtn');
            const error = document.getElementById('errorMessage');
            
            btn.disabled = true;
            btn.textContent = '登入中...';
            error.style.display = 'none';
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code: document.getElementById('code').value,
                        phone: document.getElementById('phone').value,
                        password: document.getElementById('password').value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = '/app';
                } else {
                    error.textContent = data.error || '登入失敗，請檢查帳號密碼';
                    error.style.display = 'block';
                }
            } catch (err) {
                error.textContent = '網路錯誤，請稍後再試';
                error.style.display = 'block';
            } finally {
                btn.disabled = false;
                btn.textContent = '登入系統';
            }
        });
    </script>
</body>
</html>'''
