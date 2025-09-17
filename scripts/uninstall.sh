#!/bin/bash
set -e

echo "==> Image Proxy Project 完全卸载脚本"

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$APP_DIR/venv"
SERVICE_FILE="/etc/systemd/system/fastapi.service"
CLEANUP_SERVICE="/etc/systemd/system/fastapi-cleanup.service"
TIMER_FILE="/etc/systemd/system/fastapi-cleanup.timer"
LOG_DIR="/var/log/image_proxy"
DB_FILE="$APP_DIR/server/images.db"
UPLOAD_DIR="$APP_DIR/server/uploads"
CLIENT_CACHE="$APP_DIR/client/image_cache.db"
NGINX_CONF="/etc/nginx/conf.d/image-proxy.conf"
SERVICE_NAME="fastapi"

echo "⚠️  此操作将完全卸载 Image Proxy Project！"
echo "将删除："
echo "  - systemd 服务和定时任务"
echo "  - 虚拟环境: $VENV_DIR"
echo "  - 数据库和上传文件"
echo "  - 日志文件: $LOG_DIR"
echo "  - Nginx 配置文件 (如果存在)"
echo "保留："
echo "  - 项目代码和配置文件"
read -p "是否继续？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 0
fi

echo ""
echo "开始卸载..."

# 1. 停止并禁用 systemd 服务
echo "[1/7] 停止并禁用 systemd 服务"
service_stopped=0

if systemctl is-active --quiet "$SERVICE_NAME"; then
    sudo systemctl stop "$SERVICE_NAME"
    echo "  ✅ 已停止 FastAPI 服务"
    service_stopped=1
fi

if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    sudo systemctl disable "$SERVICE_NAME"
    echo "  ✅ 已禁用 FastAPI 服务"
fi

if [ -f "$TIMER_FILE" ] && systemctl is-active --quiet fastapi-cleanup.timer; then
    sudo systemctl stop fastapi-cleanup.timer
    echo "  ✅ 已停止定时清理任务"
fi

if [ -f "$TIMER_FILE" ] && systemctl is-enabled --quiet fastapi-cleanup.timer 2>/dev/null; then
    sudo systemctl disable fastapi-cleanup.timer
    echo "  ✅ 已禁用定时清理任务"
fi

if [ -f "$CLEANUP_SERVICE" ] && systemctl is-active --quiet fastapi-cleanup; then
    sudo systemctl stop fastapi-cleanup
    echo "  ✅ 已停止清理服务"
fi

# 2. 删除 systemd 配置文件
echo "[2/7] 删除 systemd 配置文件"
files_removed=0
for file in "$SERVICE_FILE" "$CLEANUP_SERVICE" "$TIMER_FILE"; do
    if [ -f "$file" ]; then
        sudo rm -f "$file"
        echo "  ✅ 已删除: $(basename "$file")"
        files_removed=$((files_removed + 1))
    fi
done

if [ $files_removed -gt 0 ]; then
    sudo systemctl daemon-reload
    echo "  ✅ 已重新加载 systemd 配置"
else
    echo "  ⚠️ 未发现 systemd 配置文件"
fi

# 3. 删除虚拟环境
echo "[3/7] 删除虚拟环境"
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    echo "  ✅ 虚拟环境已删除: $VENV_DIR"
else
    echo "  ⚠️ 虚拟环境不存在，跳过"
fi

# 4. 删除数据库和上传目录
echo "[4/7] 删除数据库和文件"
files_removed=0

if [ -f "$DB_FILE" ]; then
    rm -f "$DB_FILE"
    echo "  ✅ 服务器数据库已删除"
    files_removed=$((files_removed + 1))
fi

if [ -f "$CLIENT_CACHE" ]; then
    rm -f "$CLIENT_CACHE"
    echo "  ✅ 客户端缓存已删除"
    files_removed=$((files_removed + 1))
fi

if [ -d "$UPLOAD_DIR" ]; then
    file_count=$(find "$UPLOAD_DIR" -type f 2>/dev/null | wc -l || echo "0")
    rm -rf "$UPLOAD_DIR"
    echo "  ✅ 上传目录已删除，包含 $file_count 个文件"
    files_removed=$((files_removed + 1))
fi

if [ $files_removed -eq 0 ]; then
    echo "  ⚠️ 未发现数据文件"
fi

# 5. 删除日志目录
echo "[5/7] 删除日志目录"
if [ -d "$LOG_DIR" ]; then
    sudo rm -rf "$LOG_DIR"
    echo "  ✅ 日志目录已删除: $LOG_DIR"
else
    echo "  ⚠️ 日志目录不存在，跳过"
fi

# 6. 删除 Nginx 配置
echo "[6/7] 检查 Nginx 配置"
nginx_updated=0

if [ -f "$NGINX_CONF" ]; then
    sudo rm -f "$NGINX_CONF"
    echo "  ✅ 独立 Nginx 配置已删除: $NGINX_CONF"
    nginx_updated=1
fi

# 检查宝塔配置
BT_CONF_PATTERN="/www/server/panel/vhost/nginx/*.conf"
for bt_conf in $BT_CONF_PATTERN; do
    if [ -f "$bt_conf" ] && grep -q "image-proxy\|fastapi" "$bt_conf" 2>/dev/null; then
        echo "  ⚠️ 发现宝塔配置可能包含代理设置: $bt_conf"
        echo "     请手动检查并清理相关配置"
        nginx_updated=1
        break
    fi
done

if [ $nginx_updated -eq 1 ]; then
    if sudo nginx -t 2>/dev/null; then
        sudo systemctl reload nginx
        echo "  ✅ Nginx 配置已重新加载"
    else
        echo "  ⚠️ Nginx 配置测试失败，请手动检查"
    fi
else
    echo "  ℹ️ 未发现相关 Nginx 配置"
fi

# 7. 验证卸载结果
echo "[7/7] 验证卸载结果"
echo ""
echo "🔍 卸载验证："

# 检查服务状态
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "  ❌ FastAPI 服务仍在运行"
else
    echo "  ✅ FastAPI 服务已停止"
fi

# 检查文件
remaining_files=0
for file in "$SERVICE_FILE" "$CLEANUP_SERVICE" "$TIMER_FILE" "$DB_FILE" "$CLIENT_CACHE" "$NGINX_CONF"; do
    if [ -f "$file" ]; then
        echo "  ❌ 文件仍存在: $file"
        remaining_files=$((remaining_files + 1))
    fi
done

for dir in "$VENV_DIR" "$UPLOAD_DIR" "$LOG_DIR"; do
    if [ -d "$dir" ]; then
        echo "  ❌ 目录仍存在: $dir"
        remaining_files=$((remaining_files + 1))
    fi
done

if [ $remaining_files -eq 0 ]; then
    echo "  ✅ 所有相关文件和目录已清理"
fi

echo ""
echo "🎉 Image Proxy Project 卸载完成！"
echo ""
echo "📋 卸载总结："
echo "  ✅ systemd 服务已移除"
echo "  ✅ 虚拟环境已删除"
echo "  ✅ 数据文件已清理"
echo "  ✅ 日志文件已删除"
if [ $nginx_updated -eq 1 ]; then
    echo "  ✅ Nginx 配置已处理"
fi
echo ""
echo "💡 注意事项："
echo "  • 项目源代码已保留在: $APP_DIR"
echo "  • config/config.json 配置文件已保留"
echo "  • 如需完全删除，请手动删除项目目录"
echo ""
echo "🔄 重新安装方法："
echo "  cd $(basename "$APP_DIR")/scripts && sudo ./install.sh"
