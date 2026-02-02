/**
 * 車行寶 CRM v5.1 - 圖表組件庫
 * 北斗七星文創數位 × 織明
 * 
 * 基於 Canvas 的輕量級圖表
 */

// ===== 圖表基礎類 =====

class Chart {
    constructor(canvas, options = {}) {
        this.canvas = typeof canvas === 'string' ? document.getElementById(canvas) : canvas;
        this.ctx = this.canvas.getContext('2d');
        this.options = {
            padding: 40,
            colors: ['#1e3a5f', '#3d5a80', '#ee6c4d', '#10b981', '#f59e0b', '#3b82f6'],
            fontFamily: 'system-ui, sans-serif',
            fontSize: 12,
            animate: true,
            ...options
        };
        this.data = null;
        
        // 設定 Canvas 大小
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        
        this.canvas.width = rect.width * dpr;
        this.canvas.height = (this.options.height || 300) * dpr;
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = (this.options.height || 300) + 'px';
        
        this.ctx.scale(dpr, dpr);
        this.width = rect.width;
        this.height = this.options.height || 300;
        
        if (this.data) {
            this.render(this.data);
        }
    }

    clear() {
        this.ctx.clearRect(0, 0, this.width, this.height);
    }

    getColor(index) {
        return this.options.colors[index % this.options.colors.length];
    }
}


// ===== 折線圖 =====

class LineChart extends Chart {
    render(data) {
        this.data = data;
        this.clear();
        
        const { labels, datasets } = data;
        const { padding } = this.options;
        
        const chartWidth = this.width - padding * 2;
        const chartHeight = this.height - padding * 2;
        
        // 計算數據範圍
        let maxValue = 0;
        Object.values(datasets).forEach(values => {
            maxValue = Math.max(maxValue, ...values);
        });
        maxValue = maxValue || 1;  // 避免除以 0
        
        // 繪製網格
        this.drawGrid(chartWidth, chartHeight, padding, maxValue);
        
        // 繪製 X 軸標籤
        this.drawXLabels(labels, chartWidth, padding);
        
        // 繪製數據線
        let colorIndex = 0;
        for (const [name, values] of Object.entries(datasets)) {
            this.drawLine(values, labels.length, chartWidth, chartHeight, padding, maxValue, colorIndex);
            colorIndex++;
        }
        
        // 繪製圖例
        this.drawLegend(Object.keys(datasets), padding);
    }

    drawGrid(chartWidth, chartHeight, padding, maxValue) {
        const ctx = this.ctx;
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        
        // 水平線和 Y 軸標籤
        const gridLines = 5;
        for (let i = 0; i <= gridLines; i++) {
            const y = padding + (chartHeight / gridLines) * i;
            
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(this.width - padding, y);
            ctx.stroke();
            
            // Y 軸標籤
            const value = Math.round(maxValue * (1 - i / gridLines));
            ctx.fillStyle = '#64748b';
            ctx.font = `${this.options.fontSize}px ${this.options.fontFamily}`;
            ctx.textAlign = 'right';
            ctx.fillText(this.formatNumber(value), padding - 8, y + 4);
        }
    }

    drawXLabels(labels, chartWidth, padding) {
        const ctx = this.ctx;
        const step = chartWidth / (labels.length - 1 || 1);
        
        ctx.fillStyle = '#64748b';
        ctx.font = `${this.options.fontSize}px ${this.options.fontFamily}`;
        ctx.textAlign = 'center';
        
        // 如果標籤太多，只顯示部分
        const showEvery = Math.ceil(labels.length / 10);
        
        labels.forEach((label, i) => {
            if (i % showEvery === 0 || i === labels.length - 1) {
                const x = padding + step * i;
                ctx.fillText(label, x, this.height - padding + 20);
            }
        });
    }

