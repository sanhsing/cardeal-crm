"""
車行寶 CRM v5.1 - 圖片服務模組
北斗七星文創數位 × 織明

功能：圖片上傳、壓縮、存儲、縮圖
"""
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

import os
import io
import base64
import hashlib
import uuid
from datetime import datetime
import config

# ===== 配置 =====

IMAGE_CONFIG = {
    'max_size': 10 * 1024 * 1024,  # 10MB
    'allowed_types': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    'max_width': 1920,
    'max_height': 1080,
    'thumb_size': (300, 200),
    'quality': 85,
    'storage_dir': os.path.join(config.DATA_DIR, 'uploads'),
}


# ===== 儲存路徑 =====

def get_storage_path(tenant_code, category='vehicles') -> Any:
    """取得儲存路徑
    
    結構：data/uploads/{tenant_code}/{category}/{year}/{month}/
    """
    now = datetime.now()
    path = os.path.join(
        IMAGE_CONFIG['storage_dir'],
        tenant_code,
        category,
        str(now.year),
        f'{now.month:02d}'
    )
    os.makedirs(path, exist_ok=True)
    return path


def generate_filename(original_name, prefix=''):
    """產生唯一檔名"""
    ext = os.path.splitext(original_name)[1].lower() or '.jpg'
    unique_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if prefix:
        return f'{prefix}_{timestamp}_{unique_id}{ext}'
    return f'{timestamp}_{unique_id}{ext}'


# ===== 圖片處理（無 PIL 版本）=====

def save_image_simple(data: bytes, tenant_code: str, category: str = 'vehicles', 
                      original_name: str = 'image.jpg') -> dict:
    """簡單儲存圖片（不壓縮）
    
    Args:
        data: 圖片二進位資料
        tenant_code: 租戶代碼
        category: 分類（vehicles/customers/documents）
        original_name: 原始檔名
    
    Returns:
        儲存結果
    """
    # 檢查大小
    if len(data) > IMAGE_CONFIG['max_size']:
        return {
            'success': False,
            'error': f'圖片過大，最大 {IMAGE_CONFIG["max_size"] // 1024 // 1024}MB'
        }
    
    # 檢查類型（簡單檢查 magic bytes）
    file_type = detect_image_type(data)
    if not file_type:
        return {'success': False, 'error': '不支援的圖片格式'}
    
    # 產生路徑和檔名
    storage_path = get_storage_path(tenant_code, category)
    filename = generate_filename(original_name)
    filepath = os.path.join(storage_path, filename)
    
    # 儲存
    with open(filepath, 'wb') as f:
        f.write(data)
    
    # 計算相對路徑
    relative_path = os.path.relpath(filepath, config.DATA_DIR)
    
    # 計算雜湊（用於去重）
    file_hash = hashlib.md5(data).hexdigest()
    
    return {
        'success': True,
        'filename': filename,
        'path': relative_path,
        'full_path': filepath,
        'size': len(data),
        'type': file_type,
        'hash': file_hash,
        'url': f'/uploads/{relative_path}'
    }


