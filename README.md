# 🖼️ Image Proxy Project

> **企业级图片上传与代理服务** - 高性能、安全可靠、开箱即用

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![systemd](https://img.shields.io/badge/systemd-Compatible-red.svg)](https://systemd.io/)

一套专为现代应用设计的高性能图片上传与代理系统，支持本地上传、云端存储、智能缓存和自动过期管理。无论是个人项目还是企业应用，都能快速集成并稳定运行。

---

## 🎯 核心特性

### 🚀 **高性能架构**
- **异步处理**: 基于FastAPI + Uvicorn，支持高并发上传
- **智能去重**: 客户端与服务端双重MD5校验，避免重复存储
- **本地缓存**: SQLite本地缓存，提升访问效率
- **自动过期**: 可配置的图片生命周期管理

### 🛡️ **企业级安全**
- **身份认证**: 用户名密码双重验证
- **文件校验**: 严格的文件类型和大小限制
- **速率限制**: 防止滥用的智能限流
- **安全Token**: 动态生成的访问令牌

### 🔧 **运维友好**
- **一键部署**: 完整的自动化安装脚本
- **服务管理**: systemd服务管理，支持开机自启
- **日志监控**: 完善的日志系统和状态监控
- **定时清理**: 自动清理过期文件，节省存储空间

### 🔌 **集成便捷**
- **多种方式**: 支持API调用、Python包、单文件集成
- **第三方友好**: 标准化的客户端包，支持pip安装
- **配置灵活**: 支持配置文件、环境变量等多种配置方式
- **文档完善**: 详细的使用文档和集成示例

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────┐    HTTP     ┌─────────────────┐
│                 │    请求     │                 │
│  客户端应用      │ ─────────> │   FastAPI服务    │
│                 │             │                 │
│ • Web应用       │             │ • 图片上传       │
│ • 移动应用      │             │ • 访问代理       │ 
│ • 桌面程序      │             │ • 权限验证       │
│ • 脚本工具      │             │ • 文件管理       │
│                 │             │                 │
└─────────────────┘             └─────────────────┘
         │                               │
         │ SQLite缓存                    │ 文件存储 + SQLite数据库
         ▼                               ▼
┌─────────────────┐             ┌─────────────────┐
│   本地缓存       │             │   服务器存储     │
│                 │             │                 │
│ • URL缓存       │             │ • uploads/目录   │
│ • MD5记录       │             │ • images.db     │
│ • 重复检测      │             │ • 元数据管理     │
└─────────────────┘             └─────────────────┘
```

### 核心组件关系

**客户端层**:
- **应用客户端**: 各种需要图片上传功能的应用
- **Python包**: 标准化的`image_proxy_client`包
- **本地缓存**: SQLite数据库缓存已上传图片信息

**服务端层**:
- **FastAPI服务**: 处理HTTP请求，提供RESTful API
- **文件存储**: 本地`uploads/`目录存储图片文件
- **数据库**: SQLite存储图片元数据和访问记录

**运维层**:
- **systemd服务**: 自动启动和监控服务状态
- **Nginx代理**: 反向代理和负载均衡（可选）
- **定时清理**: 自动清理过期文件和数据

---

## 🚀 快速开始

### 方式一：一键自动部署（推荐）

适用于**Linux生产环境**，完全自动化的部署方案：

```bash
# 1. 克隆项目
git clone https://github.com/DpengYu/Image-Proxy-Project.git
cd Image-Proxy-Project

# 2. 一键安装和部署
cd scripts
sudo ./install.sh
```

**自动完成的工作**：
- ✅ 检查系统要求（Python 3.10+、systemd、nginx等）
- ✅ 创建虚拟环境并安装所有依赖
- ✅ 生成安全配置和密钥
- ✅ 配置systemd服务和定时任务
- ✅ 设置Nginx反向代理
- ✅ 启动服务并验证安装

### 方式二：手动开发部署

适用于**开发调试**或需要自定义配置的场景：

```bash
# 1. 环境准备
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置服务
cp config/config.template.json config/config.json
# 编辑 config/config.json 修改必要参数

# 4. 生成安全密钥
python tools/generate_secret_key.py --config config/config.json --password

# 5. 启动服务
cd server
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

### 🎉 安装完成验证

```bash
# 检查服务状态
curl http://localhost:8000/health

# 运行完整测试
python tools/test_service.py

# 访问API文档
# 浏览器打开: http://your-domain.com/docs
```

---

## ⚙️ 配置说明

### 核心配置文件：`config/config.json`

| 配置项 | 说明 | 默认值 | 必须修改 |
|--------|------|--------| --------|
| `server.domain` | 服务访问域名/IP | `http://localhost` | ✅ |
| `server.port` | 服务端口 | `8000` | ❌ |
| `security.secret_key` | 32位安全密钥 | 模板值 | ✅ |
| `users[0].username` | 管理员用户名 | `admin` | ✅ |
| `users[0].password` | 管理员密码 | 模板值 | ✅ |

### 完整配置结构

```json
{
  "server": {
    "domain": "http://your-domain.com",
    "port": 8000
  },
  "security": {
    "secret_key": "your-32-char-secret-key-here",
    "upload": {
      "max_file_size_mb": 10,
      "allowed_types": ["image/jpeg", "image/png", "image/gif", "image/webp"]
    },
    "rate_limit": {
      "max_requests": 100,
      "window_seconds": 60
    }
  },
  "cleanup": {
    "enable": true,
    "expire_days": 30,
    "cleanup_time": "03:00:00"
  },
  "users": [
    {
      "username": "admin",
      "password": "your-secure-password"
    }
  ]
}
```

### 快速配置工具

```bash
# 自动生成安全配置
python tools/generate_secret_key.py --config config/config.json --username admin --password

# 快速配置向导
python tools/quick_setup.py --domain http://your-domain.com
```

---

## 🛠️ 服务管理

### 一键管理脚本

项目提供完整的服务管理脚本，位于`scripts/`目录：

```bash
# 一键安装部署
sudo ./install.sh

# 服务控制
sudo ./start.sh      # 启动所有服务
sudo ./stop.sh       # 停止所有服务

# 数据管理  
./reset.sh           # 重置数据库和上传文件（谨慎使用）
./uninstall.sh       # 完全卸载系统（保留配置）
```

### systemd服务管理

```bash
# 服务状态控制
sudo systemctl start fastapi        # 启动服务
sudo systemctl stop fastapi         # 停止服务
sudo systemctl restart fastapi      # 重启服务
sudo systemctl status fastapi       # 查看状态

# 开机自启控制
sudo systemctl enable fastapi       # 开机自启
sudo systemctl disable fastapi      # 禁用自启
```

### 日志管理

```bash
# 实时查看日志
journalctl -u fastapi --no-pager -f

# 查看最近日志
journalctl -u fastapi --no-pager -n 100

# 查看清理任务日志
journalctl -u fastapi-cleanup --no-pager -f
```

---

## 📖 使用指南

### 1. 基础客户端使用

**Python客户端**（推荐）：
```python
from client.client import upload_or_get

# 上传图片并获取信息
info = upload_or_get("your_image.jpg")
print(f"图片URL: {info['url']}")
print(f"图片大小: {info['width']}x{info['height']}")
```

**命令行工具**：
```bash
cd client
python client.py your_image.jpg
```

### 2. 第三方项目集成

**方式一：使用image_proxy_client包**（推荐）
```python
# 安装方式1: Git Submodule
git submodule add https://github.com/DpengYu/Image-Proxy-Project.git image_proxy
cd image_proxy && git sparse-checkout set image_proxy_client

# 安装方式2: 直接复制
cp -r image_proxy_client /path/to/your/project/

# 使用示例
from image_proxy_client import quick_upload

url = quick_upload(
    server_url="http://your-domain.com:8000",
    username="admin",
    password="your_password",
    image_path="image.jpg"
)
print(f"图片URL: {url}")
```

**方式二：环境变量配置**
```python
import os
from image_proxy_client import ImageProxyConfig

# 设置环境变量
os.environ['IMAGE_PROXY_URL'] = 'http://your-domain.com:8000'
os.environ['IMAGE_PROXY_USERNAME'] = 'admin'
os.environ['IMAGE_PROXY_PASSWORD'] = 'your_password'

# 自动加载配置
config = ImageProxyConfig()
client = config.get_client()
url = client.get_image_url("image.jpg")
```

### 3. Web应用集成示例

**Flask应用集成**：
```python
from flask import Flask, request, jsonify
from image_proxy_client import quick_upload

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    temp_path = f"/tmp/{file.filename}"
    file.save(temp_path)
    
    try:
        url = quick_upload(
            "http://localhost:8000",
            "admin", "password",
            temp_path
        )
        return jsonify({'url': url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.unlink(temp_path)
```

**Django应用集成**：
```python
# settings.py
IMAGE_PROXY_CONFIG = {
    'server_url': 'http://localhost:8000',
    'username': 'admin',
    'password': 'password'
}

# views.py
from django.conf import settings
from image_proxy_client import ImageProxyClient

def upload_view(request):
    config = settings.IMAGE_PROXY_CONFIG
    with ImageProxyClient(**config) as client:
        url = client.get_image_url(image_path)
        return JsonResponse({'url': url})
```

### 4. API直接调用

**上传图片**：
```bash
curl -X POST "http://your-domain.com:8000/upload" \
  -F "file=@image.jpg" \
  -F "username=admin" \
  -F "password=your_password"
```

**获取图片**：
```bash
curl "http://your-domain.com:8000/secure_get/{md5}?token={token}"
```

**健康检查**：
```bash
curl "http://your-domain.com:8000/health"
```

---

## 🔧 实用工具

### 密钥生成工具
```bash
# 生成32位安全密钥
python tools/generate_secret_key.py

# 自动更新配置文件
python tools/generate_secret_key.py --config config/config.json --password

# 生成环境变量格式
python tools/generate_secret_key.py --env
```

### 服务测试工具
```bash
# 完整功能测试
python tools/test_service.py

# 快速健康检查
python tools/test_service.py --quick

# 指定配置文件测试
python tools/test_service.py --config /path/to/config.json
```

### 快速配置工具
```bash
# 交互式配置向导
python tools/quick_setup.py --domain http://your-domain.com

# 跳过依赖安装
python tools/quick_setup.py --domain http://your-domain.com --skip-deps
```

---

## 📁 项目结构

```
Image-Proxy-Project/
├── 📂 client/                 # 客户端代码
│   ├── client.py             # 主客户端程序
│   └── download_db.py        # 数据库下载工具
├── 📂 image_proxy_client/     # 第三方集成包 ⭐
│   ├── __init__.py           # 包初始化
│   ├── client.py             # 核心客户端类
│   ├── config.py             # 配置管理
│   ├── cli.py                # 命令行工具
│   ├── setup.py              # 安装脚本
│   ├── requirements.txt      # 依赖管理
│   └── README.md             # 使用文档
├── 📂 server/                # 服务端代码
│   ├── server.py             # FastAPI主服务
│   ├── database.py           # 数据库管理
│   ├── security_utils.py     # 安全工具
│   ├── config_validator.py   # 配置验证
│   ├── logger_config.py      # 日志配置
│   └── cleanup.py            # 清理脚本
├── 📂 scripts/               # 管理脚本 ⭐
│   ├── install.sh            # 一键安装
│   ├── start.sh              # 启动服务
│   ├── stop.sh               # 停止服务
│   ├── reset.sh              # 重置数据
│   └── uninstall.sh          # 卸载系统
├── 📂 tools/                 # 实用工具
│   ├── generate_secret_key.py # 密钥生成
│   ├── test_service.py       # 服务测试
│   └── quick_setup.py        # 快速配置
├── 📂 config/                # 配置文件
│   ├── config.template.json  # 配置模板
│   └── config.json           # 实际配置（被忽略）
├── 📂 docs/                  # 文档目录
│   ├── API.md                # API文档
│   └── DEPLOYMENT.md         # 部署指南
├── 📂 examples/              # 集成示例
│   └── integration_examples.py # 第三方集成示例
├── 📂 tests/                 # 测试代码
├── 📄 QUICKSTART.md          # 快速上手指南
├── 📄 DEVELOPMENT.md         # 开发文档
├── 📄 THIRD_PARTY_INTEGRATION.md # 第三方集成指南
├── 📄 demo_integration.py    # 集成演示脚本
├── 📄 requirements.txt       # 主依赖文件
└── 📄 README.md              # 项目说明（本文件）
```

---

## 🌍 使用场景

### 1. 个人博客/网站
- **场景**: 博客图片上传和管理
- **方案**: 单机部署，使用客户端工具上传
- **配置**: 默认配置即可，修改域名和密码

### 2. 企业内部系统
- **场景**: 内部应用的图片存储服务
- **方案**: 服务器部署，第三方应用集成`image_proxy_client`包
- **配置**: 配置企业域名、增加用户、设置文件大小限制

### 3. 移动App后端
- **场景**: 移动应用的图片上传接口
- **方案**: 云服务器部署，Nginx代理，API调用
- **配置**: 配置HTTPS、增强安全设置、设置速率限制

### 4. 微服务架构
- **场景**: 微服务中的图片服务组件
- **方案**: 容器化部署，服务发现，负载均衡
- **配置**: 配置集群、数据持久化、监控告警

---

## 🚨 故障排除

### 常见问题及解决方案

#### 服务启动失败
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 检查配置文件
python -c "import json; json.load(open('config/config.json'))"

# 查看详细错误日志
journalctl -u fastapi --no-pager -n 50
```

#### 上传失败
```bash
# 检查文件权限
ls -la server/uploads/

# 检查磁盘空间
df -h

# 测试API连通性
curl -f http://localhost:8000/health
```

#### 图片访问失败
```bash
# 检查Nginx配置
sudo nginx -t

# 检查服务状态
sudo systemctl status fastapi

# 检查防火墙
sudo ufw status
```

### 重置和恢复

```bash
# 重置数据但保留配置
./scripts/reset.sh

# 重新生成密钥
python tools/generate_secret_key.py --config config/config.json --password

# 重新安装服务
./scripts/uninstall.sh
./scripts/install.sh
```

---

## 🔒 安全建议

### 生产环境安全配置

1. **HTTPS配置**
```bash
# 使用Let's Encrypt获取SSL证书
sudo certbot --nginx -d your-domain.com
```

2. **防火墙配置**
```bash
# 只开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

3. **访问控制**
```json
// 在config.json中限制IP访问
{
  "security": {
    "allowed_ips": ["192.168.1.0/24", "10.0.0.0/8"],
    "rate_limit": {
      "max_requests": 50,
      "window_seconds": 60
    }
  }
}
```

4. **定期备份**
```bash
# 设置数据库备份cron任务
0 2 * * * cp /path/to/server/images.db /backup/images_$(date +\%Y\%m\%d).db
```

---

## 🤝 贡献指南

### 开发环境搭建
```bash
# 克隆项目
git clone https://github.com/DpengYu/Image-Proxy-Project.git
cd Image-Proxy-Project

# 创建开发环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 代码格式化
black server/ client/ tools/
```

### 提交代码
1. Fork本项目
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add some amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 创建Pull Request

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🙏 致谢

感谢所有为本项目做出贡献的开发者和用户！

---

## 📞 联系我们

- **项目主页**: [GitHub Repository](https://github.com/DpengYu/Image-Proxy-Project)
- **问题反馈**: [Issues](https://github.com/DpengYu/Image-Proxy-Project/issues)
- **功能建议**: [Discussions](https://github.com/DpengYu/Image-Proxy-Project/discussions)

---

> 💡 **开始使用**: 推荐先阅读 [快速上手指南](QUICKSTART.md)，然后参考 [第三方集成文档](THIRD_PARTY_INTEGRATION.md) 进行项目集成。
> 
> 🔧 **生产部署**: 查看 [部署指南](docs/DEPLOYMENT.md) 了解详细的生产环境配置。
>
> 📚 **API文档**: 访问 `http://your-domain.com/docs` 查看完整的API文档。