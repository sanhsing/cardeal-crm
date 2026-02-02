"""
車行寶 CRM v5.0 - 首頁模板
北斗七星文創數位 × 織明
"""
import config

def render():
    return f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.APP_NAME} - 車行管理專家</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        :root {{
            --primary: {config.THEME['primary']};
            --primary-light: {config.THEME['primary_light']};
            --accent: {config.THEME['accent']};
            --success: {config.THEME['success']};
            --text: {config.THEME['text']};
            --text-secondary: {config.THEME['text_secondary']};
            --background: {config.THEME['background']};
            --surface: {config.THEME['surface']};
            --border: {config.THEME['border']};
        }}
        
        body {{
            font-family: 'Noto Sans TC', -apple-system, sans-serif;
            background: var(--background);
            color: var(--text);
            line-height: 1.6;
        }}
        
        /* Hero Section */
        .hero {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            color: white;
            padding: 80px 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .hero::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        }}
        
        .hero-content {{
            position: relative;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .hero h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }}
        
        .hero p {{
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 2rem;
        }}
        
        .btn {{
            display: inline-block;
            padding: 14px 32px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.3s ease;
            cursor: pointer;
            border: none;
        }}
        
        .btn-primary {{
            background: var(--accent);
            color: white;
        }}
        
        .btn-primary:hover {{
            background: {config.THEME['accent_hover']};
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(238, 108, 77, 0.4);
        }}
        
        .btn-outline {{
            background: transparent;
            color: white;
            border: 2px solid rgba(255,255,255,0.5);
            margin-left: 1rem;
        }}
        
        .btn-outline:hover {{
            background: rgba(255,255,255,0.1);
            border-color: white;
        }}
        
        /* Features */
        .features {{
            padding: 80px 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .features h2 {{
            text-align: center;
            font-size: 2rem;
            margin-bottom: 3rem;
            color: var(--primary);
        }}
        
        .feature-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
        }}
        
        .feature-card {{
            background: var(--surface);
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .feature-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }}
        
        .feature-icon {{
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }}
        
        .feature-card h3 {{
            font-size: 1.25rem;
            margin-bottom: 0.5rem;
            color: var(--text);
        }}
        
        .feature-card p {{
            color: var(--text-secondary);
            font-size: 0.95rem;
        }}
        
        /* Pricing */
        .pricing {{
            background: var(--primary);
            padding: 80px 20px;
            color: white;
        }}
        
        .pricing h2 {{
            text-align: center;
            font-size: 2rem;
            margin-bottom: 3rem;
        }}
        
        .pricing-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            max-width: 900px;
            margin: 0 auto;
        }}
        
        .pricing-card {{
            background: var(--surface);
            color: var(--text);
            padding: 2.5rem;
            border-radius: 16px;
            text-align: center;
        }}
        
        .pricing-card.featured {{
            transform: scale(1.05);
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        .pricing-card h3 {{
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .pricing-card .price {{
            font-size: 3rem;
            font-weight: 700;
            color: var(--primary);
            margin: 1rem 0;
        }}
        
        .pricing-card .price span {{
            font-size: 1rem;
            font-weight: 400;
            color: var(--text-secondary);
        }}
        
        .pricing-card ul {{
            list-style: none;
            margin: 1.5rem 0;
            text-align: left;
        }}
        
        .pricing-card li {{
            padding: 0.5rem 0;
            color: var(--text-secondary);
        }}
        
        .pricing-card li::before {{
            content: '✓';
            color: var(--success);
            margin-right: 0.5rem;
            font-weight: bold;
        }}
        
        /* Login Modal */
        .modal {{
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            align-items: center;
            justify-content: center;
            z-index: 1000;
            backdrop-filter: blur(4px);
        }}
        
        .modal.active {{
            display: flex;
        }}
        
        .modal-content {{
            background: var(--surface);
            padding: 2.5rem;
            border-radius: 16px;
            width: 100%;
            max-width: 400px;
            margin: 20px;
            position: relative;
        }}
        
        .modal-close {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--text-secondary);
        }}
        
        .modal h2 {{
            margin-bottom: 1.5rem;
            text-align: center;
            color: var(--primary);
        }}
        
        .form-group {{
            margin-bottom: 1rem;
        }}
        
        .form-group label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--text);
        }}
        
        .form-group input {{
            width: 100%;
            padding: 12px 16px;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }}
        
        .form-group input:focus {{
            outline: none;
            border-color: var(--primary);
        }}
        
        .form-error {{
            color: var(--error);
            font-size: 0.9rem;
            margin-top: 0.5rem;
            display: none;
        }}
        
        .btn-full {{
            width: 100%;
            margin-top: 1rem;
        }}
        
        .tabs {{
            display: flex;
            margin-bottom: 1.5rem;
            border-bottom: 2px solid var(--border);
        }}
        
        .tab {{
            flex: 1;
            padding: 1rem;
            text-align: center;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
            transition: all 0.3s ease;
        }}
        
        .tab.active {{
            border-color: var(--primary);
            color: var(--primary);
            font-weight: 500;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        /* Footer */
        footer {{
            background: var(--text);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}
        
        footer a {{
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            margin: 0 1rem;
        }}
        
        footer a:hover {{
            color: white;
        }}
        
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 1.8rem; }}
            .hero p {{ font-size: 1rem; }}
            .btn-outline {{ margin-left: 0; margin-top: 1rem; display: block; }}
            .pricing-card.featured {{ transform: none; }}
        }}
    </style>
