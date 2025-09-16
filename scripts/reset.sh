#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
DB_FILE="$APP_DIR/server/images.db"
UPLOAD_DIR="$APP_DIR/server/uploads"
SERVICE_NAME="fastapi"

echo "==> Reset FastAPI database and uploads"

# 1. 停止 FastAPI 服务
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "1. 停止 FastAPI 服务"
    sudo systemctl stop "$SERVICE_NAME"
fi

# 2. 删除数据库文件
if [ -f "$DB_FILE" ]; then
    echo "2. 删除数据库文件: images.db"
    rm -f "$DB_FILE"
else
    echo "2. 数据库文件不存在，跳过"
fi

# 3. 清空上传目录
if [ -d "$UPLOAD_DIR" ]; then
    echo "3. 清空上传目录 uploads"
    rm -rf "$UPLOAD_DIR"/*
else
    echo "3. 上传目录不存在，创建 uploads"
    mkdir -p "$UPLOAD_DIR"
fi

# 4. 确保上传目录存在
mkdir -p "$UPLOAD_DIR"

# 5. 重启 FastAPI 服务
echo "4. 重启 FastAPI 服务"
sudo systemctl start "$SERVICE_NAME"

echo "✅ Reset 完成！数据库和上传缓存已清空。"
