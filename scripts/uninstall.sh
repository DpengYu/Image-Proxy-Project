#!/bin/bash
set -e

APP_DIR="$(cd $(dirname $0)/.. && pwd)"
VENV_DIR="$APP_DIR/venv"
SERVICE_FILE="/etc/systemd/system/fastapi.service"
CLEANUP_SERVICE="/etc/systemd/system/fastapi-cleanup.service"
TIMER_FILE="/etc/systemd/system/fastapi-cleanup.timer"
LOG_DIR="/var/log/image_proxy"
DB_FILE="$APP_DIR/server/images.db"
UPLOAD_DIR="$APP_DIR/server/uploads"

echo "1. 停止并禁用 systemd 服务"
if systemctl is-active --quiet fastapi; then
    sudo systemctl stop fastapi
fi
sudo systemctl disable fastapi || true

if [ -f "$TIMER_FILE" ]; then
    if systemctl is-active --quiet fastapi-cleanup.timer; then
        sudo systemctl stop fastapi-cleanup.timer
    fi
    sudo systemctl disable fastapi-cleanup.timer || true
fi

if [ -f "$CLEANUP_SERVICE" ]; then
    if systemctl is-active --quiet fastapi-cleanup; then
        sudo systemctl stop fastapi-cleanup
    fi
    sudo systemctl disable fastapi-cleanup || true
fi

echo "2. 删除 systemd 配置文件"
sudo rm -f "$SERVICE_FILE" "$CLEANUP_SERVICE" "$TIMER_FILE"
sudo systemctl daemon-reload

echo "3. 删除虚拟环境"
rm -rf "$VENV_DIR"

echo "4. 删除数据库与上传目录（仅数据，不删除配置文件）"
rm -f "$DB_FILE"
rm -rf "$UPLOAD_DIR"

echo "5. 删除日志文件夹"
sudo rm -rf "$LOG_DIR"

echo "✅ 卸载完成！"
echo "⚠️ 注意：config/config.json 已保留，如需彻底删除，请手动移除。"
