#!/usr/bin/env python3
"""
i18n_service.py - 車行寶國際化服務
PYLIB: L2-i18n-service
Version: v1.0.0
Created: 2026-02-03

功能：
1. 多語言字串管理
2. 動態語言切換
3. 參數化翻譯
4. 缺失翻譯回退
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from functools import lru_cache

# ============================================================
# L0: 基礎常量
# ============================================================

VERSION = "1.0.0"
DEFAULT_LOCALE = "zh_TW"
FALLBACK_LOCALE = "en_US"
LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")

SUPPORTED_LOCALES = {
    "zh_TW": "繁體中文",
    "zh_CN": "简体中文",
    "en_US": "English",
    "ja_JP": "日本語",
}

# ============================================================
# L1: 資料結構
# ============================================================

@dataclass
class Translation:
    """翻譯項目"""
    key: str
    value: str
    locale: str
    namespace: str = "common"

@dataclass
class LocaleInfo:
    """語言資訊"""
    code: str
    name: str
    native_name: str
    direction: str = "ltr"  # ltr or rtl
    loaded: bool = False

@dataclass
class I18nContext:
    """國際化上下文"""
    current_locale: str = DEFAULT_LOCALE
    fallback_locale: str = FALLBACK_LOCALE
    loaded_locales: List[str] = field(default_factory=list)

# ============================================================
# L2: 核心邏輯
# ============================================================

class TranslationLoader:
    """翻譯載入器"""
    
    def __init__(self, locales_dir: str = LOCALES_DIR):
        self.locales_dir = Path(locales_dir)
        self._cache: Dict[str, Dict] = {}
    
    def load(self, locale: str) -> Dict[str, Any]:
        """載入翻譯檔"""
        if locale in self._cache:
            return self._cache[locale]
        
        filepath = self.locales_dir / f"{locale}.json"
        
        if not filepath.exists():
            # 嘗試簡化的語言代碼
            simple_code = locale.split('_')[0]
            for f in self.locales_dir.glob(f"{simple_code}*.json"):
                filepath = f
                break
        
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._cache[locale] = json.load(f)
                return self._cache[locale]
            except json.JSONDecodeError:
                pass
        
        return {}
    
    def get_available_locales(self) -> List[str]:
        """獲取可用語言列表"""
        locales = []
        if self.locales_dir.exists():
            for f in self.locales_dir.glob("*.json"):
                locales.append(f.stem)
        return sorted(locales)
    
    def clear_cache(self) -> None:
        """清除快取"""
        self._cache.clear()


class TranslationResolver:
    """翻譯解析器"""
    
    def __init__(self, translations: Dict[str, Any]):
        self.translations = translations
    
    def resolve(self, key: str, default: str = None) -> Optional[str]:
        """解析翻譯鍵值
        
        支援點號分隔的路徑，如：auth.login_success
        """
        parts = key.split('.')
        current = self.translations
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        return str(current) if current else default
    
    def interpolate(self, text: str, params: Dict[str, Any]) -> str:
        """參數插值
        
        支援 {param} 格式的佔位符
        """
        if not params:
            return text
        
        def replace(match):
            key = match.group(1)
            return str(params.get(key, match.group(0)))
        
        return re.sub(r'\{(\w+)\}', replace, text)

# ============================================================
# L3: 業務處理
# ============================================================

class I18nService:
    """國際化服務"""
    
    def __init__(self, locales_dir: str = LOCALES_DIR):
        self.loader = TranslationLoader(locales_dir)
        self.context = I18nContext()
        self._resolvers: Dict[str, TranslationResolver] = {}
        
        # 預載入預設語言
        self._ensure_loaded(DEFAULT_LOCALE)
        self._ensure_loaded(FALLBACK_LOCALE)
    
    def _ensure_loaded(self, locale: str) -> None:
        """確保語言已載入"""
        if locale not in self._resolvers:
            translations = self.loader.load(locale)
            self._resolvers[locale] = TranslationResolver(translations)
            if locale not in self.context.loaded_locales:
                self.context.loaded_locales.append(locale)
    
    def set_locale(self, locale: str) -> bool:
        """設置當前語言"""
        if locale in SUPPORTED_LOCALES or self.loader.load(locale):
            self._ensure_loaded(locale)
            self.context.current_locale = locale
            return True
        return False
    
    def get_locale(self) -> str:
        """獲取當前語言"""
        return self.context.current_locale
    
    def t(self, key: str, params: Dict[str, Any] = None, locale: str = None) -> str:
        """翻譯函數
        
        Args:
            key: 翻譯鍵值，如 'auth.login_success'
            params: 插值參數
            locale: 指定語言（可選）
        
        Returns:
            翻譯後的字串
        """
        target_locale = locale or self.context.current_locale
        self._ensure_loaded(target_locale)
        
        resolver = self._resolvers.get(target_locale)
        result = resolver.resolve(key) if resolver else None
        
        # 回退機制
        if result is None and target_locale != self.context.fallback_locale:
            fallback_resolver = self._resolvers.get(self.context.fallback_locale)
            result = fallback_resolver.resolve(key) if fallback_resolver else None
        
        # 最終回退到 key
        if result is None:
            result = key
        
        # 參數插值
        if params:
            result = TranslationResolver({}).interpolate(result, params)
        
        return result
    
    def get_translations(self, locale: str = None, namespace: str = None) -> Dict[str, Any]:
        """獲取翻譯字典"""
        target_locale = locale or self.context.current_locale
        self._ensure_loaded(target_locale)
        
        translations = self.loader.load(target_locale)
        
        if namespace and namespace in translations:
            return translations[namespace]
        
        return translations
    
    def get_available_locales(self) -> Dict[str, str]:
        """獲取可用語言"""
        available = {}
        for code in self.loader.get_available_locales():
            available[code] = SUPPORTED_LOCALES.get(code, code)
        return available
    
    def add_translations(self, locale: str, translations: Dict[str, Any]) -> None:
        """動態添加翻譯"""
        self._ensure_loaded(locale)
        existing = self.loader.load(locale)
        
        # 深度合併
        def deep_merge(base, updates):
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(existing, translations)
        self._resolvers[locale] = TranslationResolver(existing)

# ============================================================
# L4: 全域實例與便捷函數
# ============================================================

# 全域服務實例
_i18n: Optional[I18nService] = None


def get_i18n() -> I18nService:
    """獲取全域 i18n 服務"""
    global _i18n
    if _i18n is None:
        _i18n = I18nService()
    return _i18n


def t(key: str, params: Dict[str, Any] = None, locale: str = None) -> str:
    """全域翻譯函數"""
    return get_i18n().t(key, params, locale)


def set_locale(locale: str) -> bool:
    """設置語言"""
    return get_i18n().set_locale(locale)


def get_locale() -> str:
    """獲取當前語言"""
    return get_i18n().get_locale()


# API 響應輔助
def localized_response(data: Any, locale: str = None) -> Dict[str, Any]:
    """本地化 API 響應"""
    return {
        'data': data,
        'locale': locale or get_locale(),
        '_t': lambda k, p=None: t(k, p, locale)
    }


# 📚 知識點
# -----------
# 1. 點號路徑解析：支援 'auth.login' 格式的深層訪問
# 2. 回退機制：找不到翻譯時使用預設語言
# 3. 參數插值：支援 {param} 格式的動態參數
# 4. 快取策略：使用字典快取已載入的翻譯
# 5. 深度合併：動態添加翻譯時保留現有內容
