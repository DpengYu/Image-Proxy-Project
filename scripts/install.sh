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

# 安装依赖
$VENV_PY -m pip install --upgrade pip
$VENV_PY -m pip install fastapi uvicorn python-multipart requests

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

echo "4. 配置 systemd 服务"

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

echo "5. 重新加载 systemd 并启动服务"
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable fastapi.service fastapi-cleanup.timer
sudo systemctl restart fastapi.service fastapi-cleanup.timer

echo "6. 测试 FastAPI 是否可访问 /docs"
sleep 5
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT/docs || echo "000")
if [ "$STATUS" -eq 200 ]; then
  echo "✅ FastAPI /docs 访问成功！安装完成。"
else
  echo "[WARN] FastAPI /docs 访问失败！HTTP 状态码：$STATUS"
  echo "可能原因："
  echo "  - FastAPI 未正常启动"
  echo "  - 防火墙或端口未开放 ($PORT)"
  echo "  - 依赖未安装完整 (fastapi, uvicorn, python-multipart)"
  echo "请检查日志： sudo journalctl -u fastapi -f"
fi
