#!/bin/bash

APP_DIR="$(cd $(dirname $0)/.. && pwd)"
PYTHON=$(which python3)

# 优先使用 venv
if [ -f "$APP_DIR/venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$APP_DIR/venv/bin/activate"
    PYTHON="$APP_DIR/venv/bin/python"
fi

CONFIG_FILE="$APP_DIR/config/config.json"
if [ ! -f $CONFIG_FILE ]; then
    echo "请先创建 config.json 文件！"
    exit 1
fi

echo "1. 安装依赖"
$PYTHON -m pip install --upgrade pip
$PYTHON -m pip install fastapi uvicorn requests python-multipart jq

echo "2. 创建日志目录"
mkdir -p /var/log/image_proxy
LOG_FILE="/var/log/image_proxy/fastapi.log"
touch $LOG_FILE

echo "3. 读取配置"
DOMAIN=$(jq -r '.server.domain' $CONFIG_FILE)
PORT=$(jq -r '.server.port' $CONFIG_FILE)
CLEANUP_ENABLE=$(jq -r '.cleanup.enable' $CONFIG_FILE)
CLEANUP_TIME=$(jq -r '.cleanup.cleanup_time' $CONFIG_FILE)

echo "4. 配置 systemd 服务"
SERVICE_FILE="/etc/systemd/system/fastapi.service"
TIMER_FILE="/etc/systemd/system/fastapi-cleanup.timer"
CLEANUP_SERVICE="/etc/systemd/system/fastapi-cleanup.service"

cat <<EOF | sudo tee $SERVICE_FILE
[Unit]
Description=FastAPI + Uvicorn Service
After=network.target

[Service]
WorkingDirectory=$APP_DIR/server
ExecStart=$PYTHON -m uvicorn server:app --host 0.0.0.0 --port $PORT
Restart=always
RestartSec=5
User=$(whoami)
Group=$(whoami)
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE

[Install]
WantedBy=multi-user.target
EOF

if [ "$CLEANUP_ENABLE" = "true" ]; then
    cat <<EOF | sudo tee $CLEANUP_SERVICE
[Unit]
Description=FastAPI Cleanup Service
After=fastapi.service

[Service]
WorkingDirectory=$APP_DIR/server
ExecStart=$PYTHON cleanup.py
User=$(whoami)
Group=$(whoami)
EOF

    cat <<EOF | sudo tee $TIMER_FILE
[Unit]
Description=Run FastAPI Cleanup Daily

[Timer]
OnCalendar=$CLEANUP_TIME
Persistent=true

[Install]
WantedBy=timers.target
EOF
fi

echo "5. 重新加载 systemd 并启动服务"
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi

# 检查 fastapi 服务是否成功启动
if ! systemctl is-active --quiet fastapi; then
    echo "[ERROR] fastapi.service 启动失败！打印最近 50 条日志："
    sudo journalctl -u fastapi -n 50 --no-pager
    exit 1
fi

if [ "$CLEANUP_ENABLE" = "true" ]; then
    sudo systemctl enable fastapi-cleanup.timer
    sudo systemctl start fastapi-cleanup.timer

    # 检查定时器状态
    if ! systemctl is-active --quiet fastapi-cleanup.timer; then
        echo "[WARN] fastapi-cleanup.timer 启动失败！请检查配置时间：$CLEANUP_TIME"
        sudo systemctl status fastapi-cleanup.timer
    fi
fi

echo "6. 测试 FastAPI 是否可访问 /docs"
if command -v curl >/dev/null 2>&1; then
    HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" http://$DOMAIN:$PORT/docs || echo "000")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "✅ FastAPI /docs 可访问： http://$DOMAIN:$PORT/docs"
    else
        echo "[WARN] FastAPI /docs 访问失败！HTTP 状态码：$HTTP_STATUS"
        echo "可能原因："
        echo "  - FastAPI 未正常启动"
        echo "  - 防火墙或端口未开放"
        echo "  - 依赖未安装完整 (fastapi, uvicorn, python-multipart)"
        echo "请检查日志： sudo journalctl -u fastapi -f"
    fi
else
    echo "[INFO] curl 未安装，无法自动测试 /docs，请手动访问 http://$DOMAIN:$PORT/docs"
fi

echo "✅ 安装完成！FastAPI 已启动，清理任务已配置。"
