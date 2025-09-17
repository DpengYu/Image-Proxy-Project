#!/bin/bash
set -e

echo "==> Image Proxy Project 数据重置脚本"

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DB_FILE="$APP_DIR/server/images.db"
UPLOAD_DIR="$APP_DIR/server/uploads"
CLIENT_CACHE="$APP_DIR/client/image_cache.db"
SERVICE_NAME="fastapi"

echo "⚠️  此操作将删除所有上传的图片和数据库记录！"
echo "包括："
echo "  - 服务器数据库: $DB_FILE"
echo "  - 上传文件目录: $UPLOAD_DIR"
echo "  - 客户端缓存: $CLIENT_CACHE"
read -p "是否继续？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 0
fi

echo ""
echo "开始重置数据..."

# 1. 停止 FastAPI 服务
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "[1/5] 停止 FastAPI 服务"
    sudo systemctl stop "$SERVICE_NAME"
    echo "✅ 服务已停止"
else
    echo "[1/5] FastAPI 服务未运行，跳过停止"
fi

# 2. 删除服务器数据库文件
if [ -f "$DB_FILE" ]; then
    echo "[2/5] 删除服务器数据库文件"
    rm -f "$DB_FILE"
    echo "✅ 服务器数据库已删除: $DB_FILE"
else
    echo "[2/5] 服务器数据库文件不存在，跳过"
fi

# 3. 清空上传目录
if [ -d "$UPLOAD_DIR" ]; then
    echo "[3/5] 清空上传目录"
    file_count=$(find "$UPLOAD_DIR" -type f 2>/dev/null | wc -l || echo "0")
    rm -rf "$UPLOAD_DIR"/*
    echo "✅ 已清空上传目录，删除了 $file_count 个文件"
else
    echo "[3/5] 上传目录不存在，创建新目录"
    mkdir -p "$UPLOAD_DIR"
fi

# 4. 删除客户端缓存
if [ -f "$CLIENT_CACHE" ]; then
    echo "[4/5] 删除客户端缓存数据库"
    rm -f "$CLIENT_CACHE"
    echo "✅ 客户端缓存已删除: $CLIENT_CACHE"
else
    echo "[4/5] 客户端缓存文件不存在，跳过"
fi

# 5. 确保目录存在并重启服务
echo "[5/5] 重新创建必要目录并启动服务"
mkdir -p "$UPLOAD_DIR"

if sudo systemctl start "$SERVICE_NAME"; then
    echo "✅ FastAPI 服务已重启"
    # 等待服务启动
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "✅ 服务状态：运行中"
    else
        echo "⚠️ 服务可能启动失败，请检查日志: journalctl -u fastapi --no-pager -n 20"
    fi
else
    echo "❌ FastAPI 服务启动失败"
    echo "请手动检查服务状态: systemctl status fastapi"
fi

echo ""
echo "🎉 数据重置完成！"
echo ""
echo "📊 重置统计："
echo "  ✅ 服务器数据库已清空"
echo "  ✅ 上传文件已删除"
echo "  ✅ 客户端缓存已清空"
echo "  ✅ 服务已重启"
echo ""
echo "💡 下一步操作："
echo "  • 测试服务: python tools/test_service.py"
echo "  • 上传测试: python client/client.py <图片路径>"
echo "  • 查看状态: systemctl status fastapi"
