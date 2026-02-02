/**
 * 車行寶 CRM v5.2 - UI 組件系統
 * 北斗七星文創數位 × 織明
 */

// ============================================================
// Toast 通知系統
// ============================================================
const Toast = {
    container: null,
    
    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:10px;';
            document.body.appendChild(this.container);
        }
    },
    
    show(message, type = 'info', duration = 3000) {
        this.init();
        
        const toast = document.createElement('div');
        const colors = {
            success: '#38ef7d',
            error: '#f5576c',
            warning: '#ffa726',
            info: '#667eea'
        };
        
        toast.style.cssText = `
            padding: 16px 24px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            background: ${colors[type] || colors.info};
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        `;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        toast.innerHTML = `<span>${icons[type] || icons.info}</span><span>${message}</span>`;
        this.container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },
    
    success(msg) { this.show(msg, 'success'); },
    error(msg) { this.show(msg, 'error'); },
    warning(msg) { this.show(msg, 'warning'); },
    info(msg) { this.show(msg, 'info'); }
};

// ============================================================
// Modal 模態框
// ============================================================
const Modal = {
    show(options) {
        const { title, content, onConfirm, onCancel, confirmText = '確定', cancelText = '取消' } = options;
        
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.style.cssText = `
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9998;
            animation: fadeIn 0.2s ease;
        `;
        
        overlay.innerHTML = `
            <div class="modal" style="
                background: white;
                border-radius: 16px;
                max-width: 500px;
                width: 90%;
                max-height: 90vh;
                overflow: hidden;
                animation: scaleIn 0.2s ease;
            ">
                <div class="modal-header" style="
                    padding: 20px;
                    border-bottom: 1px solid #e2e8f0;
                    font-size: 18px;
                    font-weight: 600;
                ">${title || '提示'}</div>
                <div class="modal-body" style="padding: 20px;">
                    ${content}
                </div>
                <div class="modal-footer" style="
                    padding: 20px;
                    border-top: 1px solid #e2e8f0;
                    display: flex;
                    justify-content: flex-end;
                    gap: 12px;
                ">
                    <button class="btn-cancel" style="
                        padding: 10px 20px;
                        border-radius: 8px;
                        border: 1px solid #e2e8f0;
                        background: white;
                        cursor: pointer;
                    ">${cancelText}</button>
                    <button class="btn-confirm" style="
                        padding: 10px 20px;
                        border-radius: 8px;
                        border: none;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        cursor: pointer;
                    ">${confirmText}</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        const close = () => {
            overlay.style.animation = 'fadeOut 0.2s ease';
            setTimeout(() => overlay.remove(), 200);
        };
        
        overlay.querySelector('.btn-cancel').onclick = () => {
            if (onCancel) onCancel();
            close();
        };
        
        overlay.querySelector('.btn-confirm').onclick = () => {
            if (onConfirm) onConfirm();
            close();
        };
        
        overlay.onclick = (e) => {
            if (e.target === overlay) close();
        };
        
        return { close };
    },
    
    confirm(message, onConfirm) {
        return this.show({
            title: '確認',
            content: `<p>${message}</p>`,
            onConfirm
        });
    },
    
    alert(message) {
        return this.show({
            title: '提示',
            content: `<p>${message}</p>`,
            cancelText: null,
            confirmText: '知道了'
        });
    }
};

// ============================================================
// Loading 載入狀態
// ============================================================
const Loading = {
    overlay: null,
    
    show(message = '載入中...') {
        if (this.overlay) return;
        
        this.overlay = document.createElement('div');
        this.overlay.style.cssText = `
            position: fixed;
            inset: 0;
            background: rgba(255,255,255,0.9);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        `;
        
        this.overlay.innerHTML = `
            <div class="spinner" style="
                width: 50px;
                height: 50px;
                border: 4px solid #e2e8f0;
                border-top-color: #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            "></div>
            <p style="margin-top: 16px; color: #475569;">${message}</p>
        `;
        
        document.body.appendChild(this.overlay);
    },
    
    hide() {
        if (this.overlay) {
            this.overlay.remove();
            this.overlay = null;
        }
    }
};

// ============================================================
// 表格組件
// ============================================================
const DataTable = {
    render(containerId, options) {
        const { columns, data, onRowClick, emptyMessage = '暫無數據' } = options;
        const container = document.getElementById(containerId);
        
        if (!data || data.length === 0) {
            container.innerHTML = `
                <div style="text-align:center;padding:40px;color:#94a3b8;">
                    <div style="font-size:48px;margin-bottom:16px;">📭</div>
                    <p>${emptyMessage}</p>
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="table-container" style="overflow-x:auto;">
                <table class="table" style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr>
                            ${columns.map(col => `
                                <th style="
                                    background:#f8fafc;
                                    padding:12px 16px;
                                    text-align:left;
                                    font-weight:600;
                                    color:#475569;
                                    border-bottom:2px solid #e2e8f0;
                                ">${col.label}</th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.forEach((row, index) => {
            html += `<tr data-index="${index}" style="cursor:${onRowClick ? 'pointer' : 'default'};">`;
            columns.forEach(col => {
                let value = row[col.key];
                if (col.render) {
                    value = col.render(value, row);
                }
                html += `<td style="padding:12px 16px;border-bottom:1px solid #e2e8f0;">${value}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        container.innerHTML = html;
        
        if (onRowClick) {
            container.querySelectorAll('tbody tr').forEach(tr => {
                tr.onclick = () => onRowClick(data[tr.dataset.index]);
                tr.onmouseenter = () => tr.style.background = '#f8fafc';
                tr.onmouseleave = () => tr.style.background = '';
            });
        }
    }
};

// ============================================================
// 動畫樣式
// ============================================================
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
    @keyframes scaleIn {
        from { transform: scale(0.9); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// 導出
window.Toast = Toast;
window.Modal = Modal;
window.Loading = Loading;
window.DataTable = DataTable;

console.log('🚗 車行寶 UI 組件已載入');
