"""
車行寶 CRM v5.0 - 備份服務模組
北斗七星文創數位 × 織明
"""
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

import os
import shutil
import glob
from datetime import datetime, timedelta
import config
from models import get_connection
from services import telegram_service

def ensure_backup_dir() -> str:
    """確保備份目錄存在"""
    os.makedirs(config.BACKUP_DIR, exist_ok=True)

def backup_database(db_path: str, prefix: str = '') -> str:
    """備份單個資料庫"""
    ensure_backup_dir()
    
    if not os.path.exists(db_path):
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_name = os.path.basename(db_path).replace('.db', '')
    backup_name = f"{prefix}{db_name}_{timestamp}.db"
    backup_path = os.path.join(config.BACKUP_DIR, backup_name)
    
    try:
        shutil.copy2(db_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"Backup error: {e}")
        return None

def backup_all() -> dict:
    """備份所有資料庫"""
    ensure_backup_dir()
    results = {'success': [], 'failed': []}
    
    # 備份主資料庫
    if backup_database(config.MASTER_DB, 'master_'):
        results['success'].append('master.db')
    else:
        results['failed'].append('master.db')
    
    # 備份所有租戶資料庫
    conn = get_connection(config.MASTER_DB)
    c = conn.cursor()
    c.execute('SELECT id, code, db_path FROM tenants WHERE status = "active"')
    tenants = c.fetchall()
    conn.close()
    
    for tenant in tenants:
        if backup_database(tenant['db_path'], f"tenant_{tenant['code']}_"):
            results['success'].append(f"tenant_{tenant['code']}.db")
        else:
            results['failed'].append(f"tenant_{tenant['code']}.db")
    
    return results

def auto_backup_with_notify() -> bool:
    """自動備份並通知"""
    if not config.AUTO_BACKUP_ENABLED:
        return False
    
    results = backup_all()
    
    # 清理舊備份
    cleaned = cleanup_old_backups()
    
    # 發送通知
    if config.BACKUP_NOTIFY:
        success = len(results['failed']) == 0
        details = f"成功：{len(results['success'])} 個\n失敗：{len(results['failed'])} 個\n清理：{cleaned} 個舊備份"
        telegram_service.notify_backup(
            len(results['success']) + len(results['failed']),
            success,
            details
        )
    
    return len(results['failed']) == 0

def cleanup_old_backups(days: int = None) -> int:
    """清理舊備份"""
    if days is None:
        days = config.BACKUP_RETENTION_DAYS
    
    cutoff = datetime.now() - timedelta(days=days)
    count = 0
    
    backup_files = glob.glob(os.path.join(config.BACKUP_DIR, '*.db'))
    
    for backup_file in backup_files:
        try:
            file_time = datetime.fromtimestamp(os.path.getmtime(backup_file))
            if file_time < cutoff:
                os.remove(backup_file)
                count += 1
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    return count

def get_backup_list() -> list:
    """取得備份列表"""
    ensure_backup_dir()
    
    backups = []
    backup_files = glob.glob(os.path.join(config.BACKUP_DIR, '*.db'))
    
    for backup_file in sorted(backup_files, reverse=True):
        stat = os.stat(backup_file)
        backups.append({
            'name': os.path.basename(backup_file),
            'path': backup_file,
            'size': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    
    return backups

def restore_backup(backup_path: str, target_path: str) -> bool:
    """還原備份"""
    try:
        if not os.path.exists(backup_path):
            return False
        
        # 先備份現有的
        if os.path.exists(target_path):
            backup_database(target_path, 'pre_restore_')
        
        shutil.copy2(backup_path, target_path)
        return True
    except Exception as e:
        print(f"Restore error: {e}")
        return False
