#!/usr/bin/env python3
"""
Image Proxy Mini Client - 极简版本
最小化的图片转URL工具，只包含核心功能

使用方法:
  python image_proxy_mini.py SERVER_URL USERNAME PASSWORD IMAGE_PATH

示例:
  python image_proxy_mini.py http://localhost:8000 admin password123 image.jpg

版本: 1.0.0
大小: < 5KB
依赖: requests
"""

import sys
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: Missing requests library")
    print("Install: pip install requests")
    sys.exit(1)

def upload_image(server_url, username, password, image_path, timeout=30):
    """上传图片并返回URL"""
    # 检查文件
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {image_path}")
    
    # 准备请求
    url = f"{server_url.rstrip('/')}/upload"
    params = {"username": username, "password": password}
    
    with open(path, 'rb') as f:
        files = {"file": (path.name, f, "application/octet-stream")}
        response = requests.post(url, files=files, params=params, timeout=timeout)
    
    # 处理响应
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        raise ValueError("Authentication failed")
    else:
        raise ValueError(f"Upload failed: HTTP {response.status_code}")

def main():
    """命令行入口"""
    if len(sys.argv) != 5:
        print("Usage: python image_proxy_mini.py SERVER_URL USERNAME PASSWORD IMAGE_PATH")
        print("Example: python image_proxy_mini.py http://localhost:8000 admin pass123 image.jpg")
        sys.exit(1)
    
    server_url, username, password, image_path = sys.argv[1:5]
    
    try:
        result = upload_image(server_url, username, password, image_path)
        print(result.get('url', ''))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()