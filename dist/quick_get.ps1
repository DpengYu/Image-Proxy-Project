# Image Proxy Client 一键获取脚本 (PowerShell)
# 适用于 Windows 用户

param(
    [switch]$Mini,
    [switch]$Config,
    [string]$Output = ""
)

Write-Host "🚀 Image Proxy Client 快速获取" -ForegroundColor Green
Write-Host "=" * 40

# 检查 Python
try {
    $pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    Write-Host "✅ Python $pythonVersion 已安装" -ForegroundColor Green
} catch {
    Write-Host "❌ 未找到 Python，请先安装 Python" -ForegroundColor Red
    exit 1
}

# 检查 requests
try {
    python -c "import requests" 2>$null
    Write-Host "✅ requests 库已安装" -ForegroundColor Green
} catch {
    Write-Host "❌ 缺少 requests 库" -ForegroundColor Red
    Write-Host "正在安装 requests..." -ForegroundColor Yellow
    pip install requests
}

# 下载客户端
if ($Mini) {
    $filename = if ($Output) { $Output } else { "image_proxy_mini.py" }
    Write-Host "正在创建极简客户端: $filename" -ForegroundColor Yellow
    
    $miniCode = @'
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
'@
    
    $miniCode | Out-File -FilePath $filename -Encoding UTF8
    Write-Host "✅ 创建完成: $filename" -ForegroundColor Green
    
} else {
    Write-Host "❌ 暂不支持在线下载完整版本，请使用 -Mini 参数" -ForegroundColor Red
    exit 1
}

# 生成配置文件
if ($Config) {
    $configFile = "client_config.json"
    $configContent = @{
        server_url = "http://localhost:8000"
        username = "admin"
        password = "password123"
        timeout = 30
        verify_ssl = $true
    } | ConvertTo-Json -Depth 2
    
    $configContent | Out-File -FilePath $configFile -Encoding UTF8
    Write-Host "✅ 创建配置文件: $configFile" -ForegroundColor Green
    Write-Host "⚠️  请修改配置文件中的服务器地址和认证信息" -ForegroundColor Yellow
}

# 输出使用说明
Write-Host ""
Write-Host "🎉 获取完成!" -ForegroundColor Green
Write-Host ""
Write-Host "📖 使用说明:" -ForegroundColor Cyan

if ($Mini) {
    Write-Host "极简版本使用:" -ForegroundColor White
    Write-Host "  python $filename http://your-server.com username password image.jpg" -ForegroundColor Gray
}

if ($Config) {
    Write-Host ""
    Write-Host "配置文件使用:" -ForegroundColor White
    Write-Host "  1. 编辑 client_config.json" -ForegroundColor Gray
    Write-Host "  2. 修改 server_url, username, password" -ForegroundColor Gray
    Write-Host "  3. 运行: python $filename image.jpg" -ForegroundColor Gray
}