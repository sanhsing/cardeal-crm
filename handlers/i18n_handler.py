"""
車行寶 CRM v5.2 - 國際化 Handler
PYLIB: L4-i18n-handler
Version: v1.0.0

API 端點：
- GET /api/i18n/locales - 可用語言列表
- GET /api/i18n/translations - 獲取翻譯
- POST /api/i18n/locale - 設置語言
"""
from typing import Dict, Any, Optional
from handlers.base import BaseHandler
from services.i18n_service import get_i18n, t, set_locale, get_locale


class I18nHandler(BaseHandler):
    """國際化 Handler"""
    
    def handle_request(
        self, 
        method: str, 
        path: str, 
        params: Optional[Dict] = None,
        session: Any = None
    ) -> Dict[str, Any]:
        """處理請求"""
        params = params or {}
        
        # GET /api/i18n/locales
        if path == '/api/i18n/locales' and method == 'GET':
            return self._get_locales()
        
        # GET /api/i18n/translations
        if path == '/api/i18n/translations' and method == 'GET':
            return self._get_translations(params)
        
        # POST /api/i18n/locale
        if path == '/api/i18n/locale' and method == 'POST':
            return self._set_locale(params)
        
        # GET /api/i18n/t
        if path == '/api/i18n/t' and method == 'GET':
            return self._translate(params)
        
        return self.error_response(404, 'Not Found')
    
    def _get_locales(self) -> Dict[str, Any]:
        """獲取可用語言"""
        i18n = get_i18n()
        return self.success_response({
            'current': get_locale(),
            'available': i18n.get_available_locales()
        })
    
    def _get_translations(self, params: Dict) -> Dict[str, Any]:
        """獲取翻譯"""
        locale = params.get('locale')
        namespace = params.get('namespace')
        
        i18n = get_i18n()
        translations = i18n.get_translations(locale, namespace)
        
        return self.success_response({
            'locale': locale or get_locale(),
            'translations': translations
        })
    
    def _set_locale(self, params: Dict) -> Dict[str, Any]:
        """設置語言"""
        locale = params.get('locale')
        if not locale:
            return self.error_response(400, '缺少 locale 參數')
        
        success = set_locale(locale)
        if success:
            return self.success_response({
                'locale': locale,
                'message': t('common.success')
            })
        else:
            return self.error_response(400, f'不支援的語言: {locale}')
    
    def _translate(self, params: Dict) -> Dict[str, Any]:
        """翻譯單個鍵值"""
        key = params.get('key')
        if not key:
            return self.error_response(400, '缺少 key 參數')
        
        locale = params.get('locale')
        result = t(key, locale=locale)
        
        return self.success_response({
            'key': key,
            'value': result,
            'locale': locale or get_locale()
        })


def register_routes(router: Any) -> None:
    """註冊路由"""
    handler = I18nHandler()
    
    routes = [
        ('GET', '/api/i18n/locales'),
        ('GET', '/api/i18n/translations'),
        ('POST', '/api/i18n/locale'),
        ('GET', '/api/i18n/t'),
    ]
    
    for method, path in routes:
        router.add_route(method, path, handler.handle_request)
