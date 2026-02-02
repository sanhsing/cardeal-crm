"""
車行寶 CRM - PWA 圖標生成器
北斗七星文創數位 × 織明

生成各尺寸 SVG 圖標
"""
import os

# SVG 模板
SVG_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea"/>
      <stop offset="100%" style="stop-color:#764ba2"/>
    </linearGradient>
  </defs>
  <!-- 背景 -->
  <rect width="512" height="512" rx="80" fill="url(#bg)"/>
  <!-- 車輛圖標 -->
  <g transform="translate(100, 140)">
    <!-- 車身 -->
    <path d="M290 120 L270 60 L180 40 L120 40 L100 60 L30 120 L10 140 L10 180 L30 200 L290 200 L310 180 L310 140 Z" 
          fill="white" opacity="0.95"/>
    <!-- 車窗 -->
    <path d="M260 80 L245 55 L185 45 L130 45 L115 55 L60 80 L60 120 L260 120 Z" 
          fill="#667eea" opacity="0.6"/>
    <!-- 車輪 -->
    <circle cx="80" cy="200" r="40" fill="#333"/>
    <circle cx="80" cy="200" r="25" fill="#666"/>
    <circle cx="80" cy="200" r="10" fill="#999"/>
    <circle cx="240" cy="200" r="40" fill="#333"/>
    <circle cx="240" cy="200" r="25" fill="#666"/>
    <circle cx="240" cy="200" r="10" fill="#999"/>
  </g>
  <!-- 文字：寶 -->
  <text x="256" y="420" font-family="Arial, sans-serif" font-size="80" 
        font-weight="bold" fill="white" text-anchor="middle">CRM</text>
</svg>'''

# 尺寸列表
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

def generate_icons():
    """生成所有尺寸的圖標"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    for size in SIZES:
        svg_content = SVG_TEMPLATE.format(size=size)
        filename = f"icon-{size}.svg"
        filepath = os.path.join(script_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        print(f"✅ 生成 {filename}")
    
    # 生成 badge 圖標（簡化版）
    badge_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="72" height="72" viewBox="0 0 72 72" xmlns="http://www.w3.org/2000/svg">
  <circle cx="36" cy="36" r="32" fill="#667eea"/>
  <text x="36" y="45" font-family="Arial" font-size="28" font-weight="bold" 
        fill="white" text-anchor="middle">C</text>
</svg>'''
    
    with open(os.path.join(script_dir, 'badge-72.svg'), 'w') as f:
        f.write(badge_svg)
    print("✅ 生成 badge-72.svg")
    
    # 生成 favicon
    favicon_svg = SVG_TEMPLATE.format(size=32)
    with open(os.path.join(script_dir, 'favicon.svg'), 'w') as f:
        f.write(favicon_svg)
    print("✅ 生成 favicon.svg")

if __name__ == '__main__':
    generate_icons()
    print("\n🎉 所有圖標生成完成！")
