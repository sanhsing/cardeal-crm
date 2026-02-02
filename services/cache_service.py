"""
車行寶 CRM v5.1 - 快取服務模組
北斗七星文創數位 × 織明

功能：記憶體快取、LRU 策略、TTL 過期
"""
from typing import Dict, List, Any, Optional, Union, Callable

import time
import threading
from collections import OrderedDict
from functools import wraps

# ===== LRU 快取實作 =====

class LRUCache:
    """LRU (Least Recently Used) 快取"""
    
    def __init__(self, max_size=1000, default_ttl=300):
        """
        Args:
            max_size: 最大快取數量
            default_ttl: 預設過期時間（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.lock = threading.Lock()
    
    def get(self, key):
        """取得快取值"""
        with self.lock:
            if key not in self.cache:
                return None
            
            value, expiry = self.cache[key]
            
            # 檢查是否過期
            if expiry and time.time() > expiry:
                del self.cache[key]
                return None
            
            # 移到最後（最近使用）
            self.cache.move_to_end(key)
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """設定快取值"""
        with self.lock:
            if ttl is None:
                ttl = self.default_ttl
            
            expiry = time.time() + ttl if ttl > 0 else None
            
            # 如果已存在，先刪除
            if key in self.cache:
                del self.cache[key]
            
            # 檢查容量
            while len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)  # 刪除最舊的
            
            self.cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        """刪除快取"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空快取"""
        with self.lock:
            self.cache.clear()
    
    def cleanup(self):
        """清理過期項目"""
        with self.lock:
            now = time.time()
            expired = [k for k, (v, exp) in self.cache.items() 
                       if exp and now > exp]
            for k in expired:
                del self.cache[k]
            return len(expired)
    
    def stats(self):
        """快取統計"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'keys': list(self.cache.keys())[:20]  # 最多顯示20個
            }


# ===== 全域快取實例 =====

# 通用快取
_cache = LRUCache(max_size=1000, default_ttl=300)

# 專用快取
_session_cache = LRUCache(max_size=500, default_ttl=3600)
_stats_cache = LRUCache(max_size=100, default_ttl=60)
_price_cache = LRUCache(max_size=200, default_ttl=1800)


def get_cache(name: str = 'default') -> 'LRUCache':
    """取得快取實例"""
    caches = {
        'default': _cache,
        'session': _session_cache,
        'stats': _stats_cache,
        'price': _price_cache
    }
    return caches.get(name, _cache)


# ===== 快取裝飾器 =====

def cached(ttl: int = 300, key_prefix: str = '', cache_name: str = 'default') -> Callable:
    """快取裝飾器
    
    用法：
        @cached(ttl=60, key_prefix='stats')
        def get_stats(tenant_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 產生快取鍵
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{':'.join(str(a) for a in args)}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            
            cache = get_cache(cache_name)
            
            # 嘗試取得快取
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 執行函數
            result = func(*args, **kwargs)
            
            # 存入快取
            if result is not None:
                cache.set(cache_key, result, ttl)
            
            return result
        
        # 提供手動清除快取的方法
        def invalidate(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{':'.join(str(a) for a in args)}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            get_cache(cache_name).delete(cache_key)
        
        wrapper.invalidate = invalidate
        return wrapper
    
    return decorator


# ===== 快取鍵生成 =====

def make_key(*args, prefix: str = '') -> str:
    """產生快取鍵"""
    parts = [prefix] if prefix else []
    parts.extend(str(a) for a in args)
    return ':'.join(parts)


# ===== 常用快取操作 =====

def cache_get(key: str, default: Any = None) -> Any:
    """取得快取"""
    result = _cache.get(key)
    return result if result is not None else default


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """設定快取"""
    _cache.set(key, value, ttl)


def cache_delete(key: str) -> bool:
    """刪除快取"""
    return _cache.delete(key)


def cache_clear():
    """清空所有快取"""
    _cache.clear()
    _session_cache.clear()
    _stats_cache.clear()
    _price_cache.clear()


def cache_cleanup():
    """清理過期快取"""
    count = 0
    count += _cache.cleanup()
    count += _session_cache.cleanup()
    count += _stats_cache.cleanup()
    count += _price_cache.cleanup()
    return count


def cache_stats():
    """所有快取統計"""
    return {
        'default': _cache.stats(),
        'session': _session_cache.stats(),
        'stats': _stats_cache.stats(),
        'price': _price_cache.stats()
    }


# ===== 定時清理任務 =====

_cleanup_thread = None
_cleanup_running = False

def start_cleanup_task(interval=60):
    """啟動定時清理任務"""
    global _cleanup_thread, _cleanup_running
    
    if _cleanup_running:
        return
    
    _cleanup_running = True
    
    def cleanup_loop():
        while _cleanup_running:
            time.sleep(interval)
            try:
                cache_cleanup()
            except:
                pass
    
    _cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    _cleanup_thread.start()


def stop_cleanup_task():
    """停止定時清理任務"""
    global _cleanup_running
    _cleanup_running = False


# 📚 知識點
# -----------
# 1. LRU (Least Recently Used)：
#    - 最近最少使用淘汰策略
#    - 快取滿時，刪除最久沒用的
#    - OrderedDict 維護插入順序
#
# 2. OrderedDict：
#    - 有序字典，記住插入順序
#    - .move_to_end(key)：移到最後
#    - .popitem(last=False)：刪除最前面的
#
# 3. threading.Lock：
#    - 執行緒鎖，確保線程安全
#    - with self.lock: 自動取得/釋放鎖
#    - 防止多執行緒同時修改資料
#
# 4. @wraps 裝飾器：
#    - 保留原函數的 __name__、__doc__
#    - 讓裝飾後的函數看起來像原函數
#
# 5. daemon=True：
#    - 守護執行緒，主程式結束時自動終止
#    - 不會阻止程式退出
#
# 6. TTL (Time To Live)：
#    - 快取過期時間
#    - 過期後自動失效
#    - 確保資料不會太舊
