/**
 * 車行寶 CRM v5.1 - API 封裝
 * 北斗七星文創數位 × 織明
 */

// ===== API 基礎設定 =====
const API = {
    baseUrl: '',  // 同源，不需要設定
    
    /**
     * 取得 Token
     */
    getToken() {
        return localStorage.getItem('token');
    },
    
    /**
     * 發送請求
     * @param {string} endpoint - API 端點
     * @param {object} options - fetch 選項
     */
    async request(endpoint, options = {}) {
        const token = this.getToken();
        
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };
        
        try {
            const response = await fetch(endpoint, {
                ...options,
                headers
            });
            
            const data = await response.json();
            
            // 未授權，導向登入頁
            if (response.status === 401) {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/';
                return null;
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            return { success: false, error: '網路錯誤，請稍後再試' };
        }
    },
    
    /**
     * GET 請求
     */
    async get(endpoint, params = {}) {
        // 組合查詢字串
        const queryString = Object.entries(params)
            .filter(([_, v]) => v !== '' && v !== null && v !== undefined)
            .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
            .join('&');
        
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    },
    
    /**
     * POST 請求
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    /**
     * PUT 請求
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    /**
     * DELETE 請求
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// ===== 認證 API =====
const AuthAPI = {
    /**
     * 登入
     */
    async login(code, phone, password) {
        const result = await API.post('/api/login', { code, phone, password });
        if (result.success) {
            localStorage.setItem('token', result.token);
            localStorage.setItem('user', JSON.stringify(result));
        }
        return result;
    },
    
    /**
     * 註冊
     */
    async register(code, name, phone, password) {
        return API.post('/api/register', { code, name, phone, password });
    },
    
    /**
     * 登出
     */
    async logout() {
        await API.post('/api/logout');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/';
    },
    
    /**
     * 取得當前使用者
     */
    async me() {
        return API.get('/api/me');
    },
    
    /**
     * 檢查是否已登入
     */
    isLoggedIn() {
        return !!localStorage.getItem('token');
    },
    
    /**
     * 取得使用者資料
     */
    getUser() {
        const data = localStorage.getItem('user');
        return data ? JSON.parse(data) : null;
    }
};

// ===== 客戶 API =====
const CustomerAPI = {
    list(params = {}) {
        return API.get('/api/customers', params);
    },
    
    get(id) {
        return API.get(`/api/customers/${id}`);
    },
    
    create(data) {
        return API.post('/api/customers', data);
    },
    
    update(id, data) {
        return API.post(`/api/customers/${id}/update`, data);
    },
    
    delete(id) {
        return API.post(`/api/customers/${id}/delete`);
    }
};

// ===== 車輛 API =====
const VehicleAPI = {
    list(params = {}) {
        return API.get('/api/vehicles', params);
    },
    
    get(id) {
        return API.get(`/api/vehicles/${id}`);
    },
    
    create(data) {
        return API.post('/api/vehicles', data);
    },
    
    update(id, data) {
        return API.post(`/api/vehicles/${id}/update`, data);
    },
    
    delete(id) {
        return API.post(`/api/vehicles/${id}/delete`);
    }
};

// ===== 交易 API =====
const DealAPI = {
    list(params = {}) {
        return API.get('/api/deals', params);
    },
    
    get(id) {
        return API.get(`/api/deals/${id}`);
    },
    
    create(data) {
        return API.post('/api/deals', data);
    }
};

// ===== 跟進 API =====
const FollowupAPI = {
    list(params = {}) {
        return API.get('/api/followups', params);
    },
    
    create(data) {
        return API.post('/api/followups', data);
    }
};

// ===== 報表 API =====
const ReportAPI = {
    stats() {
        return API.get('/api/stats');
    },
    
    sales(startDate, endDate) {
        return API.get('/api/reports/sales', { start: startDate, end: endDate });
    },
    
    inventory() {
        return API.get('/api/reports/inventory');
    },
    
    customers() {
        return API.get('/api/reports/customers');
    },
    
    logs(limit = 50) {
        return API.get('/api/logs', { limit });
    }
};


/* 📚 知識點
 * -----------
 * 1. async/await：非同步語法
 *    - async function：宣告非同步函數
 *    - await：等待 Promise 完成
 *    - 比 .then() 鏈式寫法更易讀
 *
 * 2. fetch API：現代瀏覽器內建的 HTTP 請求
 *    - fetch(url, options)
 *    - 返回 Promise
 *    - response.json() 解析 JSON
 *
 * 3. localStorage：瀏覽器本地儲存
 *    - setItem(key, value)：存入
 *    - getItem(key)：取出
 *    - removeItem(key)：刪除
 *    - 只能存字串，物件需 JSON.stringify()
 *
 * 4. 展開運算符（Spread）：
 *    - { ...options, headers }：合併物件
 *    - ...(token && { key: value })：條件展開
 *
 * 5. encodeURIComponent：URL 編碼
 *    - 特殊字元轉換為 %XX 格式
 *    - 避免 URL 解析錯誤
 *
 * 6. 物件簡寫：
 *    - { list, get, create } 等同 { list: list, get: get, create: create }
 */
