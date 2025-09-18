#!/bin/bash
set -e

echo "==> Image Proxy Project 一键启动脚本"

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_FILE="$APP_DIR/config/config.json"
SERVICE_NAME="fastapi"

# 检查配置文件
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    echo "请先运行安装脚本: sudo ./install.sh"
    exit 1
fi

# 检查服务是否已安装
if ! systemctl list-unit-files | grep -q "^$SERVICE_NAME.service"; then
    echo "❌ FastAPI 服务未安装"
    echo "请先运行安装脚本: sudo ./install.sh"
    exit 1
fi

echo "🚀 启动 Image Proxy Project 服务..."

# 启动 FastAPI 服务
echo "[1/3] 启动 FastAPI 服务"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "  ✅ FastAPI 服务已在运行"
else
    sudo systemctl start "$SERVICE_NAME"
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "  ✅ FastAPI 服务启动成功"
    else
        echo "  ❌ FastAPI 服务启动失败"
        echo "查看日志: journalctl -u fastapi --no-pager -n 20"
        exit 1
    fi
fi

# 启动清理定时任务
echo "[2/3] 启动清理定时任务"
if systemctl is-active --quiet fastapi-cleanup.timer; then
    echo "  ✅ 清理定时任务已在运行"
else
    if sudo systemctl start fastapi-cleanup.timer 2>/dev/null; then
        echo "  ✅ 清理定时任务启动成功"
    else
        echo "  ⚠️ 清理定时任务启动失败（非致命错误）"
    fi
fi

# 验证服务状态
echo "[3/3] 验证服务状态"
PORT=$(jq -r '.server.port' "$CONFIG_FILE" 2>/dev/null || echo "8000")
DOMAIN=$(jq -r '.server.domain' "$CONFIG_FILE" 2>/dev/null | sed 's~https\?://~~' | sed 's:/*$::' || echo "localhost")

# 等待服务完全启动
sleep 3

# 测试本地访问
LOCAL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/docs" 2>/dev/null || echo "000")

echo ""
echo "📊 服务状态检查："
echo "  FastAPI 服务: $(systemctl is-active fastapi)"
echo "  清理定时任务: $(systemctl is-active fastapi-cleanup.timer 2>/dev/null || echo "inactive")"
echo "  本地访问 (127.0.0.1:$PORT): $LOCAL_STATUS"

if [ "$LOCAL_STATUS" = "200" ]; then
    echo "  ✅ 服务运行正常"
else
    echo "  ❌ 服务可能有问题，状态码: $LOCAL_STATUS"
fi

echo ""
echo "🎉 Image Proxy Project 启动完成！"
echo ""
echo "🔗 快速链接:"
echo "  • API文档: http://$DOMAIN/docs"
echo "  • 本地访问: http://127.0.0.1:$PORT/docs"
echo "  • 系统统计: http://$DOMAIN/stats"
echo ""
echo "🛠️ 管理命令:"
echo "  • 查看状态: systemctl status fastapi"
echo "  • 查看日志: journalctl -u fastapi --no-pager -f"
echo "  • 停止服务: sudo systemctl stop fastapi"
echo "  • 重启服务: sudo systemctl restart fastapi"
echo ""
echo "🧪 测试命令:"
echo "  • 服务测试: python tools/test_service.py"
echo "  • 客户端测试: python client/client.py <图片路径>"
echo "  • 第三方集成: python demo_integration.py"

if [ "$LOCAL_STATUS" != "200" ]; then
    echo ""
    echo "⚠️ 服务启动可能有问题，建议检查："
    echo "  1. 查看详细日志: journalctl -u fastapi --no-pager -n 50"
    echo "  2. 检查端口占用: netstat -tlnp | grep :$PORT"
    echo "  3. 验证配置文件: jq . $CONFIG_FILE"
    echo "  4. 重新安装服务: sudo ./install.sh"
fi