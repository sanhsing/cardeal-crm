/**
 * 車行寶 CRM v5.1 - 工具函數
 * 北斗七星文創數位 × 織明
 */

// ===== 格式化工具 =====

/**
 * 格式化金額
 * @param {number} amount - 金額
 * @returns {string} 格式化後的金額
 */
function formatMoney(amount) {
    if (amount === null || amount === undefined) return '-';
    return '$' + Number(amount).toLocaleString('zh-TW');
}

/**
 * 格式化日期
 * @param {string} dateStr - 日期字串
 * @param {string} format - 格式（'date' | 'datetime' | 'relative'）
 */
function formatDate(dateStr, format = 'date') {
    if (!dateStr) return '-';
    
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    
    if (format === 'relative') {
        return getRelativeTime(date);
    }
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    if (format === 'datetime') {
        const hour = String(date.getHours()).padStart(2, '0');
        const minute = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day} ${hour}:${minute}`;
    }
    
    return `${year}-${month}-${day}`;
}

/**
 * 取得相對時間
 */
function getRelativeTime(date) {
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (seconds < 60) return '剛剛';
    if (minutes < 60) return `${minutes} 分鐘前`;
    if (hours < 24) return `${hours} 小時前`;
    if (days < 7) return `${days} 天前`;
    
    return formatDate(date, 'date');
}

/**
 * 格式化電話
 */
function formatPhone(phone) {
    if (!phone) return '-';
    // 0912345678 → 0912-345-678
    if (phone.length === 10 && phone.startsWith('09')) {
        return `${phone.slice(0, 4)}-${phone.slice(4, 7)}-${phone.slice(7)}`;
    }
    return phone;
}

// ===== 對照表 =====

const STATUS_MAP = {
    in_stock: { name: '在庫', badge: 'success' },
    reserved: { name: '已預訂', badge: 'warning' },
    sold: { name: '已售出', badge: 'default' },
    maintenance: { name: '整備中', badge: 'info' }
};

const SOURCE_MAP = {
    walk_in: '現場來店',
    phone: '電話詢問',
    line: 'LINE',
    facebook: 'Facebook',
    referral: '朋友介紹',
    web: '網站',
    other: '其他'
};

const LEVEL_MAP = {
    vip: { name: 'VIP', badge: 'warning' },
    normal: { name: '一般', badge: 'default' },
    potential: { name: '潛在', badge: 'info' },
    cold: { name: '冷淡', badge: 'default' }
};

const DEAL_TYPE_MAP = {
    buy: { name: '收購', badge: 'info' },
    sell: { name: '售出', badge: 'success' }
};

/**
 * 取得狀態名稱
 */
function getStatusName(status) {
    return STATUS_MAP[status]?.name || status;
}

/**
 * 取得狀態徽章樣式
 */
function getStatusBadge(status) {
    return STATUS_MAP[status]?.badge || 'default';
}

/**
 * 取得來源名稱
 */
function getSourceName(source) {
    return SOURCE_MAP[source] || source;
}

/**
 * 取得等級名稱
 */
function getLevelName(level) {
    return LEVEL_MAP[level]?.name || level;
}

/**
 * 取得等級徽章
 */
function getLevelBadge(level) {
    return LEVEL_MAP[level]?.badge || 'default';
}

/**
 * 取得交易類型名稱
 */
function getDealTypeName(type) {
    return DEAL_TYPE_MAP[type]?.name || type;
}

/**
 * 取得交易類型徽章
 */
function getDealTypeBadge(type) {
    return DEAL_TYPE_MAP[type]?.badge || 'default';
}

// ===== DOM 工具 =====

/**
 * 選取元素
 */
function $(selector) {
    return document.querySelector(selector);
}

/**
 * 選取多個元素
 */
function $$(selector) {
    return document.querySelectorAll(selector);
}

/**
 * 建立元素
 */
function createElement(tag, attrs = {}, children = []) {
    const el = document.createElement(tag);
    
    for (const [key, value] of Object.entries(attrs)) {
        if (key === 'className') {
            el.className = value;
        } else if (key === 'style' && typeof value === 'object') {
            Object.assign(el.style, value);
        } else if (key.startsWith('on') && typeof value === 'function') {
            el.addEventListener(key.slice(2).toLowerCase(), value);
        } else {
            el.setAttribute(key, value);
        }
    }
    
    for (const child of children) {
        if (typeof child === 'string') {
            el.appendChild(document.createTextNode(child));
        } else if (child instanceof Node) {
            el.appendChild(child);
        }
    }
    
    return el;
}

// ===== Toast 通知 =====

/**
 * 顯示 Toast 通知
 * @param {string} message - 訊息
 * @param {string} type - 類型（'success' | 'error' | 'warning' | 'info'）
 * @param {number} duration - 持續時間（毫秒）
 */
function showToast(message, type = 'info', duration = 3000) {
    let container = $('#toast-container');
    if (!container) {
        container = createElement('div', { id: 'toast-container', className: 'toast-container' });
        document.body.appendChild(container);
    }
    
    const toast = createElement('div', { className: `toast ${type}` }, [message]);
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ===== Modal 工具 =====

/**
 * 顯示 Modal
 */
function showModal(id) {
    const modal = $(`#${id}`);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * 隱藏 Modal
 */
function hideModal(id) {
    const modal = $(`#${id}`);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// ===== 表單工具 =====

/**
 * 取得表單資料
 */
function getFormData(formId) {
    const form = $(`#${formId}`);
    if (!form) return {};
    
    const formData = new FormData(form);
    const data = {};
    
    for (const [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    return data;
}

/**
 * 重設表單
 */
function resetForm(formId) {
    const form = $(`#${formId}`);
    if (form) form.reset();
}

/**
 * 設定表單資料
 */
function setFormData(formId, data) {
    const form = $(`#${formId}`);
    if (!form) return;
    
    for (const [key, value] of Object.entries(data)) {
        const input = form.elements[key];
        if (input) {
            input.value = value ?? '';
        }
    }
}

// ===== 驗證工具 =====

/**
 * 驗證手機號碼
 */
function isValidPhone(phone) {
    return /^09\d{8}$/.test(phone);
}

/**
 * 驗證 Email
 */
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// ===== 防抖與節流 =====

/**
 * 防抖
 */
function debounce(fn, delay = 300) {
    let timer = null;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

/**
 * 節流
 */
function throttle(fn, limit = 100) {
    let inThrottle = false;
    return function(...args) {
        if (!inThrottle) {
            fn.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}


/* 📚 知識點
 * -----------
 * 1. toLocaleString('zh-TW')：本地化格式
 *    - 數字會加千分位逗號
 *    - 日期會轉換為當地格式
 *
 * 2. padStart(2, '0')：字串補齊
 *    - '5'.padStart(2, '0') → '05'
 *    - 常用於日期、時間格式化
 *
 * 3. 可選鏈（Optional Chaining）：
 *    - obj?.prop：如果 obj 是 null/undefined 就返回 undefined
 *    - 避免 "Cannot read property of undefined" 錯誤
 *
 * 4. 空值合併（Nullish Coalescing）：
 *    - value ?? '預設'：只有 null/undefined 才用預設值
 *    - 與 || 不同：0、'' 不會被替換
 *
 * 5. 防抖 vs 節流：
 *    - debounce：延遲執行，連續觸發只執行最後一次
 *      用於：搜尋輸入、視窗 resize
 *    - throttle：限制頻率，一段時間內只執行一次
 *      用於：滾動事件、按鈕連點防護
 *
 * 6. FormData：表單資料收集
 *    - new FormData(form)：自動收集所有表單欄位
 *    - .entries()：返回 [name, value] 迭代器
 */
