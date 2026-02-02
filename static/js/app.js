/**
 * 車行寶 CRM v5.1 - 主應用 JavaScript
 * 北斗七星文創數位 × 織明
 */

// ===== 應用狀態 =====
const App = {
    currentPage: 'dashboard',
    user: null,
    isLoading: false,
    data: {
        customers: [],
        vehicles: [],
        deals: [],
        stats: {}
    }
};

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    // 檢查登入狀態
    if (!AuthAPI.isLoggedIn()) {
        window.location.href = '/';
        return;
    }
    
    App.user = AuthAPI.getUser();
    
    // 初始化 UI
    initNavigation();
    initModals();
    updateUserInfo();
    
    // 載入首頁
    navigateTo('dashboard');
    
    // 啟動定時刷新
    setInterval(refreshCurrentPage, 60000);  // 每分鐘刷新
});

// ===== 導航 =====
function initNavigation() {
    // 側邊欄導航點擊
    $$('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            if (page) navigateTo(page);
        });
    });
    
    // 手機版選單切換
    const menuToggle = $('#menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            $('#sidebar').classList.toggle('open');
        });
    }
    
    // 點擊外部關閉側邊欄
    document.addEventListener('click', (e) => {
        const sidebar = $('#sidebar');
        const toggle = $('#menu-toggle');
        if (sidebar && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });
}