    drawLine(values, count, chartWidth, chartHeight, padding, maxValue, colorIndex) {
        const ctx = this.ctx;
        const step = chartWidth / (count - 1 || 1);
        const color = this.getColor(colorIndex);
        
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        
        ctx.beginPath();
        values.forEach((value, i) => {
            const x = padding + step * i;
            const y = padding + chartHeight - (value / maxValue) * chartHeight;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();
        
        // 繪製數據點
        values.forEach((value, i) => {
            const x = padding + step * i;
            const y = padding + chartHeight - (value / maxValue) * chartHeight;
            
            ctx.fillStyle = 'white';
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = color;
            ctx.stroke();
        });
    }

    drawLegend(names, padding) {
        const ctx = this.ctx;
        let x = padding;
        
        names.forEach((name, i) => {
            const color = this.getColor(i);
            
            // 色塊
            ctx.fillStyle = color;
            ctx.fillRect(x, 8, 16, 12);
            
            // 文字
            ctx.fillStyle = '#333';
            ctx.font = `${this.options.fontSize}px ${this.options.fontFamily}`;
            ctx.textAlign = 'left';
            ctx.fillText(name, x + 22, 18);
            
            x += ctx.measureText(name).width + 40;
        });
    }

    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }
}


// ===== 長條圖 =====

class BarChart extends Chart {
    render(data) {
        this.data = data;
        this.clear();
        
        const { labels, datasets } = data;
        const { padding } = this.options;
        
        const chartWidth = this.width - padding * 2;
        const chartHeight = this.height - padding * 2;
        
        // 計算最大值
        let maxValue = 0;
        Object.values(datasets).forEach(values => {
            maxValue = Math.max(maxValue, ...values);
        });
        maxValue = maxValue || 1;
        
        // 繪製網格
        this.drawGrid(chartWidth, chartHeight, padding, maxValue);
        
        // 繪製長條
        const barWidth = chartWidth / labels.length * 0.6;
        const gap = chartWidth / labels.length * 0.4;
        const seriesCount = Object.keys(datasets).length;
        const singleBarWidth = barWidth / seriesCount;
        
        let colorIndex = 0;
        for (const [name, values] of Object.entries(datasets)) {
            this.drawBars(values, labels, chartWidth, chartHeight, padding, maxValue, 
                         singleBarWidth, gap, colorIndex, seriesCount);
            colorIndex++;
        }
        
        // 繪製 X 軸標籤
        this.drawXLabels(labels, chartWidth, padding, barWidth + gap);
        
        // 繪製圖例
        this.drawLegend(Object.keys(datasets), padding);
    }

    drawGrid(chartWidth, chartHeight, padding, maxValue) {
        const ctx = this.ctx;
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        
        const gridLines = 5;
        for (let i = 0; i <= gridLines; i++) {
            const y = padding + (chartHeight / gridLines) * i;
            
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(this.width - padding, y);
            ctx.stroke();
            
            const value = Math.round(maxValue * (1 - i / gridLines));
            ctx.fillStyle = '#64748b';
            ctx.font = `${this.options.fontSize}px ${this.options.fontFamily}`;
            ctx.textAlign = 'right';
            ctx.fillText(this.formatNumber(value), padding - 8, y + 4);
        }
    }

    drawBars(values, labels, chartWidth, chartHeight, padding, maxValue, 
             barWidth, gap, colorIndex, seriesCount) {
        const ctx = this.ctx;
        const color = this.getColor(colorIndex);
        const totalWidth = barWidth * seriesCount + gap;
        
        values.forEach((value, i) => {
            const barHeight = (value / maxValue) * chartHeight;
            const x = padding + totalWidth * i + gap / 2 + barWidth * colorIndex;
            const y = padding + chartHeight - barHeight;
            
            ctx.fillStyle = color;
            ctx.fillRect(x, y, barWidth - 2, barHeight);
        });
    }

    drawXLabels(labels, chartWidth, padding, groupWidth) {
        const ctx = this.ctx;
        
        ctx.fillStyle = '#64748b';
        ctx.font = `${this.options.fontSize}px ${this.options.fontFamily}`;
        ctx.textAlign = 'center';
        
        labels.forEach((label, i) => {
            const x = padding + groupWidth * i + groupWidth / 2;
            ctx.fillText(label, x, this.height - padding + 20);
        });
    }

    drawLegend(names, padding) {
        const ctx = this.ctx;
        let x = padding;
        
        names.forEach((name, i) => {
            const color = this.getColor(i);
            
            ctx.fillStyle = color;
            ctx.fillRect(x, 8, 16, 12);
            
            ctx.fillStyle = '#333';
            ctx.font = `${this.options.fontSize}px ${this.options.fontFamily}`;
            ctx.textAlign = 'left';
            ctx.fillText(name, x + 22, 18);
            
            x += ctx.measureText(name).width + 40;
        });
    }

    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }
}


// ===== 圓餅圖 =====

class PieChart extends Chart {
    render(data) {
        this.data = data;
        this.clear();
        
        const { labels, datasets } = data;
        const values = datasets.count || Object.values(datasets)[0];
        
        const total = values.reduce((a, b) => a + b, 0);
        if (total === 0) {
            this.drawEmpty();
            return;
        }
        
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        const radius = Math.min(centerX, centerY) - 60;
        
        let startAngle = -Math.PI / 2;
        
        values.forEach((value, i) => {
            const sliceAngle = (value / total) * Math.PI * 2;
            const endAngle = startAngle + sliceAngle;
            
            // 繪製扇形
            this.ctx.fillStyle = this.getColor(i);
            this.ctx.beginPath();
            this.ctx.moveTo(centerX, centerY);
            this.ctx.arc(centerX, centerY, radius, startAngle, endAngle);
            this.ctx.closePath();
            this.ctx.fill();
            
            // 繪製標籤
            const midAngle = startAngle + sliceAngle / 2;
            const labelRadius = radius * 0.7;
            const labelX = centerX + Math.cos(midAngle) * labelRadius;
            const labelY = centerY + Math.sin(midAngle) * labelRadius;
            
            const percent = Math.round(value / total * 100);
            if (percent >= 5) {  // 只顯示 >= 5% 的標籤
                this.ctx.fillStyle = 'white';
                this.ctx.font = `bold ${this.options.fontSize}px ${this.options.fontFamily}`;
                this.ctx.textAlign = 'center';
                this.ctx.textBaseline = 'middle';
                this.ctx.fillText(percent + '%', labelX, labelY);
            }
            
            startAngle = endAngle;
        });
        
        // 繪製圖例
        this.drawPieLegend(labels, values, total);
    }

