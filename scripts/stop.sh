#!/bin/bash
set -e

echo "==> Image Proxy Project 服务停止脚本"

SERVICE_NAME="fastapi"

echo "🛑 停止 Image Proxy Project 服务..."

# 停止 FastAPI 服务
echo "[1/2] 停止 FastAPI 服务"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    sudo systemctl stop "$SERVICE_NAME"
    echo "  ✅ FastAPI 服务已停止"
else
    echo "  ℹ️ FastAPI 服务未运行"
fi

# 停止清理定时任务
echo "[2/2] 停止清理定时任务"
if systemctl is-active --quiet fastapi-cleanup.timer; then
    sudo systemctl stop fastapi-cleanup.timer
    echo "  ✅ 清理定时任务已停止"
else
    echo "  ℹ️ 清理定时任务未运行"
fi

echo ""
echo "📊 服务状态检查："
echo "  FastAPI 服务: $(systemctl is-active fastapi)"
echo "  清理定时任务: $(systemctl is-active fastapi-cleanup.timer 2>/dev/null || echo "inactive")"

echo ""
echo "✅ Image Proxy Project 服务已停止"
echo ""
echo "🔄 重新启动方法："
echo "  • 启动服务: sudo ./start.sh"
echo "  • 手动启动: sudo systemctl start fastapi"
echo "  • 完全重启: sudo systemctl restart fastapi"