function navigateTo(page) {
    // 更新狀態
    App.currentPage = page;
    
    // 更新導航高亮
    $$('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });
    
    // 隱藏所有頁面
    $$('.page').forEach(p => p.classList.remove('active'));
    
    // 顯示目標頁面
    const targetPage = $(`#page-${page}`);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    // 更新標題
    const titles = {
        dashboard: '儀表板',
        customers: '客戶管理',
        vehicles: '車輛庫存',
        deals: '交易記錄',
        followups: '跟進提醒',
        reports: '報表分析',
        settings: '系統設定'
    };
    const titleEl = $('#page-title');
    if (titleEl) titleEl.textContent = titles[page] || page;
    
    // 載入資料
    loadPageData(page);
    
    // 關閉手機版側邊欄
    $('#sidebar')?.classList.remove('open');
}

async function loadPageData(page) {
    showLoading(true);
    
    try {
        switch (page) {
            case 'dashboard':
                await loadDashboard();
                break;
            case 'customers':
                await loadCustomers();
                break;
            case 'vehicles':
                await loadVehicles();
                break;
            case 'deals':
                await loadDeals();
                break;
            case 'followups':
                await loadFollowups();
                break;
        }
    } catch (error) {
        console.error('載入資料失敗:', error);
        showToast('載入資料失敗', 'error');
    }
    
    showLoading(false);
}

function refreshCurrentPage() {
    loadPageData(App.currentPage);
}

// ===== 儀表板 =====
async function loadDashboard() {
    const result = await ReportAPI.stats();
    if (!result.success) return;
    
    App.data.stats = result.stats;
    renderDashboard(result.stats);
}

function renderDashboard(stats) {
    // 統計卡片
    setTextContent('#stat-customers', stats.customer_count || 0);
    setTextContent('#stat-vehicles', stats.vehicle_in_stock || 0);
    setTextContent('#stat-revenue', formatMoney(stats.revenue_this_month || 0));
    setTextContent('#stat-followups', stats.pending_followups || 0);
    
    // 本月交易
    const deals = stats.deals_this_month || {};
    const buyCount = deals.buy?.count || 0;
    const sellCount = deals.sell?.count || 0;
    setTextContent('#stat-buy-count', buyCount);
    setTextContent('#stat-sell-count', sellCount);
}

// ===== 客戶管理 =====
async function loadCustomers(params = {}) {
    const search = $('#customer-search')?.value || '';
    const result = await CustomerAPI.list({ ...params, search });
    
    if (!result.success) return;
    
    App.data.customers = result.customers;
    renderCustomerList(result.customers);
}

function renderCustomerList(customers) {
    const tbody = $('#customer-table tbody');
    if (!tbody) return;
    
    if (customers.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="6" class="text-center py-8 text-secondary">
                暫無客戶資料
            </td></tr>`;
        return;
    }
    
    tbody.innerHTML = customers.map(c => `
        <tr data-id="${c.id}">
            <td>
                <div class="font-medium">${sanitize(c.name)}</div>
                <div class="text-sm text-secondary">${sanitize(c.phone || '-')}</div>
            </td>
            <td><span class="badge badge-${getLevelBadge(c.level)}">${getLevelName(c.level)}</span></td>
            <td>${getSourceName(c.source)}</td>
            <td>${c.total_deals || 0} 筆</td>
            <td>${formatDate(c.last_contact, 'relative')}</td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="viewCustomer(${c.id})">查看</button>
            </td>
        </tr>
    `).join('');
}

async function createCustomer() {
    const data = getFormData('customer-form');
    
    if (!data.name) {
        showToast('請填寫客戶姓名', 'warning');
        return;
    }
    
    const result = await CustomerAPI.create(data);
    
    if (result.success) {
        showToast('客戶建立成功', 'success');
        hideModal('customer-modal');
        resetForm('customer-form');
        loadCustomers();
    } else {
        showToast(result.error || '建立失敗', 'error');
    }
}

function viewCustomer(id) {
    // TODO: 顯示客戶詳情 Modal
    console.log('View customer:', id);
}

// ===== 車輛管理 =====
async function loadVehicles(params = {}) {
    const search = $('#vehicle-search')?.value || '';
    const status = $('#vehicle-status-filter')?.value || '';
    
    const result = await VehicleAPI.list({ ...params, search, status });
    
    if (!result.success) return;
    
    App.data.vehicles = result.vehicles;
    renderVehicleList(result.vehicles);
}

function renderVehicleList(vehicles) {
    const tbody = $('#vehicle-table tbody');
    if (!tbody) return;
    
    if (vehicles.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="7" class="text-center py-8 text-secondary">
                暫無車輛資料
            </td></tr>`;
        return;
    }
    
    tbody.innerHTML = vehicles.map(v => `
        <tr data-id="${v.id}">
            <td>
                <div class="font-medium">${sanitize(v.brand)} ${sanitize(v.model)}</div>
                <div class="text-sm text-secondary">${sanitize(v.plate || '-')}</div>
            </td>
            <td>${v.year || '-'}</td>
            <td>${v.mileage ? v.mileage.toLocaleString() + ' km' : '-'}</td>
            <td>${formatMoney(v.total_cost)}</td>
            <td>${formatMoney(v.asking_price)}</td>
            <td><span class="badge badge-${getStatusBadge(v.status)}">${getStatusName(v.status)}</span></td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="viewVehicle(${v.id})">查看</button>
            </td>
        </tr>
    `).join('');
}

async function createVehicle() {
    const data = getFormData('vehicle-form');
    
    if (!data.brand || !data.model) {
        showToast('請填寫品牌和型號', 'warning');
        return;
    }
    
    // 計算總成本
    const purchasePrice = parseInt(data.purchase_price) || 0;
    const repairCost = parseInt(data.repair_cost) || 0;
    data.total_cost = purchasePrice + repairCost;
    
    const result = await VehicleAPI.create(data);
    
    if (result.success) {
        showToast('車輛建立成功', 'success');
        hideModal('vehicle-modal');
        resetForm('vehicle-form');
        loadVehicles();
    } else {
        showToast(result.error || '建立失敗', 'error');
    }
}

function viewVehicle(id) {
    // TODO: 顯示車輛詳情 Modal
    console.log('View vehicle:', id);
}

// ===== 交易記錄 =====
async function loadDeals(params = {}) {
    const dealType = $('#deal-type-filter')?.value || '';
    const result = await DealAPI.list({ ...params, deal_type: dealType });
    
    if (!result.success) return;
    
    App.data.deals = result.deals;
    renderDealList(result.deals);
}

function renderDealList(deals) {
    const tbody = $('#deal-table tbody');
    if (!tbody) return;
    
    if (deals.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="6" class="text-center py-8 text-secondary">
                暫無交易記錄
            </td></tr>`;
        return;
    }
    
    tbody.innerHTML = deals.map(d => `
        <tr data-id="${d.id}">
            <td>${formatDate(d.deal_date)}</td>
            <td><span class="badge badge-${getDealTypeBadge(d.deal_type)}">${getDealTypeName(d.deal_type)}</span></td>
            <td>${sanitize(d.customer_name || '-')}</td>
            <td>${sanitize(d.brand || '')} ${sanitize(d.model || '')}</td>
            <td>${formatMoney(d.amount)}</td>
            <td class="${d.profit >= 0 ? 'text-success' : 'text-error'}">${formatMoney(d.profit)}</td>
        </tr>
    `).join('');
}

// ===== 跟進提醒 =====
async function loadFollowups() {
    const result = await FollowupAPI.list({ pending: true });
    
    if (!result.success) return;
    
    renderFollowupList(result.followups);
}

function renderFollowupList(followups) {
    const container = $('#followup-list');
    if (!container) return;
    
    if (followups.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="icon">✅</div>
                <h3>太棒了！</h3>
                <p>目前沒有待跟進的客戶</p>
            </div>`;
        return;
    }
    
    container.innerHTML = followups.map(f => `
        <div class="card mb-4">
            <div class="card-body">
                <div class="flex justify-between items-center">
                    <div>
                        <div class="font-medium">${sanitize(f.customer_name)}</div>
                        <div class="text-sm text-secondary">${sanitize(f.phone || '-')}</div>
                    </div>
                    <div class="text-right">
                        <div class="text-sm">${formatDate(f.next_followup)}</div>
                        <button class="btn btn-sm btn-accent mt-2" onclick="doFollowup(${f.customer_id})">
                            跟進
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// ===== Modal 處理 =====
function initModals() {
    // 關閉 Modal
    $$('.modal-close, .modal-overlay').forEach(el => {
        el.addEventListener('click', (e) => {
            if (e.target === el) {
                el.closest('.modal-overlay')?.classList.remove('active');
            }
        });
    });
    
    // ESC 關閉 Modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            $$('.modal-overlay.active').forEach(m => m.classList.remove('active'));
        }
    });
}

function openModal(id) {
    const modal = $(`#${id}`);
    if (modal) {
        modal.classList.add('active');
        // 聚焦第一個輸入框
        modal.querySelector('input')?.focus();
    }
}

// ===== UI 工具 =====
function updateUserInfo() {
    if (App.user) {
        setTextContent('#user-name', App.user.user_name || '使用者');
        setTextContent('#tenant-name', App.user.tenant_name || '');
    }
}

function showLoading(show) {
    App.isLoading = show;
    const loader = $('#page-loader');
    if (loader) {
        loader.style.display = show ? 'flex' : 'none';
    }
}

function setTextContent(selector, text) {
    const el = $(selector);
    if (el) el.textContent = text;
}

function sanitize(str) {
    if (!str) return '';
    return str.replace(/[<>&"']/g, c => ({
        '<': '&lt;', '>': '&gt;', '&': '&amp;',
        '"': '&quot;', "'": '&#39;'
    }[c]));
}

// ===== 搜尋防抖 =====
const debouncedCustomerSearch = debounce(() => loadCustomers(), 300);
const debouncedVehicleSearch = debounce(() => loadVehicles(), 300);

// ===== 登出 =====
function logout() {
    if (confirm('確定要登出嗎？')) {
        AuthAPI.logout();
    }
}


/* 📚 知識點
 * -----------
 * 1. DOMContentLoaded 事件：
 *    - DOM 解析完成後觸發
 *    - 不等待圖片等資源載入
 *    - 適合初始化 JavaScript
 *
 * 2. 事件委派（Event Delegation）：
 *    - 在父元素監聽事件
 *    - 用 e.target 判斷實際觸發元素
 *    - 適合動態新增的元素
 *
 * 3. 狀態管理：
 *    - App 物件集中管理狀態
 *    - currentPage 追蹤當前頁面
 *    - data 存儲載入的資料
 *
 * 4. 模板字串（Template Literals）：
 *    - `${variable}` 插入變數
 *    - 可跨行，方便撰寫 HTML
 *    - .map().join('') 產生列表 HTML
 *
 * 5. 可選鏈 + 空值合併：
 *    - element?.value || '' 安全取值
 *    - 避免 null/undefined 錯誤
 *
 * 6. setInterval 定時器：
 *    - 每隔指定毫秒執行
 *    - 60000ms = 1分鐘
 *    - 用於自動刷新資料
 */
