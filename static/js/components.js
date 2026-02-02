/**
 * 車行寶 CRM v5.1 - 前端組件庫
 * 北斗七星文創數位 × 織明
 * 
 * 可重用的 UI 組件
 */

// ===== Modal 組件 =====

const Modal = {
    /**
     * 顯示 Modal
     * @param {Object} options - 配置選項
     * @param {string} options.title - 標題
     * @param {string} options.content - 內容（HTML）
     * @param {Function} options.onConfirm - 確認回調
     * @param {Function} options.onCancel - 取消回調
     * @param {string} options.confirmText - 確認按鈕文字
     * @param {string} options.cancelText - 取消按鈕文字
     * @param {string} options.size - 大小（small/medium/large）
     */
    show(options = {}) {
        const {
            title = '提示',
            content = '',
            onConfirm = null,
            onCancel = null,
            confirmText = '確定',
            cancelText = '取消',
            size = 'medium',
            showCancel = true
        } = options;

        // 移除已存在的 modal
        this.hide();

        const sizeClass = {
            small: 'max-width: 400px',
            medium: 'max-width: 600px',
            large: 'max-width: 800px'
        }[size];

        const modalHtml = `
            <div class="modal-overlay" id="modal-overlay" style="
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            ">
                <div class="modal-content" style="
                    background: white;
                    border-radius: 12px;
                    ${sizeClass};
                    width: 90%;
                    max-height: 80vh;
                    overflow: hidden;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                ">
                    <div class="modal-header" style="
                        padding: 20px;
                        border-bottom: 1px solid #eee;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <h3 style="margin: 0; font-size: 18px;">${title}</h3>
                        <button id="modal-close" style="
                            background: none;
                            border: none;
                            font-size: 24px;
                            cursor: pointer;
                            color: #666;
                        ">&times;</button>
                    </div>
                    <div class="modal-body" style="
                        padding: 20px;
                        overflow-y: auto;
                        max-height: calc(80vh - 140px);
                    ">
                        ${content}
                    </div>
                    <div class="modal-footer" style="
                        padding: 15px 20px;
                        border-top: 1px solid #eee;
                        display: flex;
                        justify-content: flex-end;
                        gap: 10px;
                    ">
                        ${showCancel ? `<button id="modal-cancel" class="btn btn-secondary">${cancelText}</button>` : ''}
                        <button id="modal-confirm" class="btn btn-primary">${confirmText}</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 綁定事件
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target.id === 'modal-overlay') {
                this.hide();
                if (onCancel) onCancel();
            }
        });

        document.getElementById('modal-close').addEventListener('click', () => {
            this.hide();
            if (onCancel) onCancel();
        });

        if (showCancel) {
            document.getElementById('modal-cancel').addEventListener('click', () => {
                this.hide();
                if (onCancel) onCancel();
            });
        }

        document.getElementById('modal-confirm').addEventListener('click', () => {
            if (onConfirm) {
                const result = onConfirm();
                if (result !== false) {
                    this.hide();
                }
            } else {
                this.hide();
            }
        });

        // ESC 關閉
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                this.hide();
                if (onCancel) onCancel();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    },

    /**
     * 隱藏 Modal
     */
    hide() {
        const overlay = document.getElementById('modal-overlay');
        if (overlay) {
            overlay.remove();
        }
    },

    /**
     * 確認對話框
     */
    confirm(message, onConfirm) {
        this.show({
            title: '確認',
            content: `<p>${message}</p>`,
            onConfirm,
            size: 'small'
        });
    },

    /**
     * 警告對話框
     */
    alert(message, title = '提示') {
        this.show({
            title,
            content: `<p>${message}</p>`,
            showCancel: false,
            size: 'small'
        });
    }
};


// ===== Toast 組件 =====

const Toast = {
    container: null,

    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(this.container);
        }
    },

    /**
     * 顯示 Toast
     * @param {string} message - 訊息
     * @param {string} type - 類型（success/error/warning/info）
     * @param {number} duration - 顯示時間（毫秒）
     */
    show(message, type = 'info', duration = 3000) {
        this.init();

        const colors = {
            success: { bg: '#10b981', icon: '✓' },
            error: { bg: '#ef4444', icon: '✕' },
            warning: { bg: '#f59e0b', icon: '⚠' },
            info: { bg: '#3b82f6', icon: 'ℹ' }
        };

        const { bg, icon } = colors[type] || colors.info;

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.style.cssText = `
            background: ${bg};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease;
            min-width: 200px;
        `;
        toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;

        this.container.appendChild(toast);

        // 自動移除
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    success(message) { this.show(message, 'success'); },
    error(message) { this.show(message, 'error', 5000); },
    warning(message) { this.show(message, 'warning'); },
    info(message) { this.show(message, 'info'); }
};

// 添加動畫樣式
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
`;
document.head.appendChild(style);


// ===== Loading 組件 =====

const Loading = {
    element: null,

    /**
     * 顯示 Loading
     * @param {string} message - 提示訊息
     */
    show(message = '載入中...') {
        this.hide();

        const html = `
            <div id="loading-overlay" style="
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255,255,255,0.8);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            ">
                <div class="spinner" style="
                    width: 40px;
                    height: 40px;
                    border: 3px solid #e2e8f0;
                    border-top-color: #1e3a5f;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                <p style="margin-top: 15px; color: #64748b;">${message}</p>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', html);

        // 添加旋轉動畫
        if (!document.getElementById('spinner-style')) {
            const spinStyle = document.createElement('style');
            spinStyle.id = 'spinner-style';
            spinStyle.textContent = `
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(spinStyle);
        }
    },

    /**
     * 隱藏 Loading
     */
    hide() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }
};


