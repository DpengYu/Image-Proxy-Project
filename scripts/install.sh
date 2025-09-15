#!/bin/bash
set -e

APP_DIR="$(cd $(dirname $0)/.. && pwd)"
PYTHON=$(which python3)
VENV_DIR="$APP_DIR/venv"

CONFIG_FILE="$APP_DIR/config/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 请先创建 config.json 文件！"
    exit 1
fi

# 检查 jq 是否安装
if ! command -v jq &>/dev/null; then
    echo "❌ 依赖 jq 未安装，请先执行: sudo apt install -y jq"
    exit 1
fi

echo "1. 创建虚拟环境并安装依赖"
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install fastapi uvicorn requests

echo "2. 创建日志目录"
sudo mkdir -p /var/log/image_proxy
LOG_FILE="/var/log/image_proxy/fastapi.log"
sudo touch "$LOG_FILE"
sudo chown $(whoami):$(whoami) "$LOG_FILE"

echo "3. 读取配置"
DOMAIN=$(jq -r '.server.domain' "$CONFIG_FILE")
PORT=$(jq -r '.server.port' "$CONFIG_FILE")
CLEANUP_ENABLE=$(jq -r '.cleanup.enable' "$CONFIG_FILE")
CLEANUP_TIME=$(jq -r '.cleanup.cleanup_time' "$CONFIG_FILE")

echo "4. 配置 systemd 服务"
SERVICE_FILE="/etc/systemd/system/fastapi.service"
CLEANUP_SERVICE="/etc/systemd/system/fastapi-cleanup.service"
TIMER_FILE="/etc/systemd/system/fastapi-cleanup.timer"

# 主服务
cat <<EOF | sudo tee $SERVICE_FILE >/dev/null
[Unit]
Description=FastAPI + Uvicorn Service
After=network.target

[Service]
WorkingDirectory=$APP_DIR/server
ExecStart=$VENV_DIR/bin/python -m uvicorn server:app --host 0.0.0.0 --port $PORT
Restart=always
RestartSec=5
User=$(whoami)
Group=$(whoami)
StandardOutput=file:$LOG_FILE
StandardError=file:$LOG_FILE

[Install]
WantedBy=multi-user.target
EOF

# 清理任务
if [ "$CLEANUP_ENABLE" = "true" ]; then
    cat <<EOF | sudo tee $CLEANUP_SERVICE >/dev/null
[Unit]
Description=FastAPI Cleanup Service
After=fastapi.service

[Service]
WorkingDirectory=$APP_DIR/server
ExecStart=$VENV_DIR/bin/python $APP_DIR/server/cleanup.py
User=$(whoami)
Group=$(whoami)
EOF

    cat <<EOF | sudo tee $TIMER_FILE >/dev/null
[Unit]
Description=Run FastAPI Cleanup Daily

[Timer]
OnCalendar=$CLEANUP_TIME
Persistent=true

[Install]
WantedBy=timers.target
EOF
fi

echo "5. 重新加载 systemd"
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl restart fastapi

if [ "$CLEANUP_ENABLE" = "true" ]; then
    sudo systemctl enable fastapi-cleanup.timer
    sudo systemctl restart fastapi-cleanup.timer
fi

echo "✅ 安装完成！FastAPI 已启动，清理任务已配置。"
