#!/bin/bash
set -euo pipefail

echo "==> Image Proxy Project 一键安装脚本"

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
VENV_PY="$VENV_DIR/bin/python"

die(){ echo "[FATAL] $*"; exit 1; }

########################################
# 0. 检查系统要求
########################################
echo "[STEP 0] 检查系统要求"

# 检查操作系统
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
  die "此脚本仅支持Linux系统"
fi

# 检查Python版本
if ! command -v python3 >/dev/null 2>&1; then
  die "未找到python3，请先安装Python 3.10+"
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$PYTHON_VERSION < 3.10" | bc) -eq 1 ]]; then
  die "Python版本过低($PYTHON_VERSION)，需要3.10+"
fi

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
  die "请不要使用root用户运行此脚本"
fi

echo "✅ 系统要求检查通过"

########################################
# 1. 创建/激活虚拟环境
########################################
echo "[STEP 1] 准备Python虚拟环境"

if [ ! -d "$VENV_DIR" ]; then
  echo "创建虚拟环境..."
  python3 -m venv "$VENV_DIR"
fi

if [ ! -x "$VENV_PY" ]; then
  die "虚拟环境创建失败，请检查权限"
fi

echo "✅ 虚拟环境准备完成"

########################################
# 2. 安装/升级 Python 包
########################################
echo "[STEP 2] 安装/升级 Python 包"
"$VENV_PY" -m pip install --upgrade pip setuptools wheel
"$VENV_PY" -m pip install -r "$PROJECT_DIR/requirements.txt"

echo "✅ Python依赖安装完成"

########################################
# 3. 系统工具检查与安装
########################################
echo "[STEP 3] 检查系统命令 (nginx, openssl, jq, systemctl)"
for cmd in nginx openssl jq systemctl; do
  if ! command -v $cmd >/dev/null 2>&1; then
    echo "[INFO] $cmd 未安装，尝试安装"
    if command -v apt >/dev/null 2>&1; then
      sudo apt update && sudo apt install -y $cmd
    elif command -v yum >/dev/null 2>&1; then
      sudo yum install -y $cmd
    else
      die "无法自动安装$cmd，请手动安装"
    fi
  fi
done

echo "✅ 系统工具检查完成"

########################################
# 4. 日志目录和上传目录
########################################
echo "[STEP 4] 创建日志目录和上传目录"
sudo mkdir -p /var/log/image_proxy
sudo touch /var/log/image_proxy/fastapi.log
sudo chown "$USER":"$USER" /var/log/image_proxy/fastapi.log

# 创建上传目录
mkdir -p "$PROJECT_DIR/server/uploads"

echo "✅ 目录创建完成"

########################################
# 5. 检查和验证配置文件
########################################
echo "[STEP 5] 检查配置文件"
CONFIG_FILE="$PROJECT_DIR/config/config.json"
CONFIG_TEMPLATE="$PROJECT_DIR/config/config.template.json"

if [ ! -f "$CONFIG_FILE" ]; then
  if [ -f "$CONFIG_TEMPLATE" ]; then
    echo "配置文件不存在，从模板复制..."
    cp "$CONFIG_TEMPLATE" "$CONFIG_FILE"
    echo "⚠️ 请编辑 $CONFIG_FILE 修改默认配置"
    echo "特别注意："
    echo "  - 修改 server.domain 为您的实际域名"
    echo "  - 修改 users[0].password 为安全密码"
    echo "  - 使用 tools/generate_secret_key.py 生成安全密钥"
    die "配置文件需要初始化，请修改后重新运行"
  else
    die "找不到配置文件 $CONFIG_FILE 和模板文件 $CONFIG_TEMPLATE"
  fi
fi

# 验证配置文件格式
if ! jq empty "$CONFIG_FILE" 2>/dev/null; then
  die "配置文件 $CONFIG_FILE 格式错误，请检查JSON语法"
fi

# 检查必要的配置项
REQUIRED_FIELDS=("server.domain" "server.port" "users[0].username" "users[0].password" "security.secret_key")
for field in "${REQUIRED_FIELDS[@]}"; do
  value=$(jq -r ".$field" "$CONFIG_FILE" 2>/dev/null || echo "null")
  if [[ "$value" == "null" || "$value" == "" ]]; then
    die "配置文件缺少必要字段: $field"
  fi
done

