#!/bin/bash
set -e

echo "1. 检查并安装依赖"

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PY="$PROJECT_DIR/venv/bin/python"

if [ ! -x "$VENV_PY" ]; then
  echo "[ERROR] 没有找到虚拟环境 Python: $VENV_PY"
  echo "请先运行: python3 -m venv $PROJECT_DIR/venv && source $PROJECT_DIR/venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

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

# 清洗域名，去掉 http:// 或 /
DOMAIN=$(jq -r '.server.domain' "$CONFIG_FILE" | sed 's~https\?://~~' | sed 's~/~~g')
PORT=$(jq -r '.server.port' "$CONFIG_FILE")
CLEANUP_TIME=$(jq -r '.cleanup.cleanup_time' "$CONFIG_FILE")

echo "[INFO] 域名: $DOMAIN, 端口: $PORT, 清理时间: $CLEANUP_TIME"

echo "4. 检查 Nginx 是否安装"
if ! command -v nginx >/dev/null 2>&1; then
  echo "[INFO] Nginx 未安装，正在自动安装..."
  sudo apt update
  sudo apt install -y nginx openssl
fi
echo "[INFO] Nginx 已安装：$(nginx -v 2>&1)"

echo "5. 配置 systemd 服务"

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

echo "6. 配置 Nginx 反向代理 /docs /upload /get"

DOCS_LOCATION=$(cat <<EOF
    location /docs {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
EOF
)

API_LOCATIONS=$(cat <<EOF
    location /upload {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /get {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
EOF
)

# 宝塔面板目录
BT_CONF="/www/server/panel/vhost/nginx/$DOMAIN.conf"
NGINX_CONF="/etc/nginx/conf.d/fastapi.conf"

if [ -f "$BT_CONF" ]; then
    echo "[INFO] 检测到宝塔面板 server 配置: $BT_CONF"

    for loc in "/docs" "/upload" "/get"; do
        if sudo grep -q "location $loc" "$BT_CONF"; then
            echo "[INFO] $loc location 已存在，更新 proxy_pass"
            sudo sed -i "/location $loc/,/}/ s#proxy_pass .*;#proxy_pass http://127.0.0.1:$PORT;#" "$BT_CONF"
        else
            echo "[INFO] $loc location 不存在，插入新的 location $loc"
            case $loc in
                "/docs") sudo sed -i "/server_name $DOMAIN;/a \\$DOCS_LOCATION" "$BT_CONF" ;;
                "/upload"|"/get") sudo sed -i "/server_name $DOMAIN;/a \\$API_LOCATIONS" "$BT_CONF" ;;
            esac
        fi
    done
else
    echo "[INFO] 未检测到宝塔配置，创建独立 Nginx 配置 $NGINX_CONF"
    sudo tee $NGINX_CONF > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

$DOCS_LOCATION
$API_LOCATIONS
}
EOF
fi

# 处理 HTTPS：检查已有证书，否则生成自签名证书
SSL_DIR="/etc/ssl/$DOMAIN"
SSL_CERT="$SSL_DIR/fullchain.pem"
SSL_KEY="$SSL_DIR/privkey.pem"

if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
    echo "[INFO] 未找到证书，生成自签名证书"
    sudo mkdir -p "$SSL_DIR"
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_KEY" \
        -out "$SSL_CERT" \
        -subj "/CN=$DOMAIN"
fi

# 创建 HTTPS server 块（仅独立 Nginx 配置时添加）
if [ -f "$NGINX_CONF" ]; then
    sudo tee -a $NGINX_CONF > /dev/null <<EOF
server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;

$DOCS_LOCATION
$API_LOCATIONS
}
EOF
fi

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
DOMAIN_SSL_STATUS=$(curl -s -o /dev/null -k -w "%{http_code}" https://$DOMAIN/docs || echo "000")

if [ "$LOCAL_STATUS" -eq 200 ]; then
  echo "✅ FastAPI 本地 /docs 访问成功"
else
  echo "❌ 本地访问失败 (状态码 $LOCAL_STATUS)"
fi

if [ "$DOMAIN_STATUS" -eq 200 ]; then
  echo "✅ 域名 $DOMAIN /docs HTTP 访问成功"
else
  echo "❌ 域名 HTTP 访问失败 (状态码 $DOMAIN_STATUS)"
fi

if [ "$DOMAIN_SSL_STATUS" -eq 200 ]; then
  echo "✅ 域名 $DOMAIN /docs HTTPS 访问成功"
else
  echo "⚠️ 域名 HTTPS 访问失败 (状态码 $DOMAIN_SSL_STATUS)，请检查证书或端口"
fi

echo "安装完成！HTTP + HTTPS 访问 /docs 均可用"
