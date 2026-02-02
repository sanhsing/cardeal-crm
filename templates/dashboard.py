"""
車行寶 CRM v5.2 - 數據分析儀表板
北斗七星文創數位 × 織明
"""
from typing import Dict, Any

def get_dashboard_html() -> str:
    """生成數據分析儀表板"""
    return '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>車行寶 CRM - 數據分析</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Noto Sans TC', sans-serif; }
        .card { transition: all 0.3s ease; }
        .card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.1); }
        .gradient-purple { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .gradient-blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
        .gradient-green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
        .gradient-orange { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <!-- 導航欄 -->
    <nav class="bg-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 py-3">
            <div class="flex justify-between items-center">
                <div class="flex items-center gap-3">
                    <span class="text-2xl">🚗</span>
                    <span class="text-xl font-bold text-gray-800">車行寶 CRM</span>
                    <span class="text-sm text-gray-500">數據分析</span>
                </div>
                <div class="flex items-center gap-4">
                    <a href="/app" class="text-gray-600 hover:text-purple-600">返回首頁</a>
                    <button id="refreshBtn" class="bg-purple-100 text-purple-700 px-4 py-2 rounded-lg hover:bg-purple-200">
                        🔄 刷新數據
                    </button>
                </div>
            </div>
        </div>
    </nav>
    
    <!-- 主內容 -->
    <main class="max-w-7xl mx-auto px-4 py-6">
        <!-- KPI 卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="card gradient-purple rounded-xl p-6 text-white">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="text-white/80 text-sm">本月營收</p>
                        <p class="text-3xl font-bold mt-2" id="monthlyRevenue">$0</p>
                        <p class="text-sm mt-2 text-white/80">
                            <span id="revenueChange" class="text-green-200">↑ 0%</span> vs 上月
                        </p>
                    </div>
                    <div class="text-4xl opacity-80">💰</div>
                </div>
            </div>
            
            <div class="card gradient-blue rounded-xl p-6 text-white">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="text-white/80 text-sm">成交數量</p>
                        <p class="text-3xl font-bold mt-2" id="dealsCount">0</p>
                        <p class="text-sm mt-2 text-white/80">
                            <span id="dealsChange" class="text-green-200">↑ 0%</span> vs 上月
                        </p>
                    </div>
                    <div class="text-4xl opacity-80">🤝</div>
                </div>
            </div>
            
            <div class="card gradient-green rounded-xl p-6 text-white">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="text-white/80 text-sm">在庫車輛</p>
                        <p class="text-3xl font-bold mt-2" id="inventoryCount">0</p>
                        <p class="text-sm mt-2 text-white/80">
                            平均庫存天數：<span id="avgDays">0</span>
                        </p>
                    </div>
                    <div class="text-4xl opacity-80">🚙</div>
                </div>
            </div>
            
            <div class="card gradient-orange rounded-xl p-6 text-white">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="text-white/80 text-sm">潛在客戶</p>
                        <p class="text-3xl font-bold mt-2" id="leadsCount">0</p>
                        <p class="text-sm mt-2 text-white/80">
                            轉換率：<span id="conversionRate">0%</span>
                        </p>
                    </div>
                    <div class="text-4xl opacity-80">👥</div>
                </div>
            </div>
        </div>
        
        <!-- 圖表區域 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <!-- 銷售趨勢圖 -->
            <div class="card bg-white rounded-xl p-6 shadow-md">
                <h3 class="text-lg font-bold text-gray-800 mb-4">📈 銷售趨勢</h3>
                <canvas id="salesChart" height="250"></canvas>
            </div>
            
            <!-- 品牌分布圖 -->
            <div class="card bg-white rounded-xl p-6 shadow-md">
                <h3 class="text-lg font-bold text-gray-800 mb-4">🚗 品牌分布</h3>
                <canvas id="brandChart" height="250"></canvas>
            </div>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <!-- 客戶漏斗 -->
            <div class="card bg-white rounded-xl p-6 shadow-md">
                <h3 class="text-lg font-bold text-gray-800 mb-4">🎯 客戶漏斗</h3>
                <canvas id="funnelChart" height="250"></canvas>
            </div>
            
            <!-- 業績排行 -->
            <div class="card bg-white rounded-xl p-6 shadow-md">
                <h3 class="text-lg font-bold text-gray-800 mb-4">🏆 業績排行</h3>
                <div id="leaderboard" class="space-y-3">
                    <!-- 動態填充 -->
                </div>
            </div>
        </div>
        
        <!-- 近期活動 -->
        <div class="card bg-white rounded-xl p-6 shadow-md">
            <h3 class="text-lg font-bold text-gray-800 mb-4">📋 近期活動</h3>
            <div id="recentActivity" class="space-y-2">
                <!-- 動態填充 -->
            </div>
        </div>
    </main>
    
    <script>
        // 格式化金額
        const formatCurrency = (num) => {
            return '$' + (num || 0).toLocaleString();
        };
        
        // 模擬數據（實際使用時從 API 獲取）
        const mockData = {
            monthlyRevenue: 2850000,
            revenueChange: 12.5,
            dealsCount: 18,
            dealsChange: 8.3,
            inventoryCount: 45,
            avgDays: 32,
            leadsCount: 156,
            conversionRate: 11.5,
            salesData: [1200000, 980000, 1450000, 1680000, 2100000, 2850000],
            salesLabels: ['1月', '2月', '3月', '4月', '5月', '6月'],
            brandData: [35, 28, 18, 12, 7],
            brandLabels: ['Toyota', 'Honda', 'BMW', 'Benz', '其他'],
            funnelData: [156, 89, 45, 28, 18],
            funnelLabels: ['潛在客戶', '已聯繫', '有興趣', '議價中', '成交'],
            leaderboard: [
                { name: '王小明', deals: 8, revenue: 1250000 },
                { name: '李大華', deals: 5, revenue: 890000 },
                { name: '陳美美', deals: 3, revenue: 450000 },
                { name: '張小龍', deals: 2, revenue: 260000 }
            ],
            activities: [
                { time: '10:30', action: '新成交', detail: 'Toyota Camry - 王小姐' },
                { time: '09:45', action: '新客戶', detail: '李先生 0912-xxx-xxx' },
                { time: '09:15', action: '跟進提醒', detail: '陳小姐 - 預計回訪' },
                { time: '08:30', action: '新車入庫', detail: 'Honda CR-V 2023' }
            ]
        };
        
        // 更新 KPI
        document.getElementById('monthlyRevenue').textContent = formatCurrency(mockData.monthlyRevenue);
        document.getElementById('revenueChange').textContent = `↑ ${mockData.revenueChange}%`;
        document.getElementById('dealsCount').textContent = mockData.dealsCount;
        document.getElementById('dealsChange').textContent = `↑ ${mockData.dealsChange}%`;
        document.getElementById('inventoryCount').textContent = mockData.inventoryCount;
        document.getElementById('avgDays').textContent = mockData.avgDays;
        document.getElementById('leadsCount').textContent = mockData.leadsCount;
        document.getElementById('conversionRate').textContent = `${mockData.conversionRate}%`;
        
        // 銷售趨勢圖
        new Chart(document.getElementById('salesChart'), {
            type: 'line',
            data: {
                labels: mockData.salesLabels,
                datasets: [{
                    label: '月營收',
                    data: mockData.salesData,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { 
                        beginAtZero: true,
                        ticks: { callback: (v) => '$' + (v/10000) + '萬' }
                    }
                }
            }
        });
        
        // 品牌分布圖
        new Chart(document.getElementById('brandChart'), {
            type: 'doughnut',
            data: {
                labels: mockData.brandLabels,
                datasets: [{
                    data: mockData.brandData,
                    backgroundColor: ['#667eea', '#4facfe', '#11998e', '#f093fb', '#ccc']
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'right' } }
            }
        });
        
        // 客戶漏斗圖
        new Chart(document.getElementById('funnelChart'), {
            type: 'bar',
            data: {
                labels: mockData.funnelLabels,
                datasets: [{
                    data: mockData.funnelData,
                    backgroundColor: ['#667eea', '#4facfe', '#11998e', '#f5576c', '#38ef7d']
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: { legend: { display: false } }
            }
        });
        
        // 業績排行
        const leaderboardHtml = mockData.leaderboard.map((p, i) => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-3">
                    <span class="text-2xl">${['🥇', '🥈', '🥉', '4️⃣'][i]}</span>
                    <div>
                        <p class="font-medium">${p.name}</p>
                        <p class="text-sm text-gray-500">${p.deals} 筆成交</p>
                    </div>
                </div>
                <span class="font-bold text-purple-600">${formatCurrency(p.revenue)}</span>
            </div>
        `).join('');
        document.getElementById('leaderboard').innerHTML = leaderboardHtml;
        
        // 近期活動
        const activityHtml = mockData.activities.map(a => `
            <div class="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-lg">
                <span class="text-sm text-gray-500 w-16">${a.time}</span>
                <span class="px-2 py-1 bg-purple-100 text-purple-700 rounded text-sm">${a.action}</span>
                <span class="text-gray-700">${a.detail}</span>
            </div>
        `).join('');
        document.getElementById('recentActivity').innerHTML = activityHtml;
        
        // 刷新按鈕
        document.getElementById('refreshBtn').addEventListener('click', () => {
            location.reload();
        });
    </script>
</body>
</html>'''


def get_dashboard_api_handler():
    """儀表板 API 處理"""
    return {
        'monthly_revenue': 2850000,
        'revenue_change': 12.5,
        'deals_count': 18,
        'deals_change': 8.3,
        'inventory_count': 45,
        'avg_days': 32,
        'leads_count': 156,
        'conversion_rate': 11.5
    }