// ===== Pagination 組件 =====

const Pagination = {
    /**
     * 渲染分頁
     * @param {Object} options - 配置
     * @param {HTMLElement} container - 容器
     * @param {number} options.page - 當前頁
     * @param {number} options.total - 總筆數
     * @param {number} options.limit - 每頁筆數
     * @param {Function} options.onChange - 頁碼變更回調
     */
    render(container, options) {
        const { page, total, limit, onChange } = options;
        const totalPages = Math.ceil(total / limit);

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = '<div class="pagination" style="display: flex; gap: 5px; justify-content: center; margin-top: 20px;">';

        // 上一頁
        html += `<button class="page-btn" ${page <= 1 ? 'disabled' : ''} data-page="${page - 1}" style="
            padding: 8px 12px;
            border: 1px solid #e2e8f0;
            background: white;
            border-radius: 6px;
            cursor: ${page <= 1 ? 'not-allowed' : 'pointer'};
            opacity: ${page <= 1 ? '0.5' : '1'};
        ">‹</button>`;

        // 頁碼
        const showPages = this.getShowPages(page, totalPages);
        for (const p of showPages) {
            if (p === '...') {
                html += `<span style="padding: 8px 12px;">...</span>`;
            } else {
                html += `<button class="page-btn" data-page="${p}" style="
                    padding: 8px 12px;
                    border: 1px solid ${p === page ? '#1e3a5f' : '#e2e8f0'};
                    background: ${p === page ? '#1e3a5f' : 'white'};
                    color: ${p === page ? 'white' : '#333'};
                    border-radius: 6px;
                    cursor: pointer;
                ">${p}</button>`;
            }
        }

        // 下一頁
        html += `<button class="page-btn" ${page >= totalPages ? 'disabled' : ''} data-page="${page + 1}" style="
            padding: 8px 12px;
            border: 1px solid #e2e8f0;
            background: white;
            border-radius: 6px;
            cursor: ${page >= totalPages ? 'not-allowed' : 'pointer'};
            opacity: ${page >= totalPages ? '0.5' : '1'};
        ">›</button>`;

        html += '</div>';
        html += `<div style="text-align: center; color: #64748b; font-size: 14px; margin-top: 10px;">
            共 ${total} 筆，第 ${page}/${totalPages} 頁
        </div>`;

        container.innerHTML = html;

        // 綁定事件
        container.querySelectorAll('.page-btn:not([disabled])').forEach(btn => {
            btn.addEventListener('click', () => {
                const newPage = parseInt(btn.dataset.page);
                if (onChange) onChange(newPage);
            });
        });
    },

    getShowPages(current, total) {
        const pages = [];
        const delta = 2;

        let start = Math.max(1, current - delta);
        let end = Math.min(total, current + delta);

        if (start > 1) {
            pages.push(1);
            if (start > 2) pages.push('...');
        }

        for (let i = start; i <= end; i++) {
            pages.push(i);
        }

        if (end < total) {
            if (end < total - 1) pages.push('...');
            pages.push(total);
        }

        return pages;
    }
};