    drawEmpty() {
        const ctx = this.ctx;
        ctx.fillStyle = '#e2e8f0';
        ctx.beginPath();
        ctx.arc(this.width / 2, this.height / 2, 80, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.fillStyle = '#64748b';
        ctx.font = `${this.options.fontSize}px ${this.options.fontFamily}`;
        ctx.textAlign = 'center';
        ctx.fillText('沒有資料', this.width / 2, this.height / 2);
    }

    drawPieLegend(labels, values, total) {
        const ctx = this.ctx;
        const startY = 20;
        const startX = this.width - 120;
        
        labels.forEach((label, i) => {
            const y = startY + i * 22;
            const percent = Math.round(values[i] / total * 100);
            
            ctx.fillStyle = this.getColor(i);
            ctx.fillRect(startX, y, 12, 12);
            
            ctx.fillStyle = '#333';
            ctx.font = `${this.options.fontSize - 1}px ${this.options.fontFamily}`;
            ctx.textAlign = 'left';
            ctx.fillText(`${label} (${percent}%)`, startX + 18, y + 10);
        });
    }
}


// ===== 儀表板圖表管理 =====

const Dashboard = {
    charts: {},

    /**
     * 初始化儀表板
     * @param {string} containerId - 容器 ID
     */
    async init(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px;">
                <div class="chart-card">
                    <h4>銷售趨勢</h4>
                    <canvas id="chart-sales"></canvas>
                </div>
                <div class="chart-card">
                    <h4>月度對比</h4>
                    <canvas id="chart-monthly"></canvas>
                </div>
                <div class="chart-card">
                    <h4>庫存品牌分布</h4>
                    <canvas id="chart-brand"></canvas>
                </div>
                <div class="chart-card">
                    <h4>庫存狀態</h4>
                    <canvas id="chart-status"></canvas>
                </div>
                <div class="chart-card">
                    <h4>客戶來源</h4>
                    <canvas id="chart-source"></canvas>
                </div>
                <div class="chart-card">
                    <h4>客戶成長</h4>
                    <canvas id="chart-growth"></canvas>
                </div>
            </div>
        `;

        // 添加樣式
        const style = document.createElement('style');
        style.textContent = `
            .chart-card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .chart-card h4 {
                margin: 0 0 15px 0;
                color: #1e3a5f;
            }
        `;
        document.head.appendChild(style);

        // 載入數據
        await this.loadData();
    },

    async loadData() {
        try {
            const response = await fetch('/api/charts/dashboard', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            const data = await response.json();

            if (data.success) {
                this.renderCharts(data.charts);
            }
        } catch (error) {
            console.error('載入圖表數據失敗:', error);
        }
    },

    renderCharts(data) {
        // 銷售趨勢
        if (data.sales_trend) {
            this.charts.sales = new LineChart(document.getElementById('chart-sales'));
            this.charts.sales.render(data.sales_trend);
        }

        // 月度對比
        if (data.monthly_comparison) {
            this.charts.monthly = new BarChart(document.getElementById('chart-monthly'));
            this.charts.monthly.render(data.monthly_comparison);
        }

        // 庫存品牌
        if (data.inventory_by_brand) {
            this.charts.brand = new BarChart(document.getElementById('chart-brand'));
            this.charts.brand.render(data.inventory_by_brand);
        }

        // 庫存狀態
        if (data.inventory_by_status) {
            this.charts.status = new PieChart(document.getElementById('chart-status'));
            this.charts.status.render(data.inventory_by_status);
        }

        // 客戶來源
        if (data.customer_by_source) {
            this.charts.source = new PieChart(document.getElementById('chart-source'));
            this.charts.source.render(data.customer_by_source);
        }

        // 客戶成長
        if (data.customer_growth) {
            this.charts.growth = new LineChart(document.getElementById('chart-growth'));
            this.charts.growth.render(data.customer_growth);
        }
    }
};


// ===== 匯出 =====

window.Charts = {
    LineChart,
    BarChart,
    PieChart,
    Dashboard
};


// 📚 知識點
// -----------
// 1. Canvas 繪圖：
//    - getContext('2d') 取得 2D 上下文
//    - beginPath/moveTo/lineTo/stroke 繪製路徑
//    - arc 繪製圓弧
//
// 2. 高 DPI 支援：
//    - devicePixelRatio 取得像素比
//    - canvas.width/height 設定實際像素
//    - canvas.style 設定 CSS 大小
//    - ctx.scale 縮放繪圖
//
// 3. 響應式：
//    - resize 事件監聽
//    - 重新計算大小並繪製
//
// 4. 數據格式化：
//    - K/M 單位轉換
//    - 百分比計算
//
// 5. 組合模式：
//    - 基礎 Chart 類
//    - 子類繼承並實現 render
