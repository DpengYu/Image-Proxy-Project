#!/bin/bash
# Image Proxy Client 一键获取脚本 (Bash)
# 适用于 Linux/macOS 用户

set -e

# 参数解析
MINI=false
CONFIG=false
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --mini)
            MINI=true
            shift
            ;;
        --config)
            CONFIG=true
            shift
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--mini] [--config] [-o output_file]"
            echo "  --mini    : 获取极简版本"
            echo "  --config  : 生成配置文件"
            echo "  -o FILE   : 指定输出文件名"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🚀 Image Proxy Client 快速获取"
echo "========================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ 未找到 Python，请先安装 Python"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "✅ $($PYTHON_CMD --version) 已安装"

# 检查 requests
if ! $PYTHON_CMD -c "import requests" 2>/dev/null; then
    echo "❌ 缺少 requests 库"
    echo "正在安装 requests..."
    pip install requests || pip3 install requests
else
    echo "✅ requests 库已安装"
fi

# 创建客户端文件
if [ "$MINI" = true ]; then
    FILENAME=${OUTPUT:-"image_proxy_mini.py"}
    echo "正在创建极简客户端: $FILENAME"
    
    cat > "$FILENAME" << 'EOF'
#!/usr/bin/env python3
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
EOF
    
    chmod +x "$FILENAME"
    echo "✅ 创建完成: $FILENAME"
else
    echo "❌ 暂不支持在线下载完整版本，请使用 --mini 参数"
    exit 1
fi

# 生成配置文件
if [ "$CONFIG" = true ]; then
    CONFIG_FILE="client_config.json"
    echo "正在创建配置文件: $CONFIG_FILE"
    
    cat > "$CONFIG_FILE" << 'EOF'
{
  "server_url": "http://localhost:8000",
  "username": "admin",
  "password": "password123",
  "timeout": 30,
  "verify_ssl": true
}
EOF
    
    echo "✅ 创建配置文件: $CONFIG_FILE"
    echo "⚠️  请修改配置文件中的服务器地址和认证信息"
fi

# 输出使用说明
echo ""
echo "🎉 获取完成!"
echo ""
echo "📖 使用说明:"

if [ "$MINI" = true ]; then
    echo "极简版本使用:"
    echo "  $PYTHON_CMD $FILENAME http://your-server.com username password image.jpg"
fi

if [ "$CONFIG" = true ]; then
    echo ""
    echo "配置文件使用:"
    echo "  1. 编辑 client_config.json"
    echo "  2. 修改 server_url, username, password"
    echo "  3. 运行: $PYTHON_CMD $FILENAME image.jpg"
fi

echo ""
echo "💡 提示: 更多功能请访问完整项目仓库"