"""
車行寶 CRM v5.1 - 上傳處理器
北斗七星文創數位 × 織明

功能：處理檔案上傳（圖片、文件）
"""
import json
import re
from .base import BaseHandler
from services import image_service


def handle_upload(handler, session) -> None:
    """處理圖片上傳"""
    tenant_code = session['data']['tenant_code']
    
    # 取得請求資料
    content_type = handler.headers.get('Content-Type', '')
    
    # JSON 格式（Base64）
    if 'application/json' in content_type:
        data = BaseHandler.get_json_body(handler)
        if not data or 'image' not in data:
            return BaseHandler.send_json(handler, 
                {'success': False, 'error': '缺少圖片資料'}, 400)
        
        category = data.get('category', 'vehicles')
        result = image_service.save_base64_image(data['image'], tenant_code, category)
        
        return BaseHandler.send_json(handler, result)
    
    # multipart/form-data 格式
    if 'multipart/form-data' in content_type:
        result = handle_multipart_upload(handler, tenant_code)
        return BaseHandler.send_json(handler, result)
    
    BaseHandler.send_json(handler, 
        {'success': False, 'error': '不支援的上傳格式'}, 400)


def handle_multipart_upload(handler, tenant_code: str) -> dict:
    """處理 multipart/form-data 上傳"""
    content_type = handler.headers.get('Content-Type', '')
    
    # 取得 boundary
    match = re.search(r'boundary=(.+)', content_type)
    if not match:
        return {'success': False, 'error': '無效的 multipart 格式'}
    
    boundary = match.group(1).encode()
    if boundary.startswith(b'"') and boundary.endswith(b'"'):
        boundary = boundary[1:-1]
    
    # 讀取 body
    body = BaseHandler.get_body(handler)
    
    # 解析 multipart
    parts = body.split(b'--' + boundary)
    
    results = []
    category = 'vehicles'
    
    for part in parts:
        if not part or part == b'--\r\n' or part == b'--':
            continue
        
        # 分離 header 和 content
        if b'\r\n\r\n' not in part:
            continue
        
        header_data, content = part.split(b'\r\n\r\n', 1)
        
        # 移除結尾的 \r\n
        if content.endswith(b'\r\n'):
            content = content[:-2]
        
        headers = header_data.decode('utf-8', errors='ignore')
        
        # 檢查是否為檔案
        name_match = re.search(r'name="([^"]+)"', headers)
        filename_match = re.search(r'filename="([^"]+)"', headers)
        
        if name_match:
            field_name = name_match.group(1)
            
            if field_name == 'category':
                category = content.decode('utf-8', errors='ignore').strip()
            elif filename_match and field_name in ('file', 'image', 'images[]'):
                filename = filename_match.group(1)
                result = image_service.save_image_with_resize(
                    content, tenant_code, category, filename
                )
                if result['success']:
                    results.append(result)
    
    if not results:
        return {'success': False, 'error': '沒有上傳任何檔案'}
    
    if len(results) == 1:
        return results[0]
    
    return {
        'success': True,
        'count': len(results),
        'files': results
    }


def handle_vehicle_image_upload(handler, session, vehicle_id: int) -> None:
    """上傳車輛圖片"""
    from models import get_connection
    
    db_path = session['data']['db_path']
    tenant_code = session['data']['tenant_code']
    
    # 檢查車輛是否存在
    conn = get_connection(db_path)
    c = conn.cursor()
    c.execute('SELECT id FROM vehicles WHERE id = ?', (vehicle_id,))
    if not c.fetchone():
        conn.close()
        return BaseHandler.send_json(handler, 
            {'success': False, 'error': '車輛不存在'}, 404)
    conn.close()
    
    # 取得請求資料
    content_type = handler.headers.get('Content-Type', '')
    
    if 'application/json' in content_type:
        data = BaseHandler.get_json_body(handler)
        if not data or 'image' not in data:
            return BaseHandler.send_json(handler, 
                {'success': False, 'error': '缺少圖片資料'}, 400)
        
        is_primary = data.get('is_primary', False)
        
        # 儲存圖片
        result = image_service.save_base64_image(
            data['image'], tenant_code, 'vehicles'
        )
        
        if not result['success']:
            return BaseHandler.send_json(handler, result)
        
        # 關聯到車輛
        db_result = image_service.add_vehicle_image(
            db_path, vehicle_id, result, is_primary
        )
        
        result.update(db_result)
        return BaseHandler.send_json(handler, result)
    
    elif 'multipart/form-data' in content_type:
        result = handle_multipart_upload(handler, tenant_code)
        
        if result['success']:
            # 關聯到車輛
            if 'files' in result:
                for file_data in result['files']:
                    image_service.add_vehicle_image(
                        db_path, vehicle_id, file_data, False
                    )
            else:
                image_service.add_vehicle_image(
                    db_path, vehicle_id, result, True
                )
        
        return BaseHandler.send_json(handler, result)
    
    BaseHandler.send_json(handler, 
        {'success': False, 'error': '不支援的上傳格式'}, 400)


def get_vehicle_images(handler, session, vehicle_id: int) -> None:
    """取得車輛圖片列表"""
    db_path = session['data']['db_path']
    
    images = image_service.get_vehicle_images(db_path, vehicle_id)
    
    BaseHandler.send_json(handler, {
        'success': True,
        'images': images
    })


def delete_vehicle_image(handler, session, image_id: int) -> None:
    """刪除車輛圖片"""
    db_path = session['data']['db_path']
    
    result = image_service.delete_vehicle_image(db_path, image_id)
    
    BaseHandler.send_json(handler, result)


# 📚 知識點
# -----------
# 1. multipart/form-data：
#    - 瀏覽器上傳檔案的標準格式
#    - boundary 分隔各個欄位
#    - 每個部分有 headers + content
#
# 2. boundary 解析：
#    - Content-Type: multipart/form-data; boundary=----xxx
#    - 用 boundary 切割 body
#    - 注意 -- 前綴
#
# 3. 二進位處理：
#    - body 是 bytes
#    - split() 分割
#    - decode() 轉文字（headers）
#
# 4. 檔案上傳安全：
#    - 檢查 Content-Type
#    - 檢查 Magic Bytes
#    - 限制檔案大小
#    - 產生隨機檔名
