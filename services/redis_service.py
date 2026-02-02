#!/usr/bin/env python3
"""
redis_service.py - 車行寶 Redis 快取服務
PYLIB: L3-redis-service
Version: v1.0.0
Created: 2026-02-03

功能：
1. Redis 連接管理
2. 快取裝飾器
3. 分散式鎖
4. 會話存儲
5. 速率限制
"""

import json
import time
import hashlib
import functools
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager
import threading

# ============================================================
# L0: 基礎常量
# ============================================================

VERSION = "1.0.0"
REDIS_URL = "redis://localhost:6379/0"
DEFAULT_TTL = 300  # 5 分鐘
DEFAULT_PREFIX = "cardeal:"

# 快取策略
CACHE_STRATEGIES = {
    "none": 0,       # 不快取
    "short": 60,     # 1 分鐘
    "medium": 300,   # 5 分鐘
    "long": 3600,    # 1 小時
    "day": 86400,    # 1 天
}

# ============================================================
# L1: 資料結構
# ============================================================

@dataclass
class CacheEntry:
    """快取項目"""
    key: str
    value: Any
    created_at: float
    ttl: int
    hits: int = 0
    
    @property
    def expires_at(self) -> float:
        return self.created_at + self.ttl
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

@dataclass
class CacheStats:
    """快取統計"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

@dataclass
class LockInfo:
    """鎖資訊"""
    key: str
    owner: str
    acquired_at: float
    ttl: int
    
    @property
    def expires_at(self) -> float:
        return self.acquired_at + self.ttl

# ============================================================
# L2: Redis 客戶端抽象
# ============================================================

class RedisClientBase:
    """Redis 客戶端基類（抽象）"""
    
    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError
    
    def set(self, key: str, value: str, ex: int = None) -> bool:
        raise NotImplementedError
    
    def delete(self, *keys: str) -> int:
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        raise NotImplementedError
    
    def expire(self, key: str, seconds: int) -> bool:
        raise NotImplementedError
    
    def incr(self, key: str) -> int:
        raise NotImplementedError
    
    def keys(self, pattern: str) -> List[str]:
        raise NotImplementedError
    
    def setnx(self, key: str, value: str) -> bool:
        raise NotImplementedError


class MemoryRedisClient(RedisClientBase):
    """記憶體 Redis 模擬（開發/測試用）"""
    
    def __init__(self):
        self._store: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
    
    def _cleanup_expired(self) -> None:
        """清理過期項目"""
        now = time.time()
        expired = [k for k, v in self._store.items() if v.is_expired]
        for k in expired:
            del self._store[k]
    
    def get(self, key: str) -> Optional[str]:
        with self._lock:
            self._cleanup_expired()
            entry = self._store.get(key)
            if entry and not entry.is_expired:
                entry.hits += 1
                return entry.value
            return None
    
    def set(self, key: str, value: str, ex: int = None) -> bool:
        with self._lock:
            ttl = ex or DEFAULT_TTL
            self._store[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl
            )
            return True
    
    def delete(self, *keys: str) -> int:
        with self._lock:
            count = 0
            for key in keys:
                if key in self._store:
                    del self._store[key]
                    count += 1
            return count
    
    def exists(self, key: str) -> bool:
        with self._lock:
            self._cleanup_expired()
            return key in self._store
    
    def expire(self, key: str, seconds: int) -> bool:
        with self._lock:
            if key in self._store:
                entry = self._store[key]
                self._store[key] = CacheEntry(
                    key=key,
                    value=entry.value,
                    created_at=time.time(),
                    ttl=seconds,
                    hits=entry.hits
                )
                return True
            return False
    
    def incr(self, key: str) -> int:
        with self._lock:
            entry = self._store.get(key)
            if entry:
                try:
                    value = int(entry.value) + 1
                except ValueError:
                    value = 1
            else:
                value = 1
            
            self._store[key] = CacheEntry(
                key=key,
                value=str(value),
                created_at=time.time(),
                ttl=DEFAULT_TTL
            )
            return value
    
    def keys(self, pattern: str) -> List[str]:
        import fnmatch
        with self._lock:
            self._cleanup_expired()
            return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]
    
    def setnx(self, key: str, value: str) -> bool:
        with self._lock:
            if key not in self._store or self._store[key].is_expired:
                self._store[key] = CacheEntry(
                    key=key,
                    value=value,
                    created_at=time.time(),
                    ttl=DEFAULT_TTL
                )
                return True
            return False


def get_redis_client(url: str = None) -> RedisClientBase:
    """獲取 Redis 客戶端"""
    try:
        import redis
        return redis.from_url(url or REDIS_URL)
    except ImportError:
        # 沒有 redis 套件，使用記憶體模擬
        return MemoryRedisClient()

# ============================================================
# L3: 業務服務
# ============================================================

class CacheService:
    """快取服務"""
    
    def __init__(self, client: RedisClientBase = None, prefix: str = DEFAULT_PREFIX):
        self.client = client or get_redis_client()
        self.prefix = prefix
        self.stats = CacheStats()
    
    def _make_key(self, key: str) -> str:
        """生成完整 key"""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """獲取快取"""
        full_key = self._make_key(key)
        value = self.client.get(full_key)
        
        if value is not None:
            self.stats.hits += 1
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        
        self.stats.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        """設置快取"""
        full_key = self._make_key(key)
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        
        result = self.client.set(full_key, serialized, ex=ttl)
        if result:
            self.stats.sets += 1
        return result
    
    def delete(self, key: str) -> bool:
        """刪除快取"""
        full_key = self._make_key(key)
        result = self.client.delete(full_key) > 0
        if result:
            self.stats.deletes += 1
        return result
    
    def clear_pattern(self, pattern: str) -> int:
        """清除符合模式的快取"""
        full_pattern = self._make_key(pattern)
        keys = self.client.keys(full_pattern)
        if keys:
            return self.client.delete(*keys)
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計"""
        return {
            'hits': self.stats.hits,
            'misses': self.stats.misses,
            'sets': self.stats.sets,
            'deletes': self.stats.deletes,
            'hit_rate': round(self.stats.hit_rate * 100, 2)
        }


