# 部署指南

## 系统要求

### 硬件要求
- **CPU**: 2核心以上
- **内存**: 2GB以上
- **存储**: 10GB以上可用空间
- **网络**: 稳定的网络连接

### 软件要求
- **操作系统**: Linux (Ubuntu 18.04+ / CentOS 7+)
- **Python**: 3.10或更高版本
- **系统服务**: systemd
- **工具**: jq, nginx (可选)

## 快速部署

### 1. 获取代码
```bash
git clone <your-repo-url>
cd image_proxy_project
```

### 2. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt
```

### 3. 配置服务
```bash
# 复制配置模板
cp config/config.template.json config/config.json

# 编辑配置
vim config/config.json
```

**重要配置项**:
- `server.domain`: 设置为您的域名或IP
- `server.port`: 设置服务端口
- `security.secret_key`: **必须**设置为随机32位字符串
- `users`: 配置用户名和密码

### 4. 自动化部署
```bash
cd scripts
chmod +x install.sh
sudo ./install.sh
```

## 手动部署

### 1. 安装依赖
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装系统依赖
sudo apt install -y python3 python3-pip python3-venv nginx jq

# 安装Python依赖
pip install -r requirements-prod.txt
```

### 2. 配置文件
创建并编辑配置文件：
```json
{
  "server": {
    "domain": "https://your-domain.com",
    "port": 8000
  },
  "security": {
    "secret_key": "your-32-character-secret-key-here",
    "upload": {
      "max_file_size_mb": 10,
      "allowed_types": ["image/jpeg", "image/png", "image/gif", "image/webp"]
    }
  },
  "users": [
    {
      "username": "admin",
      "password": "your-strong-password"
    }
  ]
}
```

### 3. 创建系统服务
创建 `/etc/systemd/system/image-proxy.service`:
```ini
[Unit]
Description=Image Proxy API Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/image_proxy_project/server
ExecStart=/path/to/image_proxy_project/venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 4. 配置Nginx反向代理
创建 `/etc/nginx/sites-available/image-proxy`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL配置
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # 上传限制
    client_max_body_size 10M;
    
    # API代理
    location /upload {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }
    
    location /secure_get {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location ~ ^/(info|stats|download_db|health) {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. 启动服务
```bash
# 启用Nginx配置
sudo ln -s /etc/nginx/sites-available/image-proxy /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable image-proxy
sudo systemctl start image-proxy

# 检查状态
sudo systemctl status image-proxy
```

## Docker部署

### 1. 创建Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# 复制应用代码
COPY server/ ./server/
COPY config/ ./config/

# 创建上传目录
RUN mkdir -p server/uploads

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "server.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 创建docker-compose.yml
```yaml
version: '3.8'

services:
  image-proxy:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config:ro
      - ./data/uploads:/app/server/uploads
      - ./data/db:/app/server
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - SERVER_DOMAIN=${SERVER_DOMAIN}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - image-proxy
    restart: unless-stopped
```

### 3. 部署
```bash
# 设置环境变量
echo "SECRET_KEY=your-32-character-secret-key-here" > .env
echo "SERVER_DOMAIN=https://your-domain.com" >> .env

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 环境变量配置

可以通过环境变量覆盖配置文件：

```bash
# 服务器配置
export SERVER_DOMAIN="https://your-domain.com"
export SERVER_PORT=8000

# 安全配置
export SECRET_KEY="your-32-character-secret-key-here"
export MAX_FILE_SIZE_MB=10

# 用户配置
export DEFAULT_USERNAME="admin"
export DEFAULT_PASSWORD="your-password"

# 清理配置
export CLEANUP_ENABLE=true
export CLEANUP_EXPIRE_DAYS=30
export CLEANUP_TIME="03:00:00"

# 日志配置
export LOG_LEVEL="INFO"
export LOG_FILE="/var/log/image_proxy/app.log"
```

## 监控和维护

### 1. 查看日志
```bash
# 服务日志
sudo journalctl -u image-proxy -f

# Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 应用日志
sudo tail -f /var/log/image_proxy/fastapi.log
```

### 2. 健康检查
```bash
# 检查API状态
curl http://localhost:8000/health

# 检查系统统计
curl "http://localhost:8000/stats?username=admin&password=password"
```

### 3. 数据备份
```bash
# 备份数据库
cp server/images.db backup/images_$(date +%Y%m%d_%H%M%S).db

# 备份上传文件
tar -czf backup/uploads_$(date +%Y%m%d_%H%M%S).tar.gz server/uploads/

# 备份配置
cp config/config.json backup/config_$(date +%Y%m%d_%H%M%S).json
```

### 4. 清理磁盘空间
```bash
# 手动清理过期文件
cd server && python cleanup.py

# 清理日志
sudo logrotate -f /etc/logrotate.d/image-proxy
```

## 性能优化

### 1. 调整worker数量
```bash
# 在systemd服务中设置
ExecStart=/path/to/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. 数据库优化
```sql
-- 为大型数据库创建更多索引
CREATE INDEX idx_images_created_at ON images(created_at);
CREATE INDEX idx_images_access_count ON images(access_count);
CREATE INDEX idx_images_file_size ON images(file_size);
```

### 3. 缓存优化
在Nginx中添加静态文件缓存：
```nginx
location /secure_get {
    proxy_pass http://127.0.0.1:8000;
    proxy_cache_valid 200 1h;
    add_header X-Cache-Status $upstream_cache_status;
}
```

## 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 检查配置文件
   python -c "import json; json.load(open('config/config.json'))"
   
   # 检查端口占用
   sudo netstat -tlnp | grep :8000
   ```

2. **文件上传失败**
   - 检查文件大小限制
   - 检查目录权限
   - 检查磁盘空间

3. **数据库错误**
   ```bash
   # 检查数据库文件权限
   ls -la server/images.db
   
   # 重新初始化数据库
   rm server/images.db
   python server/database.py
   ```

4. **Nginx代理错误**
   ```bash
   # 测试配置
   sudo nginx -t
   
   # 检查upstream
   curl -I http://127.0.0.1:8000/health
   ```

### 日志分析
```bash
# 查看错误日志
sudo journalctl -u image-proxy --since "1 hour ago" | grep ERROR

# 统计访问量
grep "POST /upload" /var/log/nginx/access.log | wc -l

# 监控内存使用
ps aux | grep uvicorn
```

## 安全加固

### 1. 防火墙配置
```bash
# 只开放必要端口
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 2. 限制文件权限
```bash
# 设置合适的文件权限
chmod 600 config/config.json
chmod 755 server/uploads/
chown -R www-data:www-data server/
```

### 3. 定期更新
```bash
# 更新系统包
sudo apt update && sudo apt upgrade

# 更新Python依赖
pip install -r requirements-prod.txt --upgrade
```