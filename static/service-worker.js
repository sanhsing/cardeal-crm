/**
 * 車行寶 CRM v5.1 - Service Worker
 * 北斗七星文創數位 × 織明
 * 
 * 功能：離線快取、推播通知、背景同步
 */

const CACHE_NAME = 'cardeal-v5.1';
const STATIC_CACHE = 'cardeal-static-v1';
const DYNAMIC_CACHE = 'cardeal-dynamic-v1';

// 靜態資源（優先快取）
const STATIC_ASSETS = [
  '/',
  '/app',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/js/api.js',
  '/static/js/utils.js',
  '/static/js/components.js',
  '/static/js/charts.js',
  '/static/manifest.json'
];

// API 路徑（網路優先）
const API_ROUTES = ['/api/'];

// ===== 安裝事件 =====
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// ===== 啟動事件 =====
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((keys) => {
        return Promise.all(
          keys
            .filter((key) => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
            .map((key) => {
              console.log('[SW] Deleting old cache:', key);
              return caches.delete(key);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// ===== 請求攔截 =====
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // API 請求：網路優先，失敗時用快取
  if (API_ROUTES.some(route => url.pathname.startsWith(route))) {
    event.respondWith(networkFirst(request));
    return;
  }
  
  // 靜態資源：快取優先
  event.respondWith(cacheFirst(request));
});

// ===== 快取策略 =====

// 快取優先（靜態資源）
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    return offlineFallback(request);
  }
}

// 網路優先（API 請求）
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    return offlineFallback(request);
  }
}

// 離線回退
function offlineFallback(request) {
  if (request.headers.get('Accept').includes('application/json')) {
    return new Response(
      JSON.stringify({ success: false, error: '離線中，無法連線伺服器' }),
      { headers: { 'Content-Type': 'application/json' } }
    );
  }
  
  return new Response(
    '<h1>離線中</h1><p>請檢查網路連線</p>',
    { headers: { 'Content-Type': 'text/html' } }
  );
}

// ===== 推播通知 =====
self.addEventListener('push', (event) => {
  console.log('[SW] Push received');
  
  let data = { title: '車行寶通知', body: '您有新訊息' };
  
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }
  
  const options = {
    body: data.body,
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/badge-72.png',
    vibrate: [100, 50, 100],
    data: data.url || '/',
    actions: [
      { action: 'open', title: '查看' },
      { action: 'close', title: '關閉' }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// 通知點擊
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'close') {
    return;
  }
  
  event.waitUntil(
    clients.openWindow(event.notification.data || '/')
  );
});

// ===== 背景同步 =====
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'sync-deals') {
    event.waitUntil(syncDeals());
  }
});

async function syncDeals() {
  // 從 IndexedDB 取得待同步資料
  // 發送到伺服器
  console.log('[SW] Syncing deals...');
}


// 📚 知識點
// -----------
// 1. Service Worker 生命週期：
//    - install → activate → fetch
//    - skipWaiting()：跳過等待，立即啟用
//    - clients.claim()：控制所有頁面
//
// 2. 快取策略：
//    - Cache First：靜態資源，快取優先
//    - Network First：API，網路優先
//    - Stale While Revalidate：背景更新
//
// 3. Push API：
//    - 伺服器主動推送通知
//    - 需要 VAPID 金鑰
//    - 用戶需授權
//
// 4. Background Sync：
//    - 離線時暫存操作
//    - 網路恢復時自動同步
