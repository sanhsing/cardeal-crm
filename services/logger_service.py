"""
車行寶 CRM v5.1 - 日誌服務模組
北斗七星文創數位 × 織明

功能：結構化日誌、多輸出目標、日誌輪替
"""
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import config

# ===== 日誌格式化 =====

class JsonFormatter(logging.Formatter):
    """JSON 格式化器（便於日誌分析）"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 添加額外欄位
        if hasattr(record, 'tenant_id'):
            log_data['tenant_id'] = record.tenant_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
        
        # 添加異常資訊
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 綠色
        'WARNING': '\033[33m',  # 黃色
        'ERROR': '\033[31m',    # 紅色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# ===== 日誌設定 =====

def setup_logging(
    name='cardeal',
    level=logging.INFO,
    log_dir='logs',
    console=True,
    file=True,
    json_format=False
):
    """設定日誌系統
    
    Args:
        name: 日誌名稱
        level: 日誌等級
        log_dir: 日誌目錄
        console: 是否輸出到控制台
        file: 是否輸出到檔案
        json_format: 是否使用 JSON 格式
    
    Returns:
        Logger 實例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []  # 清除現有 handlers
    
    # 控制台輸出
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        if json_format:
            console_handler.setFormatter(JsonFormatter())
        else:
            format_str = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            if sys.stdout.isatty():
                console_handler.setFormatter(ColoredFormatter(format_str))
            else:
                console_handler.setFormatter(logging.Formatter(format_str))
        
        logger.addHandler(console_handler)
    
    # 檔案輸出
    if file:
        os.makedirs(log_dir, exist_ok=True)
        
        # 一般日誌（按大小輪替）
        log_file = os.path.join(log_dir, f'{name}.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        
        if json_format:
            file_handler.setFormatter(JsonFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            ))
        
        logger.addHandler(file_handler)
        
        # 錯誤日誌（單獨檔案）
        error_file = os.path.join(log_dir, f'{name}_error.log')
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JsonFormatter())
        logger.addHandler(error_handler)
    
    return logger


# ===== 全域日誌實例 =====

_loggers = {}

def get_logger(name: str = 'cardeal') -> Any:
    """取得日誌實例"""
    if name not in _loggers:
        _loggers[name] = setup_logging(
            name=name,
            level=getattr(logging, config.LOG_LEVEL, logging.INFO),
            console=True,
            file=not config.DEBUG,
            json_format=not config.DEBUG
        )
    return _loggers[name]


# ===== 便捷函數 =====

def log_info(message: str, **kwargs) -> None:
    """記錄 INFO 日誌"""
    logger = get_logger()
    logger.info(message, extra=kwargs)


def log_warning(message: str, **kwargs) -> None:
    """記錄 WARNING 日誌"""
    logger = get_logger()
    logger.warning(message, extra=kwargs)


def log_error(message: str, exc_info: Any = None, **kwargs) -> None:
    """記錄 ERROR 日誌"""
    logger = get_logger()
    logger.error(message, exc_info=exc_info, extra=kwargs)


def log_debug(message: str, **kwargs) -> None:
    """記錄 DEBUG 日誌"""
    logger = get_logger()
    logger.debug(message, extra=kwargs)


# ===== 請求日誌 =====

class RequestLogger:
    """請求日誌記錄器"""
    
    def __init__(self, logger_name='cardeal.request'):
        self.logger = get_logger(logger_name)
    
    def log_request(self, method, path, status_code, duration_ms, 
                    client_ip=None, user_id=None, tenant_id=None):
        """記錄 HTTP 請求"""
        self.logger.info(
            f'{method} {path} {status_code} {duration_ms:.1f}ms',
            extra={
                'method': method,
                'path': path,
                'status_code': status_code,
                'duration_ms': duration_ms,
                'client_ip': client_ip,
                'user_id': user_id,
                'tenant_id': tenant_id,
            }
        )


# ===== 審計日誌 =====

class AuditLogger:
    """審計日誌記錄器（記錄重要操作）"""
    
    def __init__(self, logger_name='cardeal.audit'):
        self.logger = get_logger(logger_name)
    
    def log_action(self, action, target_type, target_id, 
                   user_id, tenant_id, details=None):
        """記錄使用者操作"""
        self.logger.info(
            f'[AUDIT] {action} {target_type}:{target_id}',
            extra={
                'action': action,
                'target_type': target_type,
                'target_id': target_id,
                'user_id': user_id,
                'tenant_id': tenant_id,
                'details': details,
            }
        )
    
    def log_login(self, user_id, tenant_id, client_ip, success=True):
        """記錄登入"""
        status = 'success' if success else 'failed'
        self.logger.info(
            f'[AUDIT] login_{status} user:{user_id}',
            extra={
                'action': f'login_{status}',
                'user_id': user_id,
                'tenant_id': tenant_id,
                'client_ip': client_ip,
            }
        )


# ===== 效能日誌 =====

class PerformanceLogger:
    """效能日誌記錄器"""
    
    def __init__(self, logger_name='cardeal.perf'):
        self.logger = get_logger(logger_name)
    
    def log_slow_query(self, sql, duration_ms, threshold=100):
        """記錄慢查詢"""
        if duration_ms > threshold:
            self.logger.warning(
                f'[SLOW_QUERY] {duration_ms:.1f}ms: {sql[:100]}...',
                extra={
                    'sql': sql[:500],
                    'duration_ms': duration_ms,
                }
            )
    
    def log_slow_request(self, path, duration_ms, threshold=1000):
        """記錄慢請求"""
        if duration_ms > threshold:
            self.logger.warning(
                f'[SLOW_REQUEST] {path} took {duration_ms:.1f}ms',
                extra={
                    'path': path,
                    'duration_ms': duration_ms,
                }
            )


# 📚 知識點
# -----------
# 1. logging 模組架構：
#    - Logger：日誌記錄器
#    - Handler：輸出目標（控制台、檔案等）
#    - Formatter：格式化器
#
# 2. 日誌輪替：
#    - RotatingFileHandler：按大小輪替
#    - TimedRotatingFileHandler：按時間輪替
#    - backupCount：保留幾個舊檔案
#
# 3. 日誌等級：
#    - DEBUG < INFO < WARNING < ERROR < CRITICAL
#    - 設定等級後，低於該等級的不會輸出
#
# 4. ANSI 顏色碼：
#    - \033[32m：綠色
#    - \033[0m：重設
#    - 只在終端機有效
#
# 5. extra 參數：
#    - 傳遞額外欄位給 Formatter
#    - 用於結構化日誌
#
# 6. 審計日誌：
#    - 記錄「誰」在「何時」做了「什麼」
#    - 用於安全審計、問題追蹤
