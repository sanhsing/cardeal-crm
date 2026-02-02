"""
車行寶 CRM v5.1 - 排程任務管理器
北斗七星文創數位 × 織明

功能：定時任務、背景執行、任務佇列
"""
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

import time
import threading
import logging
from datetime import datetime, timedelta
from functools import wraps
import config

# ===== 任務定義 =====

class Task:
    """任務定義"""
    
    def __init__(self, name, func, interval_seconds, enabled=True):
        self.name = name
        self.func = func
        self.interval = interval_seconds
        self.enabled = enabled
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.error_count = 0
        self.last_error = None
        self.last_duration = 0
    
    def should_run(self):
        """檢查是否應該執行"""
        if not self.enabled:
            return False
        if self.next_run is None:
            return True
        return datetime.now() >= self.next_run
    
    def run(self):
        """執行任務"""
        start_time = time.time()
        try:
            self.func()
            self.run_count += 1
            self.last_error = None
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logging.error(f"Task {self.name} failed: {e}")
        finally:
            self.last_run = datetime.now()
            self.next_run = self.last_run + timedelta(seconds=self.interval)
            self.last_duration = (time.time() - start_time) * 1000
    
    def to_dict(self):
        """轉為字典"""
        return {
            'name': self.name,
            'interval_seconds': self.interval,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'last_duration_ms': round(self.last_duration, 2)
        }


# ===== 排程器 =====

class Scheduler:
    """排程器"""
    
    def __init__(self) -> None:
        self.tasks = {}
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
    
    def add_task(self, name, func, interval_seconds, enabled=True):
        """添加任務"""
        with self.lock:
            self.tasks[name] = Task(name, func, interval_seconds, enabled)
    
    def remove_task(self, name):
        """移除任務"""
        with self.lock:
            if name in self.tasks:
                del self.tasks[name]
    
    def enable_task(self, name):
        """啟用任務"""
        with self.lock:
            if name in self.tasks:
                self.tasks[name].enabled = True
    
    def disable_task(self, name):
        """停用任務"""
        with self.lock:
            if name in self.tasks:
                self.tasks[name].enabled = False
    
    def run_task_now(self, name):
        """立即執行任務"""
        with self.lock:
            if name in self.tasks:
                self.tasks[name].run()
                return True
        return False
    
    def start(self) -> None:
        """啟動排程器"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logging.info("Scheduler started")
    
    def stop(self):
        """停止排程器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logging.info("Scheduler stopped")
    
    def _run_loop(self):
        """執行迴圈"""
        while self.running:
            with self.lock:
                for task in self.tasks.values():
                    if task.should_run():
                        task.run()
            time.sleep(1)  # 每秒檢查一次
    
    def get_status(self):
        """取得排程器狀態"""
        with self.lock:
            return {
                'running': self.running,
                'tasks': [t.to_dict() for t in self.tasks.values()]
            }


# ===== 全域排程器 =====

scheduler = Scheduler()


def scheduled(interval_seconds, name=None):
    """排程裝飾器
    
    用法：
        @scheduled(60, name='cleanup')
        def cleanup_job():
            ...
    """
    def decorator(func):
        task_name = name or func.__name__
        scheduler.add_task(task_name, func, interval_seconds)
        return func
    return decorator


# ===== 預設任務 =====

def register_default_tasks():
    """註冊預設任務"""
    
    # Session 清理（每小時）
    @scheduled(3600, name='session_cleanup')
    def session_cleanup():
        from models import cleanup_sessions
        cleanup_sessions()
    
    # CSRF Token 清理（每30分鐘）
    @scheduled(1800, name='csrf_cleanup')
    def csrf_cleanup():
        from services.security_service import cleanup_csrf_tokens
        cleanup_csrf_tokens()
    
    # 快取清理（每5分鐘）
    @scheduled(300, name='cache_cleanup')
    def cache_cleanup():
        from services.cache_service import cache_cleanup
        count = cache_cleanup()
        if count > 0:
            logging.debug(f"Cleaned {count} expired cache items")
    
    # 備份（每天）
    if config.AUTO_BACKUP_ENABLED:
        @scheduled(86400, name='daily_backup')
        def daily_backup():
            from services.backup_service import auto_backup_with_notify
            # 只在凌晨2-4點執行
            hour = datetime.now().hour
            if 2 <= hour <= 4:
                auto_backup_with_notify()


# ===== 任務佇列（簡易版）=====

class TaskQueue:
    """簡易任務佇列"""
    
    def __init__(self, max_workers=2):
        self.queue = []
        self.lock = threading.Lock()
        self.workers = []
        self.running = False
        self.max_workers = max_workers
    
    def add(self, func, *args, **kwargs):
        """添加任務到佇列"""
        with self.lock:
            self.queue.append((func, args, kwargs))
    
    def start(self) -> None:
        """啟動工作執行緒"""
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def stop(self):
        """停止佇列"""
        self.running = False
    
    def _worker(self):
        """工作執行緒"""
        while self.running:
            task = None
            with self.lock:
                if self.queue:
                    task = self.queue.pop(0)
            
            if task:
                func, args, kwargs = task
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Task queue error: {e}")
            else:
                time.sleep(0.1)
    
    @property
    def pending_count(self):
        """待處理數量"""
        with self.lock:
            return len(self.queue)


# 全域任務佇列
task_queue = TaskQueue()


def enqueue(func, *args, **kwargs):
    """將任務加入佇列"""
    task_queue.add(func, *args, **kwargs)


# 📚 知識點
# -----------
# 1. 排程器設計：
#    - 定時檢查任務是否應執行
#    - 記錄執行歷史和錯誤
#    - 支援動態啟用/停用
#
# 2. threading.Lock：
#    - 確保執行緒安全
#    - with self.lock: 自動取得/釋放
#    - 防止競爭條件
#
# 3. daemon=True：
#    - 守護執行緒
#    - 主程式結束時自動終止
#    - 不會阻止程式退出
#
# 4. 裝飾器工廠：
#    - @scheduled(60) 返回裝飾器
#    - 可帶參數的裝飾器
#
# 5. 任務佇列：
#    - 生產者-消費者模式
#    - 多工作執行緒並行處理
#    - 非同步執行長時間任務
