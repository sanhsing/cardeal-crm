"""
車行寶 CRM v5.2 - Swagger UI 頁面
北斗七星文創數位 × 織明
"""
from typing import Dict, Any

def get_swagger_html() -> str:
    """生成 Swagger UI HTML"""
    return '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>車行寶 CRM API 文檔</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    <style>
        body { margin: 0; padding: 0; }
        .topbar { display: none; }
        .swagger-ui .info { margin: 20px 0; }
        .swagger-ui .info .title { color: #3b4151; }
        .custom-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .custom-header h1 { margin: 0 0 10px 0; font-size: 24px; }
        .custom-header p { margin: 0; opacity: 0.9; }
    </style>
</head>
<body>
    <div class="custom-header">
        <h1>🚗 車行寶 CRM API 文檔</h1>
        <p>v5.2 | 北斗七星文創數位</p>
    </div>
    <div id="swagger-ui"></div>
    
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            SwaggerUIBundle({
                url: "/api/docs/openapi.yaml",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                persistAuthorization: true,
                displayRequestDuration: true,
                filter: true,
                tryItOutEnabled: true
            });
        };
    </script>
</body>
</html>'''


def get_redoc_html() -> str:
    """生成 ReDoc HTML（替代方案）"""
    return '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>車行寶 CRM API 文檔</title>
    <link href="https://fonts.googleapis.com/css?family=Noto+Sans+TC:400,700" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; font-family: 'Noto Sans TC', sans-serif; }
    </style>
</head>
<body>
    <redoc spec-url="/api/docs/openapi.yaml"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>'''