# 检查默认密码
password=$(jq -r '.users[0].password' "$CONFIG_FILE")
secret_key=$(jq -r '.security.secret_key' "$CONFIG_FILE")
if [[ "$password" == "CHANGE_THIS_PASSWORD" ]]; then
  die "请修改默认密码！使用: python tools/generate_secret_key.py --config config/config.json --password"
fi
if [[ "$secret_key" == "CHANGE_THIS_TO_A_RANDOM_32_CHAR_STRING_MINIMUM" ]]; then
  die "请修改默认密钥！使用: python tools/generate_secret_key.py --config config/config.json"
fi

RAW_DOMAIN=$(jq -r '.server.domain' "$CONFIG_FILE")
DOMAIN=$(echo "$RAW_DOMAIN" | sed 's~https\?://~~' | sed 's:/*$::')
PORT=$(jq -r '.server.port' "$CONFIG_FILE")
CLEANUP_TIME=$(jq -r '.cleanup.cleanup_time' "$CONFIG_FILE" 2>/dev/null || echo "03:00:00")

echo "[INFO] domain=$DOMAIN port=$PORT cleanup_time=$CLEANUP_TIME"
echo "✅ 配置文件验证通过"

########################################
# 6. systemd 服务配置
########################################
echo "[STEP 6] 配置 systemd 服务 (fastapi + cleanup)"
SERVICE_FILE=/etc/systemd/system/fastapi.service
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Image Proxy FastAPI Service
After=network.target
Documentation=https://github.com/DpengYu/Image-Proxy-Project

[Service]
WorkingDirectory=$PROJECT_DIR/server
ExecStart=$VENV_PY -m uvicorn server:app --host 0.0.0.0 --port $PORT
Restart=always
RestartSec=5
User=$USER
Group=$USER
StandardOutput=append:/var/log/image_proxy/fastapi.log
StandardError=append:/var/log/image_proxy/fastapi.log
Environment=PYTHONPATH=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF

CLEANUP_SERVICE=/etc/systemd/system/fastapi-cleanup.service
sudo tee "$CLEANUP_SERVICE" > /dev/null <<EOF
[Unit]
Description=Image Proxy Cleanup Service
After=fastapi.service
Documentation=https://github.com/DpengYu/Image-Proxy-Project

[Service]
WorkingDirectory=$PROJECT_DIR/server
ExecStart=$VENV_PY cleanup.py
User=$USER
Group=$USER
StandardOutput=append:/var/log/image_proxy/fastapi.log
StandardError=append:/var/log/image_proxy/fastapi.log
Environment=PYTHONPATH=$PROJECT_DIR
EOF

CLEANUP_TIMER=/etc/systemd/system/fastapi-cleanup.timer
sudo tee "$CLEANUP_TIMER" > /dev/null <<EOF
[Unit]
Description=Image Proxy Daily Cleanup Timer
Documentation=https://github.com/DpengYu/Image-Proxy-Project

[Timer]
OnCalendar=$CLEANUP_TIME
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "✅ systemd 服务配置完成"

########################################
# 7. Nginx 配置（宝塔或独立）
########################################
echo "[STEP 7] 配置 Nginx 反向代理"

BT_CONF="/www/server/panel/vhost/nginx/${DOMAIN}.conf"
# 修改NGINX_CONF路径，使用宝塔面板的配置目录
NGINX_CONF="/www/server/panel/vhost/nginx/image-proxy.conf"
# 更新API路径，包括新增的/stats和/health等
LOCS=( "/docs" "/upload" "/get" "/secure_get" "/download_db" "/stats" "/health" )

# 检查宝塔面板配置文件是否存在，如果不存在则尝试查找其他可能的配置文件
if [ ! -f "$BT_CONF" ]; then
  echo "[DEBUG] 宝塔配置文件 $BT_CONF 不存在，尝试查找其他可能的配置文件"
  # 检查宝塔面板目录是否存在
  if [ -d "/www/server/panel/vhost/nginx/" ]; then
    echo "[DEBUG] 宝塔面板目录存在，查找所有配置文件"
    BT_FILES=$(find /www/server/panel/vhost/nginx/ -name "*.conf" 2>/dev/null || echo "")
    if [ -n "$BT_FILES" ]; then
      echo "[DEBUG] 找到以下宝塔配置文件:"
      echo "$BT_FILES"
      # 尝试查找包含域名的配置文件
      FOUND_BT_CONF=$(find /www/server/panel/vhost/nginx/ -name "*.conf" -exec grep -l "$DOMAIN" {} \; 2>/dev/null | head -n 1)
      if [ -n "$FOUND_BT_CONF" ]; then
        BT_CONF="$FOUND_BT_CONF"
        echo "[DEBUG] 找到匹配域名的宝塔配置文件: $BT_CONF"
      fi
    else
      echo "[DEBUG] 未找到任何宝塔配置文件"
    fi
  else
    echo "[DEBUG] 宝塔面板目录不存在"
  fi
