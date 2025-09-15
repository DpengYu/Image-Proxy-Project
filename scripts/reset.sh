#!/bin/bash
set -e

APP_DIR="$(cd $(dirname $0)/.. && pwd)"
DB_FILE="$APP_DIR/server/images.db"
UPLOAD_DIR="$APP_DIR/server/uploads"

echo "1. 停止 FastAPI 服务"
if systemctl is-active --quiet fastapi; then
    sudo systemctl stop fastapi
fi

echo "2. 删除数据库文件"
if [ -f "$DB_FILE" ]; then
    rm -f "$DB_FILE"
    echo "   - 数据库 images.db 已删除"
fi

echo "3. 清空上传目录"
if [ -d "$UPLOAD_DIR" ]; then
    rm -rf "$UPLOAD_DIR/*"
    echo "   - 上传目录 uploads 已清空"
else
    mkdir -p "$UPLOAD_DIR"
    echo "   - 上传目录 uploads 已创建"
fi

echo "4. 重新创建空上传目录"
mkdir -p "$UPLOAD_DIR"

echo "5. 重启 FastAPI 服务"
sudo systemctl start fastapi

echo "✅ 重置完成！数据库和上传缓存已清空。"
