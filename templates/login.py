"""
車行寶 CRM v5.2 - 登入頁面（美化版）
北斗七星文創數位 × 織明
"""
from typing import Dict, Any

def get_login_html() -> str:
    """生成美化的登入頁面"""
    return '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>車行寶 CRM - 登入</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Noto Sans TC', sans-serif; }
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .glass {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
        }
        .car-icon {
            animation: bounce 2s infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        .input-focus:focus {
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
        }
        .btn-gradient {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: all 0.3s ease;
        }
        .btn-gradient:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
    </style>
</head>
<body class="gradient-bg min-h-screen flex items-center justify-center p-4">
    <div class="glass rounded-2xl shadow-2xl w-full max-w-md p-8">
        <!-- Logo -->
        <div class="text-center mb-8">
            <div class="car-icon text-6xl mb-4">🚗</div>
            <h1 class="text-3xl font-bold text-gray-800">車行寶 CRM</h1>
            <p class="text-gray-500 mt-2">中古車行智能管理系統</p>
        </div>
        
        <!-- 登入表單 -->
        <form id="loginForm" class="space-y-6">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    <span class="flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                        </svg>
                        帳號
                    </span>
                </label>
                <input type="text" id="username" name="username" 
                    class="input-focus w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                    placeholder="請輸入帳號" required>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    <span class="flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                        </svg>
                        密碼
                    </span>
                </label>
                <input type="password" id="password" name="password" 
                    class="input-focus w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:border-purple-500"
                    placeholder="請輸入密碼" required>
            </div>
            
            <div class="flex items-center justify-between">
                <label class="flex items-center">
                    <input type="checkbox" class="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500">
                    <span class="ml-2 text-sm text-gray-600">記住我</span>
                </label>
                <a href="#" class="text-sm text-purple-600 hover:text-purple-800">忘記密碼？</a>
            </div>
            
            <button type="submit" 
                class="btn-gradient w-full py-3 px-4 text-white font-medium rounded-lg">
                登入系統
            </button>
        </form>
        
        <!-- 錯誤訊息 -->
        <div id="errorMsg" class="hidden mt-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm text-center"></div>
        
        <!-- 測試帳號提示 -->
        <div class="mt-6 p-4 bg-blue-50 rounded-lg">
            <p class="text-sm text-blue-800 text-center">
                <strong>測試帳號：</strong> demo / demo1234
            </p>
        </div>
        
        <!-- Footer -->
        <div class="mt-8 text-center text-sm text-gray-500">
            <p>© 2024 北斗七星文創數位</p>
            <p class="mt-1">v5.2 | 技術支援：織明</p>
        </div>
    </div>
    
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorMsg = document.getElementById('errorMsg');
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = '/app';
                } else {
                    errorMsg.textContent = data.error || '登入失敗';
                    errorMsg.classList.remove('hidden');
                }
            } catch (err) {
                errorMsg.textContent = '網路錯誤，請稍後再試';
                errorMsg.classList.remove('hidden');
            }
        });
    </script>
</body>
</html>'''
