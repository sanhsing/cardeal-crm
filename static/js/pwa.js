/**
 * 車行寶 CRM v5.2 - PWA 初始化
 * 北斗七星文創數位 × 織明
 */

// ===== VAPID 公鑰配置 =====
// 從伺服器取得或使用預設值
const VAPID_PUBLIC_KEY = 'BBLB6VwPWNCwcmYeN_XFa-q9_QT3EDuLNGjgB6k9vyedDr2MPLW410Ng_FVZcmjb8xhiTeAkhbyg20iZEpqex0w';

// ===== Service Worker 註冊 =====
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/static/service-worker.js');
      console.log('[PWA] SW registered:', registration.scope);
      
      // 檢查更新
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            showUpdateNotification();
          }
        });
      });
    } catch (error) {
      console.error('[PWA] SW registration failed:', error);
    }
  });
}

// ===== 安裝提示 =====
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  showInstallButton();
});

function showInstallButton() {
  const btn = document.getElementById('install-btn');
  if (btn) {
    btn.style.display = 'block';
    btn.addEventListener('click', installApp);
  }
}

async function installApp() {
  if (!deferredPrompt) return;
  
  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  
  console.log('[PWA] Install outcome:', outcome);
  deferredPrompt = null;
  
  const btn = document.getElementById('install-btn');
  if (btn) btn.style.display = 'none';
}

// ===== 推播通知 =====
async function requestNotificationPermission() {
  if (!('Notification' in window)) {
    console.log('[PWA] Notifications not supported');
    return false;
  }
  
  const permission = await Notification.requestPermission();
  console.log('[PWA] Notification permission:', permission);
  
  if (permission === 'granted') {
    await subscribeToPush();
  }
  
  return permission === 'granted';
}

async function subscribeToPush() {
  try {
    const registration = await navigator.serviceWorker.ready;
    
    // 檢查是否已訂閱
    let subscription = await registration.pushManager.getSubscription();
    
    if (!subscription) {
      // 訂閱推播
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      });
      
      console.log('[PWA] Push subscribed');
    }
    
    // 發送訂閱資訊到伺服器
    await sendSubscriptionToServer(subscription);
    
    return subscription;
  } catch (error) {
    console.error('[PWA] Push subscription failed:', error);
    return null;
  }
}

async function sendSubscriptionToServer(subscription) {
  try {
    const response = await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subscription: subscription.toJSON()
      })
    });
    
    const result = await response.json();
    console.log('[PWA] Subscription saved:', result);
  } catch (error) {
    console.error('[PWA] Failed to save subscription:', error);
  }
}

async function unsubscribeFromPush() {
  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    
    if (subscription) {
      // 通知伺服器
      await fetch('/api/push/unsubscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint: subscription.endpoint })
      });
      
      // 取消訂閱
      await subscription.unsubscribe();
      console.log('[PWA] Unsubscribed from push');
    }
  } catch (error) {
    console.error('[PWA] Unsubscribe failed:', error);
  }
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');
  
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  
  return outputArray;
}

// ===== 更新提示 =====
function showUpdateNotification() {
  const div = document.createElement('div');
  div.className = 'update-notification';
  div.innerHTML = `
    <p>🔄 有新版本可用</p>
    <button onclick="location.reload()">立即更新</button>
    <button onclick="this.parentElement.remove()">稍後</button>
  `;
  document.body.appendChild(div);
}

// ===== 離線狀態 =====
window.addEventListener('online', () => {
  console.log('[PWA] Online');
  document.body.classList.remove('offline');
  showToast('✅ 已恢復連線');
});

window.addEventListener('offline', () => {
  console.log('[PWA] Offline');
  document.body.classList.add('offline');
  showToast('📴 目前離線中');
});

function showToast(message) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => toast.remove(), 3000);
}

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
  // 檢查是否已安裝
  if (window.matchMedia('(display-mode: standalone)').matches) {
    console.log('[PWA] Running in standalone mode');
  }
  
  // 自動請求通知權限（可選）
  // requestNotificationPermission();
});

// ===== 導出功能 =====
window.PWA = {
  install: installApp,
  requestNotification: requestNotificationPermission,
  subscribe: subscribeToPush,
  unsubscribe: unsubscribeFromPush,
  VAPID_PUBLIC_KEY
};


// 📚 知識點
// -----------
// 1. applicationServerKey：
//    - VAPID 公鑰用於 Push 訂閱
//    - 需要轉換為 Uint8Array
//
// 2. userVisibleOnly: true：
//    - 必須設定，表示每次推播都會顯示通知
//    - 瀏覽器要求
//
// 3. subscription.toJSON()：
//    - 包含 endpoint, keys.p256dh, keys.auth
//    - 發送到伺服器儲存
