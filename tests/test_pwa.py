"""
車行寶 CRM v5.1 - PWA 測試
北斗七星文創數位 × 織明
"""
import unittest
import json
import os


class TestManifest(unittest.TestCase):
    """PWA Manifest 測試"""
    
    @classmethod
    def setUpClass(cls):
        """讀取 manifest.json"""
        manifest_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'static', 'manifest.json'
        )
        with open(manifest_path, 'r', encoding='utf-8') as f:
            cls.manifest = json.load(f)
    
    def test_required_fields(self):
        """測試必要欄位"""
        required = ['name', 'short_name', 'start_url', 'display', 'icons']
        for field in required:
            self.assertIn(field, self.manifest)
    
    def test_icons_exist(self):
        """測試圖標存在"""
        self.assertGreater(len(self.manifest['icons']), 0)
        
        # 檢查必要尺寸
        sizes = [icon['sizes'] for icon in self.manifest['icons']]
        self.assertIn('192x192', sizes)
        self.assertIn('512x512', sizes)
    
    def test_display_mode(self):
        """測試顯示模式"""
        valid_modes = ['standalone', 'fullscreen', 'minimal-ui', 'browser']
        self.assertIn(self.manifest['display'], valid_modes)
    
    def test_theme_color(self):
        """測試主題色"""
        self.assertIn('theme_color', self.manifest)
        # 應該是有效的顏色格式
        color = self.manifest['theme_color']
        self.assertTrue(color.startswith('#') or color.startswith('rgb'))


class TestServiceWorker(unittest.TestCase):
    """Service Worker 測試"""
    
    @classmethod
    def setUpClass(cls):
        """讀取 service-worker.js"""
        sw_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'static', 'service-worker.js'
        )
        with open(sw_path, 'r', encoding='utf-8') as f:
            cls.sw_content = f.read()
    
    def test_install_event(self):
        """測試 install 事件"""
        self.assertIn("addEventListener('install'", self.sw_content)
    
    def test_activate_event(self):
        """測試 activate 事件"""
        self.assertIn("addEventListener('activate'", self.sw_content)
    
    def test_fetch_event(self):
        """測試 fetch 事件"""
        self.assertIn("addEventListener('fetch'", self.sw_content)
    
    def test_cache_strategy(self):
        """測試快取策略"""
        # 應該有 cacheFirst 或 networkFirst
        self.assertTrue(
            'cacheFirst' in self.sw_content or 
            'networkFirst' in self.sw_content
        )
    
    def test_push_event(self):
        """測試推播事件"""
        self.assertIn("addEventListener('push'", self.sw_content)


class TestIcons(unittest.TestCase):
    """圖標測試"""
    
    def test_icons_directory_exists(self):
        """測試圖標目錄存在"""
        icons_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'static', 'icons'
        )
        self.assertTrue(os.path.isdir(icons_path))
    
    def test_required_icons_exist(self):
        """測試必要圖標存在"""
        icons_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'static', 'icons'
        )
        
        required_sizes = [72, 96, 128, 144, 152, 192, 384, 512]
        for size in required_sizes:
            icon_file = os.path.join(icons_path, f'icon-{size}.png')
            self.assertTrue(
                os.path.exists(icon_file), 
                f'Missing icon-{size}.png'
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