class LockService:
    """分散式鎖服務"""
    
    def __init__(self, client: RedisClientBase = None, prefix: str = DEFAULT_PREFIX):
        self.client = client or get_redis_client()
        self.prefix = f"{prefix}lock:"
    
    def _make_key(self, name: str) -> str:
        return f"{self.prefix}{name}"
    
    @contextmanager
    def lock(self, name: str, ttl: int = 10, timeout: int = 5):
        """獲取鎖（上下文管理器）"""
        key = self._make_key(name)
        owner = f"{time.time()}:{id(self)}"
        acquired = False
        deadline = time.time() + timeout
        
        # 嘗試獲取鎖
        while time.time() < deadline:
            if self.client.setnx(key, owner):
                self.client.expire(key, ttl)
                acquired = True
                break
            time.sleep(0.1)
        
        if not acquired:
            raise TimeoutError(f"無法獲取鎖: {name}")
        
        try:
            yield
        finally:
            # 釋放鎖（確保是自己的鎖）
            if self.client.get(key) == owner:
                self.client.delete(key)


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, client: RedisClientBase = None, prefix: str = DEFAULT_PREFIX):
        self.client = client or get_redis_client()
        self.prefix = f"{prefix}rate:"
    
    def is_allowed(self, key: str, max_requests: int, window: int) -> bool:
        """檢查是否允許請求"""
        full_key = f"{self.prefix}{key}"
        current = self.client.incr(full_key)
        
        if current == 1:
            self.client.expire(full_key, window)
        
        return current <= max_requests
    
    def get_remaining(self, key: str, max_requests: int) -> int:
        """獲取剩餘配額"""
        full_key = f"{self.prefix}{key}"
        value = self.client.get(full_key)
        
        if value is None:
            return max_requests
        
        try:
            used = int(value)
            return max(0, max_requests - used)
        except ValueError:
            return max_requests

# ============================================================
# L4: 裝飾器與便捷函數
# ============================================================

# 全域服務實例
_cache_service: Optional[CacheService] = None
_lock_service: Optional[LockService] = None
_rate_limiter: Optional[RateLimiter] = None


def get_cache() -> CacheService:
    """獲取快取服務"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def get_lock_service() -> LockService:
    """獲取鎖服務"""
    global _lock_service
    if _lock_service is None:
        _lock_service = LockService()
    return _lock_service


def get_rate_limiter() -> RateLimiter:
    """獲取速率限制器"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def cached(ttl: int = DEFAULT_TTL, key_prefix: str = ""):
    """快取裝飾器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成快取 key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # 嘗試從快取獲取
            cache = get_cache()
            result = cache.get(cache_key)
            
            if result is not None:
                return result
            
            # 執行函數並快取
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        # 添加清除快取方法
        wrapper.clear_cache = lambda: get_cache().clear_pattern(f"{key_prefix}*")
        
        return wrapper
    return decorator


def rate_limited(max_requests: int = 60, window: int = 60, key_func: Callable = None):
    """速率限制裝飾器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成限制 key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = func.__name__
            
            limiter = get_rate_limiter()
            if not limiter.is_allowed(key, max_requests, window):
                raise Exception(f"Rate limit exceeded for {key}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def with_lock(name: str, ttl: int = 10, timeout: int = 5):
    """鎖裝飾器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_service = get_lock_service()
            with lock_service.lock(name, ttl, timeout):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# 📚 知識點
# -----------
# 1. 適配器模式：RedisClientBase 抽象實際實現
# 2. 記憶體模擬：沒有 Redis 時使用字典模擬
# 3. 分散式鎖：使用 SETNX 實現互斥
# 4. 速率限制：滑動窗口算法
# 5. 裝飾器模式：cached/rate_limited/with_lock
