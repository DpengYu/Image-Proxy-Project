#!/bin/bash
set -e

echo "1. 检查并安装依赖"

# 确定 venv 路径
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PY="$PROJECT_DIR/venv/bin/python"

if [ ! -x "$VENV_PY" ]; then
  echo "[ERROR] 没有找到虚拟环境 Python: $VENV_PY"
  echo "请先运行: python3 -m venv $PROJECT_DIR/venv && source $PROJECT_DIR/venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# 安装 Python 依赖
$VENV_PY -m pip install --upgrade pip
$VENV_PY -m pip install fastapi uvicorn python-multipart requests jq

echo "2. 创建日志目录"
sudo mkdir -p /var/log/image_proxy
sudo touch /var/log/image_proxy/fastapi.log
sudo chown "$USER":"$USER" /var/log/image_proxy/fastapi.log

echo "3. 读取配置"
CONFIG_FILE="$PROJECT_DIR/config/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "[ERROR] 找不到配置文件 $CONFIG_FILE"
  exit 1
fi

DOMAIN=$(jq -r '.server.domain' "$CONFIG_FILE")
PORT=$(jq -r '.server.port' "$CONFIG_FILE")
CLEANUP_TIME=$(jq -r '.cleanup.cleanup_time' "$CONFIG_FILE")

echo "[INFO] 域名: $DOMAIN, 端口: $PORT, 清理时间: $CLEANUP_TIME"

echo "4. 检查 Nginx 是否安装"
if ! command -v nginx >/dev/null 2>&1; then
  echo "[INFO] Nginx 未安装，正在自动安装..."
  sudo apt update
  sudo apt install -y nginx
fi
echo "[INFO] Nginx 已安装：$(nginx -v 2>&1)"

echo "5. 配置 systemd 服务"

# FastAPI 主服务
SERVICE_FILE=/etc/systemd/system/fastapi.service
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=FastAPI + Uvicorn Service
After=network.target

[Service]
WorkingDirectory=$PROJECT_DIR/server
ExecStart=$VENV_PY -m uvicorn server:app --host 0.0.0.0 --port $PORT
Restart=always
RestartSec=5
User=$USER
Group=$USER
StandardOutput=append:/var/log/image_proxy/fastapi.log
StandardError=append:/var/log/image_proxy/fastapi.log

[Install]
WantedBy=multi-user.target
EOF

# 清理任务服务
CLEANUP_SERVICE=/etc/systemd/system/fastapi-cleanup.service
sudo tee $CLEANUP_SERVICE > /dev/null <<EOF
[Unit]
Description=FastAPI Cleanup Service
After=fastapi.service

[Service]
WorkingDirectory=$PROJECT_DIR/server
ExecStart=$VENV_PY cleanup.py
User=$USER
Group=$USER
EOF

# 定时任务
CLEANUP_TIMER=/etc/systemd/system/fastapi-cleanup.timer
sudo tee $CLEANUP_TIMER > /dev/null <<EOF
[Unit]
Description=Run FastAPI Cleanup Daily

[Timer]
OnCalendar=$CLEANUP_TIME
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "6. 配置 Nginx 反向代理 /docs"

# 查找宝塔面板生成的 server 配置
PANEL_CONF=$(sudo nginx -T 2>/dev/null | grep -A5 "server_name $DOMAIN" | grep -oP '/www/server/panel/vhost/nginx/\S+\.conf' | head -n1)

if [ -f "$PANEL_CONF" ]; then
    echo "[INFO] 检测到面板配置：$PANEL_CONF"

    if sudo grep -q "location /docs" "$PANEL_CONF"; then
        echo "[INFO] /docs 已存在，保留原配置，仅更新 proxy_pass"
        sudo sed -i -E "/location \/docs {/,/}/{
            s|proxy_pass http://[^;]+;|proxy_pass http://127.0.0.1:$PORT/;|g
        }" "$PANEL_CONF"
    else
        echo "[INFO] 添加 /docs 反向代理"
        sudo sed -i "/server_name $DOMAIN;/a \\\n    location /docs {\n        proxy_pass http://127.0.0.1:$PORT/;\n        proxy_set_header Host \$host;\n        proxy_set_header X-Real-IP \$remote_addr;\n        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto \$scheme;\n    }" "$PANEL_CONF"
    fi
else
    echo "[INFO] 面板配置未找到，创建 /etc/nginx/conf.d/fastapi.conf"
    NGINX_CONF=/etc/nginx/conf.d/fastapi.conf
    sudo tee $NGINX_CONF > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 100M;

    location /docs {
        proxy_pass http://127.0.0.1:$PORT/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
fi

# 测试 Nginx 配置并重载
sudo nginx -t
sudo systemctl reload nginx

echo "7. 重新加载 systemd 并启动服务"
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable fastapi.service fastapi-cleanup.timer
sudo systemctl restart fastapi.service fastapi-cleanup.timer

echo "8. 测试 FastAPI 是否可访问 /docs"
sleep 5
LOCAL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT/docs || echo "000")
DOMAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/docs || echo "000")

if [ "$LOCAL_STATUS" -eq 200 ]; then
  echo "✅ FastAPI 本地 /docs 访问成功"
else
  echo "❌ 本地访问失败 (状态码 $LOCAL_STATUS)"
fi

if [ "$DOMAIN_STATUS" -eq 200 ]; then
  echo "✅ FastAPI 域名 $DOMAIN/docs 访问成功！安装完成。"
else
  echo "❌ 域名访问失败 (状态码 $DOMAIN_STATUS)"
  echo "可能原因："
  echo "  - Nginx 配置错误或未生效"
  echo "  - 防火墙未开放 80 端口"
  echo "  - FastAPI 服务未正常运行"
  echo "请检查： sudo journalctl -u fastapi -f"
fi