fi

PY_MODIFY_SCRIPT=$(cat <<'PYCODE'
import sys, re
fn, loc, proxy = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(fn,'r',encoding='utf-8').read()
loc_pat = re.compile(r'(^\s*location\s+'+re.escape(loc)+r'\s*\{)', re.M)
block = ("    location {loc} {{\n"
         "        proxy_pass {proxy};\n"
         "        proxy_set_header Host $host;\n"
         "        proxy_set_header X-Real-IP $remote_addr;\n"
         "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
         "        proxy_set_header X-Forwarded-Proto $scheme;\n"
         "    }}\n").format(loc=loc,proxy=proxy)
if loc_pat.search(s):
    # 已存在 location，更新 proxy_pass
    s = re.sub(r'location\s+'+re.escape(loc)+r'\s*\{[^}]+\}', block, s, flags=re.S)
else:
    # 插到 server_name 后
    m2 = re.search(r'(server_name\s+[^\n;]+;)',s)
    if m2: insert_pos=m2.end(); s=s[:insert_pos]+"\n"+block+s[insert_pos:]
    else: s=s+"\n"+block
open(fn,'w',encoding='utf-8').write(s)
PYCODE
)

PY_HELPER=$(mktemp)
echo "$PY_MODIFY_SCRIPT" > "$PY_HELPER"
chmod +x "$PY_HELPER"

# 检查宝塔面板配置是否存在
BT_EXISTS=false
if [ -f "$BT_CONF" ]; then
  BT_EXISTS=true
else
  # 尝试查找其他可能的宝塔配置文件
  if [ -d "/www/server/panel/vhost/nginx/" ]; then
    # 查找包含域名的配置文件
    FOUND_BT_CONF=$(find /www/server/panel/vhost/nginx/ -name "*.conf" -exec grep -l "$DOMAIN" {} \; 2>/dev/null | head -n 1)
    if [ -n "$FOUND_BT_CONF" ]; then
      BT_CONF="$FOUND_BT_CONF"
      BT_EXISTS=true
      echo "[INFO] 找到匹配的宝塔配置: $BT_CONF"
    fi
  fi
fi

if [ "$BT_EXISTS" = true ]; then
  echo "[INFO] 检测到宝塔配置: $BT_CONF"
  sudo cp "$BT_CONF" "${BT_CONF}.bak.$(date +%s)" || true
  for L in "${LOCS[@]}"; do
    echo "  -> 添加/更新 location $L"
    sudo "$VENV_PY" "$PY_HELPER" "$BT_CONF" "$L" "http://127.0.0.1:$PORT"
  done
  echo "✅ 宝塔Nginx配置更新完成"
else
  echo "[INFO] 未检测到宝塔配置，创建独立配置"
  sudo mkdir -p "$(dirname "$NGINX_CONF")"
  
  # 创建HTTP服务器块
  sudo tee "$NGINX_CONF" > /dev/null <<EOF