def detect_image_type(data: bytes) -> str:
    """檢測圖片類型（通過 magic bytes）"""
    if len(data) < 8:
        return None
    
    # JPEG: FF D8 FF
    if data[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    
    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    
    # GIF: GIF87a or GIF89a
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return 'image/gif'
    
    # WebP: RIFF....WEBP
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    
    return None


# ===== 圖片處理（PIL 版本）=====

def save_image_with_resize(data: bytes, tenant_code: str, category: str = 'vehicles',
                           original_name: str = 'image.jpg', 
                           max_width: int = None, max_height: int = None) -> dict:
    """儲存並調整圖片大小（需要 PIL）
    
    如果 PIL 不可用，回退到簡單儲存
    """
    try:
        from PIL import Image
    except ImportError:
        # PIL 不可用，使用簡單版本
        return save_image_simple(data, tenant_code, category, original_name)
    
    # 檢查大小
    if len(data) > IMAGE_CONFIG['max_size']:
        return {
            'success': False,
            'error': f'圖片過大，最大 {IMAGE_CONFIG["max_size"] // 1024 // 1024}MB'
        }
    
    try:
        # 讀取圖片
        img = Image.open(io.BytesIO(data))
        
        # 轉換 RGBA → RGB（如果是 PNG 轉 JPEG）
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 調整大小
        max_w = max_width or IMAGE_CONFIG['max_width']
        max_h = max_height or IMAGE_CONFIG['max_height']
        
        if img.width > max_w or img.height > max_h:
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        
        # 產生路徑和檔名
        storage_path = get_storage_path(tenant_code, category)
        filename = generate_filename(original_name, prefix='')
        filepath = os.path.join(storage_path, filename)
        
        # 儲存
        img.save(filepath, 'JPEG', quality=IMAGE_CONFIG['quality'], optimize=True)
        
        # 取得檔案資訊
        file_size = os.path.getsize(filepath)
        relative_path = os.path.relpath(filepath, config.DATA_DIR)
        
        return {
            'success': True,
            'filename': filename,
            'path': relative_path,
            'full_path': filepath,
            'size': file_size,
            'width': img.width,
            'height': img.height,
            'type': 'image/jpeg',
            'url': f'/uploads/{relative_path}'
        }
        
    except Exception as e:
        return {'success': False, 'error': f'圖片處理失敗：{str(e)}'}


def create_thumbnail(source_path: str, thumb_size: tuple = None) -> dict:
    """建立縮圖（需要 PIL）"""
    try:
        from PIL import Image
    except ImportError:
        return {'success': False, 'error': 'PIL 未安裝'}
    
    if not os.path.exists(source_path):
        return {'success': False, 'error': '來源圖片不存在'}
    
    size = thumb_size or IMAGE_CONFIG['thumb_size']
    
    try:
        img = Image.open(source_path)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # 縮圖檔名
        dir_path = os.path.dirname(source_path)
        filename = os.path.basename(source_path)
        name, ext = os.path.splitext(filename)
        thumb_filename = f'{name}_thumb{ext}'
        thumb_path = os.path.join(dir_path, thumb_filename)
        
        img.save(thumb_path, 'JPEG', quality=80)
        
        return {
            'success': True,
            'filename': thumb_filename,
            'path': thumb_path,
            'width': img.width,
            'height': img.height
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ===== Base64 處理 =====

def save_base64_image(base64_data: str, tenant_code: str, 
                      category: str = 'vehicles') -> dict:
    """儲存 Base64 編碼的圖片
    
    Args:
        base64_data: Base64 字串（可含 data:image/xxx;base64, 前綴）
        tenant_code: 租戶代碼
        category: 分類
    """
    # 移除 data URL 前綴
    if ',' in base64_data:
        header, base64_data = base64_data.split(',', 1)
        # 從 header 取得格式：data:image/jpeg;base64
        if 'png' in header:
            ext = '.png'
        elif 'gif' in header:
            ext = '.gif'
        elif 'webp' in header:
            ext = '.webp'
        else:
            ext = '.jpg'
    else:
        ext = '.jpg'
    
    try:
        data = base64.b64decode(base64_data)
    except Exception as e:
        return {'success': False, 'error': 'Base64 解碼失敗'}
    
    return save_image_with_resize(data, tenant_code, category, f'upload{ext}')


# ===== 車輛圖片管理 =====

def get_vehicle_images(db_path: str, vehicle_id: int) -> list:
    """取得車輛的所有圖片"""
    from models import get_connection
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    c.execute('''SELECT id, filename, path, is_primary, sort_order, created_at
                 FROM vehicle_images
                 WHERE vehicle_id = ?
                 ORDER BY is_primary DESC, sort_order ASC''',
              (vehicle_id,))
    
    images = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return images


def add_vehicle_image(db_path: str, vehicle_id: int, image_data: dict, 
                      is_primary: bool = False) -> dict:
    """新增車輛圖片"""
    from models import get_connection
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 如果設為主圖，先取消其他主圖
    if is_primary:
        c.execute('UPDATE vehicle_images SET is_primary = 0 WHERE vehicle_id = ?',
                  (vehicle_id,))
    
    # 取得排序順序
    c.execute('SELECT MAX(sort_order) FROM vehicle_images WHERE vehicle_id = ?',
              (vehicle_id,))
    max_order = c.fetchone()[0] or 0
    
    c.execute('''INSERT INTO vehicle_images 
                 (vehicle_id, filename, path, is_primary, sort_order)
                 VALUES (?, ?, ?, ?, ?)''',
              (vehicle_id, image_data['filename'], image_data['path'],
               1 if is_primary else 0, max_order + 1))
    
    image_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {'success': True, 'id': image_id}


def delete_vehicle_image(db_path: str, image_id: int) -> dict:
    """刪除車輛圖片"""
    from models import get_connection
    
    conn = get_connection(db_path)
    c = conn.cursor()
    
    # 取得圖片路徑
    c.execute('SELECT path FROM vehicle_images WHERE id = ?', (image_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return {'success': False, 'error': '圖片不存在'}
    
    # 刪除資料庫記錄
    c.execute('DELETE FROM vehicle_images WHERE id = ?', (image_id,))
    conn.commit()
    conn.close()
    
    # 刪除檔案（選擇性）
    file_path = os.path.join(config.DATA_DIR, row['path'])
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except:
            pass  # 忽略刪除失敗
    
    return {'success': True}


# 📚 知識點
# -----------
# 1. Magic Bytes（檔案簽名）：
#    - 檔案開頭的特殊位元組
#    - JPEG: FF D8 FF
#    - PNG: 89 50 4E 47
#    - 用於識別真實檔案類型，比副檔名更可靠
#
# 2. PIL (Pillow)：
#    - Python 圖片處理庫
#    - thumbnail()：等比例縮放
#    - Image.Resampling.LANCZOS：高品質縮放演算法
#
# 3. Base64 編碼：
#    - 二進位轉文字（用於 JSON/HTML）
#    - 約增加 33% 大小
#    - data:image/jpeg;base64,{data}
#
# 4. 縮圖策略：
#    - 原圖存儲，縮圖顯示
#    - 減少流量，加快載入
#    - _thumb 後綴區分
#
# 5. uuid.uuid4()：
#    - 產生隨機唯一識別碼
#    - 避免檔名衝突
#    - .hex[:8] 取前8字元
