# 🚀 Image Proxy Project 快速上手指南

本指南将帮助您在5分钟内快速部署和使用Image Proxy Project。

---

## 📋 前置要求

- **Python**: 3.10或更高版本
- **操作系统**: Linux (推荐) / Windows (开发测试)
- **内存**: 至少512MB可用内存
- **磁盘**: 至少1GB可用空间

---

## ⚡ 快速部署

### 1️⃣ 下载项目
```bash
git clone https://github.com/DpengYu/Image-Proxy-Project.git
cd image_proxy_project
```

### 2️⃣ 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements-prod.txt
```

### 3️⃣ 生成安全配置
```bash
# 生成32位安全密钥并自动配置
python tools/generate_secret_key.py --config config/config.json --username admin --password

# 输出示例：
# 🔑 安全密钥 (32位): Kx7mP9QwE3rT8uY2vZ5nB6cF4gH1jL0k
# 🔒 强密码 (16位): Mg8$kL2#pR9*qW5!
# ✅ 配置文件已更新: config/config.json
```

### 4️⃣ 修改域名配置
```bash
# 编辑配置文件，设置您的域名
vim config/config.json
```

**需要修改的配置：**
```json
{
  "server": {
    "domain": "http://your-domain.com",  # 改为您的域名或IP
    "port": 8000
  }
}
```

### 5️⃣ 启动服务

**开发环境：**
```bash
cd server
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**生产环境 (Linux)：**
```bash
cd scripts
sudo ./install.sh
```

### 6️⃣ 测试服务
```bash
# 运行测试工具
python tools/test_service.py

# 快速测试（仅健康检查）
python tools/test_service.py --quick
```

---

## 🎯 基本使用

### 方法1: 使用客户端脚本
```bash
cd client
python client.py
```

### 方法2: 第三方项目集成
```python
# 在您的项目中
from image_proxy_simple import setup_image_proxy, upload_image

# 配置服务
setup_image_proxy("http://your-domain.com", "admin", "your-password")

# 上传图片
url = upload_image("/path/to/your/image.jpg")
if url:
    print(f"图片URL: {url}")
```

### 方法3: 直接API调用
```bash
# 上传图片
curl -X POST "http://your-domain.com/upload?username=admin&password=your-password" \
  -F "file=@image.jpg"

# 健康检查
curl "http://your-domain.com/health"
```

---

## ⚙️ 重要配置参数

### 核心配置 (`config/config.json`)

| 参数 | 说明 | 默认值 | 必须修改 |
|------|------|--------|----------|
| `server.domain` | 访问域名/IP | `http://localhost` | ✅ |
| `server.port` | 服务端口 | `8000` | ❌ |
| `security.secret_key` | 32位安全密钥 | 模板值 | ✅ |
| `users[0].username` | 用户名 | `admin` | ✅ |
| `users[0].password` | 密码 | 模板值 | ✅ |

### 可选配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `security.upload.max_file_size_mb` | 最大文件大小(MB) | `10` |
| `security.upload.allowed_types` | 允许的文件类型 | 图片格式 |
| `cleanup.expire_days` | 图片过期天数 | `30` |
| `cleanup.enable` | 是否自动清理 | `true` |

---

## 🔧 常用工具

### 🔑 密钥生成工具
```bash
# 生成新密钥
python tools/generate_secret_key.py

# 直接更新配置文件
python tools/generate_secret_key.py --config config/config.json --username myuser --password

# 生成环境变量格式
python tools/generate_secret_key.py --env
```

### 🧪 服务测试工具
```bash
# 完整测试
python tools/test_service.py

# 快速测试
python tools/test_service.py --quick

# 指定配置文件
python tools/test_service.py --config /path/to/config.json
```

### 📊 健康检查
```bash
# API健康检查
curl "http://your-domain.com/health"

# 系统统计
curl "http://your-domain.com/stats?username=admin&password=your-password"
```

---

## 🌐 第三方集成示例

### Python项目集成

**1. 复制简化客户端**
```bash
# 将客户端文件复制到您的项目
cp client/image_proxy_simple.py /path/to/your/project/
```

**2. 快速使用**
```python
from image_proxy_simple import setup_image_proxy, upload_image

# 一次性配置
setup_image_proxy(
    server_url="http://your-domain.com",
    username="admin", 
    password="your-password"
)

# 使用
image_url = upload_image("photo.jpg")
print(f"图片链接: {image_url}")
```

**3. 批量上传**
```python
from image_proxy_simple import SimpleImageProxy

with SimpleImageProxy("http://your-domain.com", "admin", "password") as client:
    for image_file in ["img1.jpg", "img2.png", "img3.gif"]:
        url = client.upload_image(image_file)
        if url:
            print(f"{image_file} -> {url}")
```

### Web项目集成

**Flask示例:**
```python
from flask import Flask, request, jsonify
from image_proxy_simple import upload_image, setup_image_proxy

app = Flask(__name__)
setup_image_proxy("http://your-domain.com", "admin", "password")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    file.save(f"temp_{file.filename}")
    
    url = upload_image(f"temp_{file.filename}")
    return jsonify({'url': url})
```

### 命令行工具

**快速上传脚本:**
```bash
#!/bin/bash
# quick_upload.sh

if [ $# -eq 0 ]; then
    echo "用法: $0 <image_file>"
    exit 1
fi

curl -X POST "http://your-domain.com/upload?username=admin&password=your-password" \
  -F "file=@$1" \
  -s | jq -r '.url'
```

---

## 🐛 故障排除

### 常见问题

**1. 服务启动失败**
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 检查配置文件
python -c "import json; json.load(open('config/config.json'))"
```

**2. 上传失败**
- 检查文件大小是否超限（默认10MB）
- 检查文件类型是否支持
- 检查用户名密码是否正确

**3. 图片访问失败**
- 检查token是否过期
- 检查网络连接
- 检查服务器磁盘空间

### 日志查看

**开发环境:**
```bash
# 查看控制台输出
cd server && python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

**生产环境:**
```bash
# 查看systemd日志
sudo journalctl -u image-proxy -f

# 查看应用日志
tail -f /var/log/image_proxy/fastapi.log
```

### 重置配置

**重新生成密钥:**
```bash
python tools/generate_secret_key.py --config config/config.json --username admin --password
```

**重置数据库:**
```bash
# 删除数据库和上传文件
rm -f server/images.db
rm -rf server/uploads/*
```

---

## 📈 性能优化

### 基础优化

**1. 调整worker数量:**
```bash
# 生产环境建议
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

**2. 配置Nginx代理:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**3. 启用缓存:**
```python
# 客户端使用缓存
from client.client import ImageProxyClient

client = ImageProxyClient(enable_cache=True)
url = client.get_image_url("image.jpg", use_cache=True)
```

### 监控设置

**系统监控:**
```bash
# 内存使用
ps aux | grep uvicorn

# 磁盘空间
df -h server/uploads/

# 数据库大小
ls -lh server/images.db
```

---

## 🛡️ 安全建议

1. **生产环境必须使用HTTPS**
2. **定期更换密钥和密码**
3. **限制上传文件大小和类型**
4. **设置防火墙规则**
5. **定期备份数据**

---

## 🎉 完成！

恭喜！您已经成功部署了Image Proxy Project。现在可以：

- ✅ 上传图片获取URL
- ✅ 集成到您的项目中
- ✅ 享受高性能图片代理服务

如有问题，请查看：
- 📖 [完整文档](README.md)
- 🔧 [API文档](docs/API.md)
- 🚀 [部署指南](docs/DEPLOYMENT.md)

**需要帮助？** 创建 [Issue](../../issues/new) 获取支持！