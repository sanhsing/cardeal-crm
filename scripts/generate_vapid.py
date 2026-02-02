#!/usr/bin/env python3
"""
車行寶 CRM v5.2 - VAPID 金鑰生成工具
北斗七星文創數位 × 織明

用法：python scripts/generate_vapid.py
"""
import os
import base64
import secrets

try:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def generate_vapid_keys():
    """生成 VAPID 公私鑰對"""
    
    if HAS_CRYPTO:
        # 使用 cryptography 庫（推薦）
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        public_key = private_key.public_key()
        
        # 私鑰（Base64 URL safe）
        private_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
        private_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').rstrip('=')
        
        # 公鑰（未壓縮格式，65 bytes）
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        public_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').rstrip('=')
        
        return public_b64, private_b64
    else:
        # 簡易生成（僅供測試）
        print("⚠️ cryptography 未安裝，生成簡易金鑰（僅供測試）")
        print("   安裝：pip install cryptography")
        
        private_b64 = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        public_b64 = base64.urlsafe_b64encode(secrets.token_bytes(65)).decode('utf-8').rstrip('=')
        
        return public_b64, private_b64


def main():
    print("=" * 50)
    print("🔑 VAPID 金鑰生成工具")
    print("=" * 50)
    print()
    
    public_key, private_key = generate_vapid_keys()
    
    print("✅ 金鑰生成成功！")
    print()
    print("請將以下內容添加到 .env 檔案：")
    print()
    print("-" * 50)
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print(f"VAPID_PRIVATE_KEY={private_key}")
    print("VAPID_SUBJECT=mailto:admin@your-domain.com")
    print("-" * 50)
    print()
    print("📱 前端使用（service-worker.js）：")
    print(f"   applicationServerKey: '{public_key}'")
    print()
    print("⚠️ 注意事項：")
    print("   1. 私鑰請妥善保管，勿外洩")
    print("   2. 公鑰需要配置到前端")
    print("   3. 每個環境應使用不同金鑰")


if __name__ == '__main__':
    main()
