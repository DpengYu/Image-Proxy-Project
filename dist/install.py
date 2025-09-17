#!/usr/bin/env python3
"""
Image Proxy Client 一键安装脚本
自动下载并配置图片代理客户端

使用方法:
  python install.py
  python install.py --mini     # 安装极简版本
  python install.py --config   # 同时生成配置文件
"""

import os
import sys
import json
import argparse
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError

# 客户端文件URLs (可以替换为实际的在线地址)
CLIENT_URLS = {
    "full": "https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/dist/image_proxy_client.py",
    "mini": "https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/dist/image_proxy_mini.py"
}

# 本地文件内容（作为fallback）
MINI_CLIENT_CODE = '''#!/usr/bin/env python3
"""
Image Proxy Mini Client - 极简版本
最小化的图片转URL工具，只包含核心功能
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
'''

def download_file(url, filename):
    """下载文件"""
    try:
        print(f"正在下载 {filename}...")
        urlretrieve(url, filename)
        print(f"✅ 下载完成: {filename}")
        return True
    except URLError:
        print(f"❌ 下载失败，使用本地版本创建 {filename}")
        return False

def create_mini_client(filename="image_proxy_mini.py"):
    """创建极简客户端"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(MINI_CLIENT_CODE)
        
        # 设置执行权限 (Unix/Linux)
        if os.name != 'nt':
            os.chmod(filename, 0o755)
        
        print(f"✅ 创建极简客户端: {filename}")
        return True
    except Exception as e:
        print(f"❌ 创建文件失败: {e}")
        return False

def create_config_file(filename="client_config.json"):
    """创建配置文件"""
    config = {
        "server_url": "http://localhost:8000",
        "username": "admin",
        "password": "password123",
        "timeout": 30,
        "verify_ssl": True
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ 创建配置文件: {filename}")
        print("⚠️  请修改配置文件中的服务器地址和认证信息")
        return True
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False

def check_dependencies():
    """检查依赖"""
    try:
        import requests
        print("✅ requests 库已安装")
        return True
    except ImportError:
        print("❌ 缺少 requests 库")
        print("请运行: pip install requests")
        return False

def main():
    parser = argparse.ArgumentParser(description="Image Proxy Client 一键安装")
    parser.add_argument("--mini", action="store_true", help="安装极简版本")
    parser.add_argument("--config", action="store_true", help="生成配置文件")
    parser.add_argument("--no-deps-check", action="store_true", help="跳过依赖检查")
    parser.add_argument("-o", "--output", help="输出文件名")
    
    args = parser.parse_args()
    
    print("🚀 Image Proxy Client 安装程序")
    print("=" * 40)
    
    # 检查依赖
    if not args.no_deps_check and not check_dependencies():
        return False
    
    success = True
    
    # 安装客户端
    if args.mini:
        filename = args.output or "image_proxy_mini.py"
        success &= create_mini_client(filename)
    else:
        filename = args.output or "image_proxy_client.py"
        if filename in CLIENT_URLS:
            success &= download_file(CLIENT_URLS["full"], filename)
        else:
            print("❌ 暂不支持在线下载完整版本，请使用 --mini 参数")
            success = False
    
    # 生成配置文件
    if args.config:
        success &= create_config_file()
    
    # 输出使用说明
    if success:
        print("\n🎉 安装完成!")
        print("\n📖 使用说明:")
        
        if args.mini:
            print("极简版本使用:")
            print(f"  python {filename} http://your-server.com username password image.jpg")
        else:
            print("完整版本使用:")
            print(f"  python {filename} -s http://your-server.com -u username -p password image.jpg")
            print(f"  python {filename} --config config.json image.jpg")
        
        if args.config:
            print("\n配置文件:")
            print("  1. 编辑 client_config.json")
            print("  2. 修改 server_url, username, password")
            print("  3. 直接使用: python {} image.jpg".format(filename))
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)