</head>
<body>
    <!-- Hero -->
    <section class="hero">
        <div class="hero-content">
            <h1>🚗 {config.APP_NAME}</h1>
            <p>專為中古車行打造的智慧管理系統<br>客戶管理、車輛庫存、交易追蹤、LINE 整合</p>
            <a href="#" class="btn btn-primary" onclick="showModal('login')">立即開始</a>
            <a href="#features" class="btn btn-outline">了解更多</a>
        </div>
    </section>
    
    <!-- Features -->
    <section class="features" id="features">
        <h2>為什麼選擇車行寶？</h2>
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">👥</div>
                <h3>客戶管理</h3>
                <p>完整的客戶資料管理，標籤分類、跟進提醒，不漏接任何商機</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🚙</div>
                <h3>車輛庫存</h3>
                <p>清楚掌握每台車的成本、利潤、狀態，庫存管理一目了然</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💰</div>
                <h3>交易追蹤</h3>
                <p>買入賣出完整記錄，自動計算利潤，報表一鍵生成</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <h3>LINE 整合</h3>
                <p>客戶綁定 LINE，交易通知自動推送，提升服務體驗</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3>智慧報表</h3>
                <p>營收分析、客戶分析、庫存週轉，數據驅動決策</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">☁️</div>
                <h3>雲端備份</h3>
                <p>資料自動備份，多設備同步，安全又方便</p>
            </div>
        </div>
    </section>
    
    <!-- Pricing -->
    <section class="pricing" id="pricing">
        <h2>簡單透明的定價</h2>
        <div class="pricing-grid">
            <div class="pricing-card">
                <h3>免費版</h3>
                <div class="price">$0<span>/月</span></div>
                <ul>
                    <li>客戶管理（100位）</li>
                    <li>車輛管理（50台）</li>
                    <li>交易記錄</li>
                    <li>基本報表</li>
                </ul>
                <a href="#" class="btn btn-primary btn-full" onclick="showModal('register')">免費註冊</a>
            </div>
            <div class="pricing-card featured">
                <h3>專業版</h3>
                <div class="price">$299<span>/月</span></div>
                <ul>
                    <li>無限客戶</li>
                    <li>無限車輛</li>
                    <li>LINE 整合</li>
                    <li>進階報表</li>
                    <li>自動備份</li>
                    <li>Excel 匯出</li>
                    <li>優先支援</li>
                </ul>
                <a href="#" class="btn btn-primary btn-full" onclick="showModal('register')">開始試用</a>
            </div>
        </div>
    </section>
    
    <!-- Footer -->
    <footer>
        <p>© 2026 北斗七星文創數位有限公司</p>
        <p style="margin-top: 1rem;">
            <a href="/privacy">隱私政策</a>
            <a href="/terms">服務條款</a>
        </p>
    </footer>
    
    <!-- Login/Register Modal -->
    <div class="modal" id="modal">
        <div class="modal-content">
            <button class="modal-close" onclick="hideModal()">&times;</button>
            
            <div class="tabs">
                <div class="tab active" onclick="switchTab('login')">登入</div>
                <div class="tab" onclick="switchTab('register')">註冊</div>
            </div>
            
            <!-- Login Form -->
            <div class="tab-content active" id="login-form">
                <form onsubmit="handleLogin(event)">
                    <div class="form-group">
                        <label>店家代碼</label>
                        <input type="text" id="login-code" placeholder="例：myshop" required>
                    </div>
                    <div class="form-group">
                        <label>手機號碼</label>
                        <input type="tel" id="login-phone" placeholder="0912345678" required>
                    </div>
                    <div class="form-group">
                        <label>密碼</label>
                        <input type="password" id="login-password" required>
                    </div>
                    <div class="form-error" id="login-error"></div>
                    <button type="submit" class="btn btn-primary btn-full">登入</button>
                </form>
            </div>
            
            <!-- Register Form -->
            <div class="tab-content" id="register-form">
                <form onsubmit="handleRegister(event)">
                    <div class="form-group">
                        <label>店家代碼</label>
                        <input type="text" id="reg-code" placeholder="小寫英數字，3-20字元" required pattern="[a-z0-9_]{{3,20}}">
                    </div>
                    <div class="form-group">
                        <label>店家名稱</label>
                        <input type="text" id="reg-name" placeholder="例：小明車行" required>
                    </div>
                    <div class="form-group">
                        <label>手機號碼</label>
                        <input type="tel" id="reg-phone" placeholder="0912345678" required>
                    </div>
                    <div class="form-group">
                        <label>密碼</label>
                        <input type="password" id="reg-password" placeholder="至少4位" required minlength="4">
                    </div>
                    <div class="form-error" id="reg-error"></div>
                    <button type="submit" class="btn btn-primary btn-full">註冊</button>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        function showModal(tab) {{
            document.getElementById('modal').classList.add('active');
            switchTab(tab);
        }}
        
        function hideModal() {{
            document.getElementById('modal').classList.remove('active');
        }}
        
        function switchTab(tab) {{
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            document.querySelector(`.tab:nth-child(${{tab === 'login' ? 1 : 2}})`).classList.add('active');
            document.getElementById(tab + '-form').classList.add('active');
        }}
        
        async function handleLogin(e) {{
            e.preventDefault();
            const error = document.getElementById('login-error');
            error.style.display = 'none';
            
            const data = {{
                code: document.getElementById('login-code').value,
                phone: document.getElementById('login-phone').value,
                password: document.getElementById('login-password').value
            }};
            
            try {{
                const resp = await fetch('/api/login', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(data)
                }});
                const result = await resp.json();
                
                if (result.success) {{
                    localStorage.setItem('token', result.token);
                    localStorage.setItem('user', JSON.stringify(result));
                    window.location.href = '/app';
                }} else {{
                    error.textContent = result.error;
                    error.style.display = 'block';
                }}
            }} catch (err) {{
                error.textContent = '連線錯誤，請稍後再試';
                error.style.display = 'block';
            }}
        }}
        
        async function handleRegister(e) {{
            e.preventDefault();
            const error = document.getElementById('reg-error');
            error.style.display = 'none';
            
            const data = {{
                code: document.getElementById('reg-code').value.toLowerCase(),
                name: document.getElementById('reg-name').value,
                phone: document.getElementById('reg-phone').value,
                password: document.getElementById('reg-password').value
            }};
            
            try {{
                const resp = await fetch('/api/register', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(data)
                }});
                const result = await resp.json();
                
                if (result.success) {{
                    alert('註冊成功！請使用您的帳號登入。');
                    switchTab('login');
                    document.getElementById('login-code').value = data.code;
                    document.getElementById('login-phone').value = data.phone;
                }} else {{
                    error.textContent = result.error;
                    error.style.display = 'block';
                }}
            }} catch (err) {{
                error.textContent = '連線錯誤，請稍後再試';
                error.style.display = 'block';
            }}
        }}
        
        // 檢查是否已登入
        if (localStorage.getItem('token')) {{
            window.location.href = '/app';
        }}
    </script>
</body>
</html>'''
