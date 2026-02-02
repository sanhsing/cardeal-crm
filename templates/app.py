"""
車行寶 CRM v5.0 - 主應用模板
北斗七星文創數位 × 織明
UI/UX 優化版
"""
import config

def render():
    return f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.APP_NAME}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        :root {{
            --primary: {config.THEME['primary']};
            --primary-light: {config.THEME['primary_light']};
            --accent: {config.THEME['accent']};
            --success: {config.THEME['success']};
            --warning: {config.THEME['warning']};
            --error: {config.THEME['error']};
            --info: {config.THEME['info']};
            --text: {config.THEME['text']};
            --text-secondary: {config.THEME['text_secondary']};
            --background: {config.THEME['background']};
            --surface: {config.THEME['surface']};
            --border: {config.THEME['border']};
            --sidebar-width: 260px;
        }}
        
        body {{
            font-family: 'Noto Sans TC', -apple-system, sans-serif;
            background: var(--background);
            color: var(--text);
            line-height: 1.5;
        }}
        
        /* Layout */
        .app {{
            display: flex;
            min-height: 100vh;
        }}
        
        /* Sidebar */
        .sidebar {{
            width: var(--sidebar-width);
            background: var(--primary);
            color: white;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            transition: transform 0.3s ease;
            z-index: 100;
        }}
        
        .sidebar-header {{
            padding: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .sidebar-header h1 {{
            font-size: 1.25rem;
            font-weight: 600;
        }}
        
        .sidebar-header .tenant {{
            font-size: 0.85rem;
            opacity: 0.8;
            margin-top: 4px;
        }}
        
        .sidebar-nav {{
            padding: 20px 0;
        }}
        
        .nav-item {{
            display: flex;
            align-items: center;
            padding: 12px 20px;
            color: rgba(255,255,255,0.8);
            text-decoration: none;
            transition: all 0.2s ease;
            cursor: pointer;
            border-left: 3px solid transparent;
        }}
        
        .nav-item:hover {{
            background: rgba(255,255,255,0.1);
            color: white;
        }}
        
        .nav-item.active {{
            background: rgba(255,255,255,0.15);
            color: white;
            border-left-color: var(--accent);
        }}
        
        .nav-item .icon {{
            width: 24px;
            margin-right: 12px;
            text-align: center;
        }}
        
        .nav-divider {{
            height: 1px;
            background: rgba(255,255,255,0.1);
            margin: 10px 20px;
        }}
        
        /* Main Content */
        .main {{
            flex: 1;
            margin-left: var(--sidebar-width);
            min-height: 100vh;
        }}
        
        /* Header */
        .header {{
            background: var(--surface);
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 50;
        }}
        
        .header-left {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        
        .menu-toggle {{
            display: none;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 8px;
        }}
        
        .page-title {{
            font-size: 1.25rem;
            font-weight: 600;
        }}
        
        .header-right {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        
        .user-menu {{
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            padding: 8px 12px;
            border-radius: 8px;
            transition: background 0.2s;
        }}
        
        .user-menu:hover {{
            background: var(--background);
        }}
        
        /* Content Area */
        .content {{
            padding: 24px;
        }}
        
        /* Stats Cards */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}
        
        .stat-card {{
            background: var(--surface);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .stat-card .label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }}
        
        .stat-card .value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
        }}
        
        .stat-card .change {{
            font-size: 0.85rem;
            margin-top: 8px;
        }}
        
        .stat-card .change.positive {{ color: var(--success); }}
        .stat-card .change.negative {{ color: var(--error); }}
        
        /* Cards */
        .card {{
            background: var(--surface);
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 24px;
        }}
        
        .card-header {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .card-title {{
            font-size: 1rem;
            font-weight: 600;
        }}
        
        .card-body {{
            padding: 20px;
        }}
        
        /* Tables */
        .table-wrapper {{
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        
        th {{
            font-weight: 500;
            color: var(--text-secondary);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        tr:hover {{
            background: var(--background);
        }}
        
        /* Buttons */
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
        }}
        
        .btn-primary {{
            background: var(--primary);
            color: white;
        }}
        
        .btn-primary:hover {{
            background: var(--primary-light);
        }}
        
        .btn-accent {{
            background: var(--accent);
            color: white;
        }}
        
        .btn-accent:hover {{
            background: {config.THEME['accent_hover']};
        }}
        
        .btn-outline {{
            background: transparent;
            border: 2px solid var(--border);
            color: var(--text);
        }}
        
        .btn-outline:hover {{
            border-color: var(--primary);
            color: var(--primary);
        }}
        
        .btn-sm {{
            padding: 6px 12px;
            font-size: 0.8rem;
        }}
        
        /* Status Badges */
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        
        .badge-success {{ background: #dcfce7; color: #166534; }}
        .badge-warning {{ background: #fef3c7; color: #92400e; }}
        .badge-info {{ background: #dbeafe; color: #1e40af; }}
        .badge-default {{ background: #f1f5f9; color: #475569; }}
        
        /* Forms */
        .form-group {{
            margin-bottom: 16px;
        }}
        
        .form-label {{
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            font-size: 0.9rem;
        }}
        
        .form-input {{
            width: 100%;
            padding: 10px 14px;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 0.95rem;
            transition: border-color 0.2s;
        }}
        
        .form-input:focus {{
            outline: none;
            border-color: var(--primary);
        }}
        
        .form-select {{
            width: 100%;
            padding: 10px 14px;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 0.95rem;
            background: white;
            cursor: pointer;
        }}
        
        /* Modal */
        .modal {{
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            align-items: center;
            justify-content: center;
            z-index: 200;
            backdrop-filter: blur(4px);
        }}
        
        .modal.active {{ display: flex; }}
        
        .modal-content {{
            background: var(--surface);
            border-radius: 16px;
            width: 100%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
            margin: 20px;
        }}
        
        .modal-header {{
            padding: 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .modal-title {{
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        .modal-close {{
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--text-secondary);
            padding: 4px;
        }}
        
        .modal-body {{
            padding: 20px;
        }}
        
        .modal-footer {{
            padding: 16px 20px;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: flex-end;
            gap: 12px;
        }}
        
        /* Search */
        .search-box {{
            position: relative;
        }}
        
        .search-box input {{
            padding-left: 40px;
        }}
        
        .search-box .icon {{
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
        }}
        
        /* Toolbar */
        .toolbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 12px;
        }}
        
        .toolbar-left {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
        }}
        
        .empty-state .icon {{
            font-size: 4rem;
            margin-bottom: 16px;
            opacity: 0.5;
        }}
        
        /* Toast Notifications */
        .toast-container {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 300;
        }}
        
        .toast {{
            background: var(--surface);
            padding: 14px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideIn 0.3s ease;
        }}
        
        .toast.success {{ border-left: 4px solid var(--success); }}
        .toast.error {{ border-left: 4px solid var(--error); }}
        .toast.warning {{ border-left: 4px solid var(--warning); }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .sidebar {{
                transform: translateX(-100%);
            }}
            
            .sidebar.open {{
                transform: translateX(0);
            }}
            
            .main {{
                margin-left: 0;
            }}
            
            .menu-toggle {{
                display: block;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
        
        /* Loading */
        .loading {{
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
        }}
        
        .spinner {{
            width: 40px;
            height: 40px;
            border: 3px solid var(--border);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Tabs */
        .tabs {{
            display: flex;
            border-bottom: 2px solid var(--border);
            margin-bottom: 20px;
        }}
        
        .tab {{
            padding: 12px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
            color: var(--text-secondary);
            transition: all 0.2s;
        }}
        
        .tab:hover {{
            color: var(--text);
        }}
        
        .tab.active {{
            color: var(--primary);
            border-bottom-color: var(--primary);
            font-weight: 500;
        }}
        
        /* Page Sections */
        .page {{ display: none; }}
        .page.active {{ display: block; }}
    </style>
</head>
<body>
    <div class="app">
        <!-- Sidebar -->
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h1>🚗 {config.APP_NAME}</h1>
                <div class="tenant" id="tenant-name">載入中...</div>
            </div>
            <nav class="sidebar-nav">
                <a class="nav-item active" data-page="dashboard">
                    <span class="icon">📊</span> 儀表板
                </a>
                <a class="nav-item" data-page="customers">
                    <span class="icon">👥</span> 客戶管理
                </a>
                <a class="nav-item" data-page="vehicles">
                    <span class="icon">🚙</span> 車輛庫存
                </a>
                <a class="nav-item" data-page="deals">
                    <span class="icon">💰</span> 交易記錄
                </a>
                <a class="nav-item" data-page="followups">
                    <span class="icon">📋</span> 跟進提醒
                </a>
                <div class="nav-divider"></div>
                <a class="nav-item" data-page="reports">
                    <span class="icon">📈</span> 報表分析
                </a>
                <a class="nav-item" data-page="settings">
                    <span class="icon">⚙️</span> 系統設定
                </a>
                <div class="nav-divider"></div>
                <a class="nav-item" onclick="logout()">
                    <span class="icon">🚪</span> 登出
                </a>
            </nav>
        </aside>
        
        <!-- Main Content -->
        <main class="main">
            <header class="header">
                <div class="header-left">
                    <button class="menu-toggle" onclick="toggleSidebar()">☰</button>
                    <h2 class="page-title" id="page-title">儀表板</h2>
                </div>
                <div class="header-right">
                    <div class="user-menu" id="user-menu">
                        <span id="user-name">使用者</span> ▾
                    </div>
                </div>
            </header>
            
            <div class="content">
                <!-- Dashboard Page -->
                <div class="page active" id="page-dashboard">
                    <div class="stats-grid" id="stats-grid">
                        <div class="stat-card">
                            <div class="label">總客戶數</div>
                            <div class="value" id="stat-customers">-</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">在庫車輛</div>
                            <div class="value" id="stat-vehicles">-</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">本月營收</div>
                            <div class="value" id="stat-revenue">-</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">待跟進</div>
                            <div class="value" id="stat-followups">-</div>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">近期交易</h3>
                            <button class="btn btn-sm btn-outline" onclick="navigate('deals')">查看全部</button>
                        </div>
                        <div class="card-body">
                            <div class="table-wrapper">
                                <table id="recent-deals-table">
                                    <thead>
                                        <tr>
                                            <th>日期</th>
                                            <th>類型</th>
                                            <th>車輛</th>
                                            <th>客戶</th>
                                            <th>金額</th>
                                        </tr>
                                    </thead>
                                    <tbody id="recent-deals"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Customers Page -->
                <div class="page" id="page-customers">
                    <div class="toolbar">
                        <div class="toolbar-left">
                            <div class="search-box">
                                <span class="icon">🔍</span>
                                <input type="text" class="form-input" placeholder="搜尋客戶..." id="customer-search">
                            </div>
                        </div>
                        <button class="btn btn-accent" onclick="showModal('customer-modal')">
                            + 新增客戶
                        </button>
                    </div>
                    
                    <div class="card">
                        <div class="card-body">
                            <div class="table-wrapper">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>姓名</th>
                                            <th>電話</th>
                                            <th>來源</th>
                                            <th>等級</th>
                                            <th>最後聯繫</th>
                                            <th>操作</th>
                                        </tr>
                                    </thead>
                                    <tbody id="customers-list"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Vehicles Page -->
                <div class="page" id="page-vehicles">
                    <div class="toolbar">
                        <div class="toolbar-left">
                            <div class="search-box">
                                <span class="icon">🔍</span>
                                <input type="text" class="form-input" placeholder="搜尋車輛..." id="vehicle-search">
                            </div>
                            <select class="form-select" id="vehicle-status-filter" style="width: auto;">
                                <option value="">全部狀態</option>
                                <option value="in_stock">在庫</option>
                                <option value="reserved">已預訂</option>
                                <option value="sold">已售出</option>
                            </select>
                        </div>
                        <button class="btn btn-accent" onclick="showModal('vehicle-modal')">
                            + 新增車輛
                        </button>
                    </div>
                    
                    <div class="card">
                        <div class="card-body">
                            <div class="table-wrapper">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>車牌</th>
                                            <th>品牌/型號</th>
                                            <th>年份</th>
                                            <th>成本</th>
                                            <th>售價</th>
                                            <th>狀態</th>
                                            <th>操作</th>
                                        </tr>
                                    </thead>
                                    <tbody id="vehicles-list"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Deals Page -->
                <div class="page" id="page-deals">
                    <div class="toolbar">
                        <div class="toolbar-left">
                            <select class="form-select" id="deal-type-filter" style="width: auto;">
                                <option value="">全部類型</option>
                                <option value="buy">收購</option>
                                <option value="sell">售出</option>
                            </select>
                        </div>
                        <button class="btn btn-accent" onclick="showModal('deal-modal')">
                            + 新增交易
                        </button>
                    </div>
                    
                    <div class="card">
                        <div class="card-body">
                            <div class="table-wrapper">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>日期</th>
                                            <th>類型</th>
                                            <th>車輛</th>
                                            <th>客戶</th>
                                            <th>金額</th>
                                            <th>利潤</th>
                                            <th>狀態</th>
                                        </tr>
                                    </thead>
                                    <tbody id="deals-list"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Other pages... -->
                <div class="page" id="page-followups">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">待跟進客戶</h3>
                        </div>
                        <div class="card-body">
                            <div id="followups-list"></div>
                        </div>
                    </div>
                </div>
                
                <div class="page" id="page-reports">
                    <div class="empty-state">
                        <div class="icon">📊</div>
                        <h3>報表功能</h3>
                        <p>專業版功能，請升級後使用</p>
                    </div>
                </div>
                
                <div class="page" id="page-settings">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">帳戶設定</h3>
                        </div>
                        <div class="card-body">
                            <p>設定功能開發中...</p>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>
    
    <!-- Customer Modal -->
    <div class="modal" id="customer-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title">新增客戶</h3>
                <button class="modal-close" onclick="hideModal('customer-modal')">&times;</button>
            </div>
            <div class="modal-body">
                <form id="customer-form">
                    <div class="form-group">
                        <label class="form-label">姓名 *</label>
                        <input type="text" class="form-input" name="name" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">電話 *</label>
                        <input type="tel" class="form-input" name="phone" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">來源</label>
                        <select class="form-select" name="source">
                            <option value="walk_in">現場來店</option>
                            <option value="phone">電話詢問</option>
                            <option value="line">LINE</option>
                            <option value="facebook">Facebook</option>
                            <option value="referral">朋友介紹</option>
                            <option value="other">其他</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">備註</label>
                        <textarea class="form-input" name="notes" rows="3"></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="hideModal('customer-modal')">取消</button>
                <button class="btn btn-primary" onclick="saveCustomer()">儲存</button>
            </div>
        </div>
    </div>
    
    <!-- Toast Container -->
    <div class="toast-container" id="toast-container"></div>
    
    <script>
        // Global State
        const state = {{
            user: null,
            token: null,
            currentPage: 'dashboard'
        }};
        
        // API Helper
        async function api(endpoint, options = {{}}) {{
            const token = localStorage.getItem('token');
            const headers = {{
                'Content-Type': 'application/json',
                ...(token && {{ 'Authorization': `Bearer ${{token}}` }})
            }};
            
            const resp = await fetch(endpoint, {{ ...options, headers }});
            return await resp.json();
        }}
        
        // Initialize
        async function init() {{
            state.token = localStorage.getItem('token');
            const userData = localStorage.getItem('user');
            
            if (!state.token || !userData) {{
                window.location.href = '/';
                return;
            }}
            
            state.user = JSON.parse(userData);
            
            // Update UI
            document.getElementById('user-name').textContent = state.user.user_name;
            document.getElementById('tenant-name').textContent = state.user.tenant_name;
            
            // Load initial data
            loadDashboard();
        }}
        
        // Navigation
        function navigate(page) {{
            state.currentPage = page;
            
            // Update nav
            document.querySelectorAll('.nav-item').forEach(item => {{
                item.classList.toggle('active', item.dataset.page === page);
            }});
            
            // Update page
            document.querySelectorAll('.page').forEach(p => {{
                p.classList.toggle('active', p.id === `page-${{page}}`);
            }});
            
            // Update title
            const titles = {{
                dashboard: '儀表板',
                customers: '客戶管理',
                vehicles: '車輛庫存',
                deals: '交易記錄',
                followups: '跟進提醒',
                reports: '報表分析',
                settings: '系統設定'
            }};
            document.getElementById('page-title').textContent = titles[page] || page;
            
            // Load page data
            switch(page) {{
                case 'dashboard': loadDashboard(); break;
                case 'customers': loadCustomers(); break;
                case 'vehicles': loadVehicles(); break;
                case 'deals': loadDeals(); break;
                case 'followups': loadFollowups(); break;
            }}
            
            // Close sidebar on mobile
            document.getElementById('sidebar').classList.remove('open');
        }}
        
        // Setup nav click handlers
        document.querySelectorAll('.nav-item[data-page]').forEach(item => {{
            item.addEventListener('click', () => navigate(item.dataset.page));
        }});
        
        // Dashboard
        async function loadDashboard() {{
            const result = await api('/api/stats');
            if (result.success) {{
                const stats = result.stats;
                document.getElementById('stat-customers').textContent = stats.customers || 0;
                document.getElementById('stat-vehicles').textContent = stats.vehicles?.in_stock || 0;
                
                const revenue = stats.deals?.sell?.amount || 0;
                document.getElementById('stat-revenue').textContent = `$${{revenue.toLocaleString()}}`;
                
                document.getElementById('stat-followups').textContent = stats.pending_followups || 0;
            }}
            
            // Load recent deals
            const deals = await api('/api/deals');
            if (deals.success) {{
                const tbody = document.getElementById('recent-deals');
                tbody.innerHTML = deals.deals.slice(0, 5).map(d => `
                    <tr>
                        <td>${{d.deal_date || '-'}}</td>
                        <td><span class="badge badge-${{d.deal_type === 'sell' ? 'success' : 'info'}}">${{d.deal_type === 'sell' ? '售出' : '收購'}}</span></td>
                        <td>${{d.brand || ''}} ${{d.model || ''}}</td>
                        <td>${{d.customer_name || '-'}}</td>
                        <td>$${{d.amount?.toLocaleString() || 0}}</td>
                    </tr>
                `).join('');
            }}
        }}
        
        // Customers
        async function loadCustomers() {{
            const result = await api('/api/customers');
            if (result.success) {{
                const tbody = document.getElementById('customers-list');
                if (result.customers.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:#999;">尚無客戶資料</td></tr>';
                    return;
                }}
                tbody.innerHTML = result.customers.map(c => `
                    <tr>
                        <td><strong>${{c.name}}</strong></td>
                        <td>${{c.phone || '-'}}</td>
                        <td>${{getSourceName(c.source)}}</td>
                        <td><span class="badge badge-${{getLevelBadge(c.level)}}">${{getLevelName(c.level)}}</span></td>
                        <td>${{c.last_contact || '-'}}</td>
                        <td>
                            <button class="btn btn-sm btn-outline" onclick="editCustomer(${{c.id}})">編輯</button>
                        </td>
                    </tr>
                `).join('');
            }}
        }}
        
        function getSourceName(source) {{
            const sources = {{ walk_in: '現場', phone: '電話', line: 'LINE', facebook: 'FB', referral: '介紹', other: '其他' }};
            return sources[source] || source;
        }}
        
        function getLevelName(level) {{
            const levels = {{ vip: 'VIP', normal: '一般', potential: '潛在', cold: '冷淡' }};
            return levels[level] || level;
        }}
        
        function getLevelBadge(level) {{
            const badges = {{ vip: 'warning', normal: 'default', potential: 'info', cold: 'default' }};
            return badges[level] || 'default';
        }}
        
        // Vehicles
        async function loadVehicles() {{
            const status = document.getElementById('vehicle-status-filter').value;
            const result = await api(`/api/vehicles?status=${{status}}`);
            if (result.success) {{
                const tbody = document.getElementById('vehicles-list');
                if (result.vehicles.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:#999;">尚無車輛資料</td></tr>';
                    return;
                }}
                tbody.innerHTML = result.vehicles.map(v => `
                    <tr>
                        <td>${{v.plate || '-'}}</td>
                        <td><strong>${{v.brand}}</strong> ${{v.model}}</td>
                        <td>${{v.year || '-'}}</td>
                        <td>$${{v.total_cost?.toLocaleString() || 0}}</td>
                        <td>$${{v.asking_price?.toLocaleString() || 0}}</td>
                        <td><span class="badge badge-${{getStatusBadge(v.status)}}">${{getStatusName(v.status)}}</span></td>
                        <td>
                            <button class="btn btn-sm btn-outline" onclick="editVehicle(${{v.id}})">編輯</button>
                        </td>
                    </tr>
                `).join('');
            }}
        }}
        
        function getStatusName(status) {{
            const names = {{ in_stock: '在庫', reserved: '已預訂', sold: '已售出', maintenance: '整備中' }};
            return names[status] || status;
        }}
        
        function getStatusBadge(status) {{
            const badges = {{ in_stock: 'success', reserved: 'warning', sold: 'default', maintenance: 'info' }};
            return badges[status] || 'default';
        }}
        
        // Deals
        async function loadDeals() {{
            const result = await api('/api/deals');
            if (result.success) {{
                const tbody = document.getElementById('deals-list');
                if (result.deals.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:#999;">尚無交易記錄</td></tr>';
                    return;
                }}
                tbody.innerHTML = result.deals.map(d => `
                    <tr>
                        <td>${{d.deal_date || '-'}}</td>
                        <td><span class="badge badge-${{d.deal_type === 'sell' ? 'success' : 'info'}}">${{d.deal_type === 'sell' ? '售出' : '收購'}}</span></td>
                        <td>${{d.brand || ''}} ${{d.model || ''}}</td>
                        <td>${{d.customer_name || '-'}}</td>
                        <td>$${{d.amount?.toLocaleString() || 0}}</td>
                        <td style="color: ${{d.profit >= 0 ? 'var(--success)' : 'var(--error)'}}">$${{d.profit?.toLocaleString() || 0}}</td>
                        <td><span class="badge badge-success">完成</span></td>
                    </tr>
                `).join('');
            }}
        }}
        
        // Followups
        async function loadFollowups() {{
            const result = await api('/api/followups');
            if (result.success) {{
                const container = document.getElementById('followups-list');
                if (result.followups.length === 0) {{
                    container.innerHTML = '<div class="empty-state"><div class="icon">✅</div><h3>太棒了！</h3><p>目前沒有待跟進的客戶</p></div>';
                    return;
                }}
                container.innerHTML = result.followups.map(f => `
                    <div style="padding: 16px; border-bottom: 1px solid var(--border);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>${{f.customer_name}}</strong>
                                <span style="color: var(--text-secondary); margin-left: 8px;">${{f.next_date || '未設定'}}</span>
                            </div>
                            <button class="btn btn-sm btn-primary">跟進</button>
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 4px;">${{f.next_action || '無'}}</div>
                    </div>
                `).join('');
            }}
        }}
        
        // Modal
        function showModal(id) {{
            document.getElementById(id).classList.add('active');
        }}
        
        function hideModal(id) {{
            document.getElementById(id).classList.remove('active');
        }}
        
        // Save Customer
        async function saveCustomer() {{
            const form = document.getElementById('customer-form');
            const data = Object.fromEntries(new FormData(form));
            
            const result = await api('/api/customers', {{
                method: 'POST',
                body: JSON.stringify(data)
            }});
            
            if (result.success) {{
                showToast('客戶新增成功', 'success');
                hideModal('customer-modal');
                form.reset();
                loadCustomers();
            }} else {{
                showToast(result.error || '新增失敗', 'error');
            }}
        }}
        
        // Toast
        function showToast(message, type = 'info') {{
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${{type}}`;
            toast.textContent = message;
            container.appendChild(toast);
            
            setTimeout(() => toast.remove(), 3000);
        }}
        
        // Sidebar Toggle
        function toggleSidebar() {{
            document.getElementById('sidebar').classList.toggle('open');
        }}
        
        // Logout
        function logout() {{
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/';
        }}
        
        // Filter change handlers
        document.getElementById('vehicle-status-filter')?.addEventListener('change', loadVehicles);
        
        // Search handlers
        let searchTimeout;
        document.getElementById('customer-search')?.addEventListener('input', (e) => {{
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => loadCustomers(), 300);
        }});
        
        // Initialize
        init();
    </script>
</body>
</html>'''