// ===== Table 組件 =====

const Table = {
    /**
     * 渲染表格
     * @param {HTMLElement} container - 容器
     * @param {Object} options - 配置
     * @param {Array} options.columns - 欄位定義
     * @param {Array} options.data - 資料
     * @param {boolean} options.selectable - 是否可選擇
     * @param {Function} options.onSelect - 選擇回調
     */
    render(container, options) {
        const { columns, data, selectable = false, onSelect = null, emptyText = '沒有資料' } = options;

        if (!data || data.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #64748b;">
                    ${emptyText}
                </div>
            `;
            return;
        }

        let html = '<table class="data-table" style="width: 100%; border-collapse: collapse;">';

        // 表頭
        html += '<thead><tr style="background: #f8fafc;">';
        if (selectable) {
            html += '<th style="padding: 12px; width: 40px;"><input type="checkbox" id="select-all"></th>';
        }
        for (const col of columns) {
            html += `<th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">${col.title}</th>`;
        }
        html += '</tr></thead>';

        // 表身
        html += '<tbody>';
        for (const row of data) {
            html += `<tr data-id="${row.id}" style="border-bottom: 1px solid #e2e8f0;">`;
            if (selectable) {
                html += `<td style="padding: 12px;"><input type="checkbox" class="row-select" data-id="${row.id}"></td>`;
            }
            for (const col of columns) {
                const value = col.render ? col.render(row[col.key], row) : (row[col.key] ?? '');
                html += `<td style="padding: 12px;">${value}</td>`;
            }
            html += '</tr>';
        }
        html += '</tbody></table>';

        container.innerHTML = html;

        // 綁定選擇事件
        if (selectable) {
            const selectAll = container.querySelector('#select-all');
            const rowSelects = container.querySelectorAll('.row-select');

            selectAll.addEventListener('change', () => {
                rowSelects.forEach(cb => cb.checked = selectAll.checked);
                if (onSelect) onSelect(this.getSelected(container));
            });

            rowSelects.forEach(cb => {
                cb.addEventListener('change', () => {
                    selectAll.checked = [...rowSelects].every(c => c.checked);
                    if (onSelect) onSelect(this.getSelected(container));
                });
            });
        }
    },

    getSelected(container) {
        const selected = [];
        container.querySelectorAll('.row-select:checked').forEach(cb => {
            selected.push(parseInt(cb.dataset.id));
        });
        return selected;
    }
};


// ===== 匯出 =====

window.Components = {
    Modal,
    Toast,
    Loading,
    Pagination,
    Table
};


// 📚 知識點
// -----------
// 1. 組件化設計：
//    - 單一職責
//    - 可重用
//    - 狀態封裝
//
// 2. CSS in JS：
//    - 內聯樣式
//    - 避免全局污染
//    - 便於組件封裝
//
// 3. 事件委派：
//    - 動態元素事件綁定
//    - 減少事件監聽器
//
// 4. 動畫：
//    - CSS @keyframes
//    - animation 屬性
//    - 進入/離開動畫
//
// 5. 無障礙：
//    - ESC 關閉 Modal
//    - disabled 狀態