# Image Proxy Project Nginx Configuration
server {
    listen 80;
    server_name $DOMAIN;
    
    # 基本安全设置
    client_max_body_size 20M;
    
    # 访问日志
    access_log /www/wwwlogs/image-proxy-access.log;
    error_log /www/wwwlogs/image-proxy-error.log;
EOF

  for L in "${LOCS[@]}"; do
    echo "  -> 添加 location $L"
    sudo "$VENV_PY" "$PY_HELPER" "$NGINX_CONF" "$L" "http://127.0.0.1:$PORT"
  done
  
  # 添加服务器块结束标签
  echo "}" | sudo tee -a "$NGINX_CONF" > /dev/null
  
  # 创建HTTPS服务器块（如果证书存在）
  if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] && [ -f "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ]; then
    sudo tee -a "$NGINX_CONF" > /dev/null <<EOF

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL安全设置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 基本安全设置
    client_max_body_size 20M;
    
    # 访问日志
    access_log /www/wwwlogs/image-proxy-access.log;
    error_log /www/wwwlogs/image-proxy-error.log;
EOF

    # 为HTTPS服务器块添加location配置
    for L in "${LOCS[@]}"; do
      sudo "$VENV_PY" "$PY_HELPER" "$NGINX_CONF" "$L" "http://127.0.0.1:$PORT"
    done
    
    # 添加HTTPS服务器块结束标签
    echo "}" | sudo tee -a "$NGINX_CONF" > /dev/null
  else
    echo "[INFO] SSL证书未找到，跳过HTTPS配置"
    echo "[INFO] 您可以使用Let's Encrypt获取免费SSL证书:"
    echo "      sudo certbot --nginx -d $DOMAIN"
  fi
  
  echo "✅ 独立Nginx配置创建完成"
fi

rm -f "$PY_HELPER"

########################################
# 8. 测试和重载 nginx
########################################
echo "[STEP 8] 测试并重载 nginx"
if sudo nginx -t; then
  sudo systemctl reload nginx
  echo "✅ Nginx配置测试通过并已重载"
else
  echo "⚠️ Nginx配置测试失败，跳过重载"
fi

########################################
# 9. 启动服务
########################################
echo "[STEP 9] 启动并启用 systemd 服务"
sudo systemctl daemon-reload

# 启动FastAPI服务
if sudo systemctl enable --now fastapi.service; then
  echo "✅ FastAPI服务启动成功"
else
  die "FastAPI服务启动失败"
fi

# 启动清理定时任务
if sudo systemctl enable --now fastapi-cleanup.timer; then
  echo "✅ 清理定时任务启动成功"
else
  echo "⚠️ 清理定时任务启动失败（非致命错误）"
fi

########################################
# 10. 验证安装
########################################
echo "[STEP 10] 验证安装结果"
sleep 3

# 检查服务状态
echo "检查服务状态:"
if systemctl is-active --quiet fastapi.service; then
  echo "  ✅ FastAPI服务: 运行中"
else
  echo "  ❌ FastAPI服务: 停止"
fi

if systemctl is-active --quiet fastapi-cleanup.timer; then
  echo "  ✅ 清理定时任务: 运行中"
else
  echo "  ❌ 清理定时任务: 停止"
fi

# 测试接口访问
echo "
测试接口访问:"
LOCAL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT/docs 2>/dev/null || echo "000")
DOMAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/docs 2>/dev/null || echo "000")
DOMAIN_SSL_STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" https://$DOMAIN/docs 2>/dev/null || echo "000")

echo "  本地HTTP  (127.0.0.1:$PORT): $LOCAL_STATUS"
echo "  域名HTTP  ($DOMAIN): $DOMAIN_STATUS"
echo "  域名HTTPS ($DOMAIN): $DOMAIN_SSL_STATUS"

echo "
==> 🎉 Image Proxy Project 安装完成！"
echo "
🔗 快速链接:"
echo "  • API文档: http://$DOMAIN/docs"
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] && [ -f "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ]; then
  echo "  • API文档(HTTPS): https://$DOMAIN/docs"
fi
echo "  • 管理面板: http://$DOMAIN/docs"
echo "  • 统计信息: http://$DOMAIN/stats"

echo "
🚀 后续操作:"
echo "  • 使用客户端: python client/client.py <图片路径>"
echo "  • 第三方集成: 查看 THIRD_PARTY_INTEGRATION.md"
echo "  • 服务管理: systemctl [start|stop|restart|status] fastapi"
echo "  • 查看日志: journalctl -u fastapi --no-pager -f"
echo "  • 测试服务: python tools/test_service.py"

echo "
🔍 验证方法:"
echo "  1. 上传测试: curl -X POST -F 'file=@/path/to/image.jpg' -F 'username=admin' -F 'password=您的密码' http://$DOMAIN/upload"
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] && [ -f "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ]; then
  echo "  1. HTTPS上传测试: curl -X POST -F 'file=@/path/to/image.jpg' -F 'username=admin' -F 'password=您的密码' https://$DOMAIN/upload"
fi
echo "  2. 查看数据: sqlite3 $PROJECT_DIR/server/images.db 'SELECT md5,name,access_count FROM images LIMIT 5;'"
echo "  3. 系统状态: systemctl status fastapi"

echo "
⚠️  重要提示:"
echo "  • 如果使用外网访问，请确保防火墙开放端口 80 和 443"
echo "  • 建议配置 HTTPS 证书以提高安全性"
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] || [ ! -f "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ]; then
  echo "  • 获取免费SSL证书: sudo certbot --nginx -d $DOMAIN"
fi
echo "  • 定期备份数据库: $PROJECT_DIR/server/images.db"

