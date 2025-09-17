# Image Proxy Client 第三方快速获取指南

本目录提供了多种便捷方式，让第三方用户**仅获取转URL工具**，无需下载整个工程。

## 🚀 快速获取方式

### 方式1: 一行命令获取 (推荐)

**Windows PowerShell:**
```powershell
# 获取极简版本
iex (irm 'https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/dist/quick_get.ps1') -Mini

# 获取完整版本 + 配置文件
iex (irm 'https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/dist/quick_get.ps1') -Mini -Config
```

**Linux/macOS:**
```bash
# 获取极简版本
curl -fsSL https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/dist/quick_get.sh | bash -s -- --mini

# 获取完整版本 + 配置文件
curl -fsSL https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/dist/quick_get.sh | bash -s -- --mini --config
```

### 方式2: 直接下载单文件

选择适合的版本下载：

**极简版本 (< 5KB):**
```bash
# 只需一个文件，适合简单使用
wget https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/dist/image_proxy_mini.py
# 或
curl -O https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/dist/image_proxy_mini.py
```

**完整版本 (< 15KB):**
```bash
# 支持配置文件、多种选项
wget https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/dist/image_proxy_client.py
# 或  
curl -O https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/dist/image_proxy_client.py
```

### 方式3: Python 安装脚本

```bash
# 下载安装脚本
wget https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/dist/install.py

# 安装极简版本
python install.py --mini

# 安装完整版本并生成配置
python install.py --config
```

## 📦 版本对比

| 版本 | 文件大小 | 功能 | 适用场景 |
|------|----------|------|----------|
| **极简版** | < 5KB | 基础上传功能 | 脚本集成、一次性使用 |
| **完整版** | < 15KB | 完整功能、配置文件支持 | 项目集成、持续使用 |

## 🔧 使用方法

### 极简版本使用

```bash
# 命令行直接使用
python image_proxy_mini.py http://your-server.com username password image.jpg
```

**Python 代码调用:**
```python
from image_proxy_mini import upload_image

# 上传图片
result = upload_image("http://your-server.com", "username", "password", "image.jpg")
url = result.get('url')
print(f"图片URL: {url}")
```

### 完整版本使用

**命令行使用:**
```bash
# 直接指定参数
python image_proxy_client.py -s http://your-server.com -u username -p password image.jpg

# 使用配置文件
python image_proxy_client.py --config config.json image.jpg

# 检查服务健康状态
python image_proxy_client.py --health -s http://your-server.com
```

**Python 代码调用:**
```python
from image_proxy_client import quick_upload, ImageProxyClient

# 方式1: 快速上传
url = quick_upload("http://your-server.com", "username", "password", "image.jpg")
print(f"图片URL: {url}")

# 方式2: 使用客户端类
with ImageProxyClient("http://your-server.com", "username", "password") as client:
    result = client.upload_image("image.jpg")
    print(f"图片URL: {result['url']}")
```

## ⚙️ 配置文件格式

创建 `client_config.json`:
```json
{
  "server_url": "http://your-server.com:8000",
  "username": "your_username",
  "password": "your_password",
  "timeout": 30,
  "verify_ssl": true
}
```

使用配置文件:
```bash
python image_proxy_client.py --config client_config.json image.jpg
```

## 📋 依赖要求

- **Python**: 3.6+
- **依赖库**: `requests`

自动安装依赖:
```bash
pip install requests
```

## 🎯 集成示例

### 在现有项目中集成

**方法1: 复制文件到项目**
```bash
# 将客户端文件复制到项目目录
cp image_proxy_mini.py /path/to/your/project/utils/

# 在代码中使用
from utils.image_proxy_mini import upload_image
```

**方法2: 子模块方式**
```bash
# 添加为git子模块
git submodule add https://github.com/DpengYu/Image-Proxy-Project.git image_proxy
git submodule update --init

# 使用客户端
from image_proxy.dist.image_proxy_mini import upload_image
```

### 自动化脚本集成

**批量处理脚本:**
```bash
#!/bin/bash
# batch_upload.sh

SERVER="http://your-server.com"
USER="admin"  
PASS="password123"

for image in images/*.jpg; do
    echo "上传: $image"
    url=$(python image_proxy_mini.py "$SERVER" "$USER" "$PASS" "$image")
    echo "URL: $url"
    echo "$image -> $url" >> upload_log.txt
done
```

**Python 批量处理:**
```python
#!/usr/bin/env python3
import os
import glob
from image_proxy_mini import upload_image

# 配置
SERVER_URL = "http://your-server.com"
USERNAME = "admin"
PASSWORD = "password123"

# 批量上传
image_files = glob.glob("images/*.jpg")
for image_file in image_files:
    try:
        result = upload_image(SERVER_URL, USERNAME, PASSWORD, image_file)
        url = result.get('url')
        print(f"✅ {image_file} -> {url}")
    except Exception as e:
        print(f"❌ {image_file} 上传失败: {e}")
```

## 🔗 快速链接

- [完整项目仓库](../README.md)
- [API 文档](../docs/API.md)
- [快速上手指南](../QUICKSTART.md)
- [部署指南](../docs/DEPLOYMENT.md)

## ❓ 常见问题

**Q: 如何验证服务是否可用？**
```bash
# 使用完整版本检查
python image_proxy_client.py --health -s http://your-server.com
```

**Q: 如何处理认证失败？**
- 检查用户名和密码是否正确
- 确认服务器地址是否可访问
- 检查网络连接

**Q: 支持哪些图片格式？**
- 常见格式：JPG, PNG, GIF, BMP, WEBP
- 具体支持格式取决于服务器配置

**Q: 如何自定义超时时间？**
```python
# 完整版本支持自定义超时
client = ImageProxyClient(server_url, username, password, timeout=60)
```

## 📝 更新日志

- **v1.0.0**: 初始版本，支持基础上传功能
- 更多更新请查看完整项目仓库

---

💡 **提示**: 如需更多功能（如数据库管理、服务器部署等），请访问[完整项目仓库](../README.md)。