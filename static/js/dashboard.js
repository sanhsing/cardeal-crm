/**
 * 車行寶 CRM v5.2 - 數據分析儀表板
 * 北斗七星文創數位 × 織明
 */

// 圖表配置
const chartColors = {
    primary: '#3b82f6',
    secondary: '#8b5cf6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    gradient: ['#667eea', '#764ba2']
};

// 格式化金額
function formatMoney(amount) {
    if (amount >= 10000) {
        return (amount / 10000).toFixed(1) + ' 萬';
    }
    return amount.toLocaleString();
}

// ============================================================
// KPI 卡片組件
// ============================================================

async function loadKPICards() {
    try {
        const response = await fetch('/api/analytics/kpi');
        const data = await response.json();
        
        if (!data.success) {
            console.error('KPI 載入失敗:', data.error);
            return;
        }
        
        const kpi = data.data;
        
        // 更新 KPI 卡片
        updateKPICard('monthly-sales', {
            value: formatMoney(kpi.monthly_sales.amount),
            label: '本月銷售額',
            icon: '💰',
            subtext: `${kpi.monthly_sales.count} 筆成交`
        });
        
        updateKPICard('active-customers', {
            value: kpi.active_customers,
            label: '活躍客戶',
            icon: '👥',
            subtext: '待跟進客戶'
        });
        
        updateKPICard('inventory', {
            value: kpi.inventory.count,
            label: '在庫車輛',
            icon: '🚗',
            subtext: `價值 ${formatMoney(kpi.inventory.value)}`
        });
        
        updateKPICard('pending-followups', {
            value: kpi.pending_followups,
            label: '待跟進',
            icon: '📞',
            subtext: '今日需處理'
        });
        
    } catch (error) {
        console.error('KPI 載入錯誤:', error);
    }
}

function updateKPICard(id, data) {
    const card = document.getElementById(id);
    if (!card) return;
    
    card.innerHTML = `
        <div class="stat-icon gradient-primary">${data.icon}</div>
        <div class="stat-value">${data.value}</div>
        <div class="stat-label">${data.label}</div>
        <div class="stat-change">${data.subtext}</div>
    `;
}

// ============================================================
// 銷售趨勢圖表
// ============================================================

let salesChart = null;

async function loadSalesTrend(days = 30) {
    try {
        const response = await fetch(`/api/analytics/sales?days=${days}`);
        const data = await response.json();
        
        if (!data.success) return;
        
        const trend = data.data.trend;
        
        const ctx = document.getElementById('sales-chart');
        if (!ctx) return;
        
        // 準備數據
        const labels = trend.daily.map(d => d.date.substring(5));
        const amounts = trend.daily.map(d => d.amount / 10000);
        const counts = trend.daily.map(d => d.count);
        
        // 銷毀舊圖表
        if (salesChart) {
            salesChart.destroy();
        }
        
        // 創建新圖表
        salesChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '銷售額 (萬)',
                    data: amounts,
                    borderColor: chartColors.primary,
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: '成交數',
                    data: counts,
                    borderColor: chartColors.success,
                    backgroundColor: 'transparent',
                    yAxisID: 'y1',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: '銷售額 (萬)' }
                    },
                    y1: {
                        position: 'right',
                        beginAtZero: true,
                        title: { display: true, text: '成交數' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
        
        // 更新摘要
        const summary = trend.summary;
        document.getElementById('sales-summary').innerHTML = `
            <span class="badge badge-primary">總銷售: ${formatMoney(summary.total_amount)}</span>
            <span class="badge ${summary.growth_rate >= 0 ? 'badge-success' : 'badge-error'}">
                ${summary.growth_rate >= 0 ? '↑' : '↓'} ${Math.abs(summary.growth_rate)}%
            </span>
        `;
        
    } catch (error) {
        console.error('銷售趨勢載入錯誤:', error);
    }
}

// ============================================================
// 客戶漏斗圖
// ============================================================

let funnelChart = null;

async function loadCustomerFunnel() {
    try {
        const response = await fetch('/api/analytics/funnel');
        const data = await response.json();
        
        if (!data.success) return;
        
        const funnel = data.data.funnel.funnel;
        
        const ctx = document.getElementById('funnel-chart');
        if (!ctx) return;
        
        // 準備數據
        const labels = funnel.map(f => f.label);
        const values = funnel.map(f => f.count);
        const colors = [
            chartColors.primary,
            chartColors.info,
            chartColors.success,
            chartColors.warning,
            chartColors.secondary,
            chartColors.danger
        ];
        
        if (funnelChart) {
            funnelChart.destroy();
        }
        
        funnelChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '客戶數',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 8
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { beginAtZero: true }
                }
            }
        });
        
        // 更新轉化率
        document.getElementById('funnel-rate').textContent = 
            `整體轉化率: ${data.data.funnel.overall_rate}%`;
        
    } catch (error) {
        console.error('漏斗圖載入錯誤:', error);
    }
}

// ============================================================
// 品牌分佈圖
// ============================================================

let brandChart = null;

async function loadBrandDistribution() {
    try {
        const response = await fetch('/api/analytics/sales?days=30');
        const data = await response.json();
        
        if (!data.success) return;
        
        const brands = data.data.by_brand;
        
        const ctx = document.getElementById('brand-chart');
        if (!ctx) return;
        
        const labels = brands.slice(0, 8).map(b => b.brand);
        const values = brands.slice(0, 8).map(b => b.count);
        
        if (brandChart) {
            brandChart.destroy();
        }
        
        brandChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b',
                        '#ef4444', '#06b6d4', '#ec4899', '#6366f1'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('品牌分佈載入錯誤:', error);
    }
}

// ============================================================
// 業績排行榜
// ============================================================

async function loadRanking() {
    try {
        const response = await fetch('/api/analytics/ranking?days=30');
        const data = await response.json();
        
        if (!data.success) return;
        
        const ranking = data.data.sales_ranking;
        const container = document.getElementById('ranking-list');
        if (!container) return;
        
        container.innerHTML = ranking.map((item, index) => `
            <div class="ranking-item animate-slide-in" style="animation-delay: ${index * 0.1}s">
                <span class="ranking-position">${index + 1}</span>
                <span class="ranking-name">${item.name}</span>
                <span class="ranking-value">${formatMoney(item.total_amount)}</span>
                <span class="ranking-count">${item.deal_count} 筆</span>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('排行榜載入錯誤:', error);
    }
}

// ============================================================
// 初始化儀表板
// ============================================================

async function initDashboard() {
    // 顯示載入狀態
    document.querySelectorAll('.chart-container').forEach(el => {
        el.innerHTML = '<div class="loading-overlay"><div class="spinner"></div></div>';
    });
    
    // 並行載入所有數據
    await Promise.all([
        loadKPICards(),
        loadSalesTrend(30),
        loadCustomerFunnel(),
        loadBrandDistribution(),
        loadRanking()
    ]);
    
    console.log('儀表板載入完成');
}

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', initDashboard);

// 自動刷新（每 5 分鐘）
setInterval(() => {
    loadKPICards();
}, 5 * 60 * 1000);
