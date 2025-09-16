#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
VENV_DIR="$APP_DIR/venv"
SERVICE_FILE="/etc/systemd/system/fastapi.service"
CLEANUP_SERVICE="/etc/systemd/system/fastapi-cleanup.service"
TIMER_FILE="/etc/systemd/system/fastapi-cleanup.timer"
LOG_DIR="/var/log/image_proxy"
DB_FILE="$APP_DIR/server/images.db"
UPLOAD_DIR="$APP_DIR/server/uploads"
SERVICE_NAME="fastapi"

echo "==> Uninstall Image Proxy Project"

# 1. 停止并禁用 systemd 服务
echo "1. 停止并禁用 systemd 服务"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    sudo systemctl stop "$SERVICE_NAME"
fi
sudo systemctl disable "$SERVICE_NAME" || true

if [ -f "$TIMER_FILE" ] && systemctl is-active --quiet fastapi-cleanup.timer; then
    sudo systemctl stop fastapi-cleanup.timer
    sudo systemctl disable fastapi-cleanup.timer || true
fi

if [ -f "$CLEANUP_SERVICE" ] && systemctl is-active --quiet fastapi-cleanup; then
    sudo systemctl stop fastapi-cleanup
    sudo systemctl disable fastapi-cleanup || true
fi

# 2. 删除 systemd 配置文件
echo "2. 删除 systemd 配置文件"
sudo rm -f "$SERVICE_FILE" "$CLEANUP_SERVICE" "$TIMER_FILE"
sudo systemctl daemon-reload

# 3. 删除虚拟环境
if [ -d "$VENV_DIR" ]; then
    echo "3. 删除虚拟环境"
    rm -rf "$VENV_DIR"
fi

# 4. 删除数据库和上传目录（保留配置）
echo "4. 删除数据库文件"
rm -f "$DB_FILE"

if [ -d "$UPLOAD_DIR" ]; then
    echo "   - 删除上传目录内容"
    rm -rf "$UPLOAD_DIR"/*
else
    echo "   - 上传目录不存在，跳过"
fi

# 5. 删除日志目录
if [ -d "$LOG_DIR" ]; then
    echo "5. 删除日志目录 /var/log/image_proxy"
    sudo rm -rf "$LOG_DIR"
fi

echo "✅ 卸载完成！"
echo "⚠️ 注意：config/config.json 已保留，如需彻底删除，请手动移除。"
