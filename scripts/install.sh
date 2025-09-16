#!/bin/bash
set -euo pipefail

# ------------------------------
# install.sh - final version
# ------------------------------
# 功能：
# - 安装 Python 依赖 (fastapi, uvicorn, python-multipart, requests)
# - 创建 systemd 服务 (fastapi + cleanup timer)
# - 检测宝塔面板配置并智能插入/更新 location /docs /upload /get（避免重复）
# - 非宝塔创建 /etc/nginx/conf.d/fastapi.conf，支持 HTTP + HTTPS（自签名证书）
# - 测试访问
# ------------------------------

echo "==> Start install.sh"

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PY="$PROJECT_DIR/venv/bin/python"

# helper: exit with message
die(){ echo "[FATAL] $*"; exit 1; }

# 0. check python venv
if [ ! -x "$VENV_PY" ]; then
  echo "[ERROR] 没有找到虚拟环境 Python: $VENV_PY"
  echo "请先运行（在项目根目录）："
  echo "  python3 -m venv venv"
  echo "  source venv/bin/activate"
  echo "  pip install -r requirements.txt"
  die "虚拟环境未准备好，退出。"
fi

echo "1. 安装/升级 Python 包 (在 venv 中)"
"$VENV_PY" -m pip install --upgrade pip setuptools >/dev/null
"$VENV_PY" -m pip install fastapi uvicorn python-multipart requests >/dev/null

# 1. ensure system tools
echo "2. 检查系统命令 (nginx, openssl, jq)"
if ! command -v nginx >/dev/null 2>&1; then
  echo "[INFO] nginx 未安装，尝试自动安装（apt）"
  sudo apt update
  sudo apt install -y nginx
fi
if ! command -v openssl >/dev/null 2>&1; then
  sudo apt install -y openssl
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "[INFO] jq 未安装，尝试安装（apt）"
  sudo apt update
  sudo apt install -y jq
fi

echo "3. 创建日志目录 /var/log/image_proxy"
sudo mkdir -p /var/log/image_proxy
sudo touch /var/log/image_proxy/fastapi.log
sudo chown "$USER":"$USER" /var/log/image_proxy/fastapi.log

# 2. read config
CONFIG_FILE="$PROJECT_DIR/config/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
  die "找不到配置文件 $CONFIG_FILE"
fi

# Clean domain: remove scheme and trailing slashes
RAW_DOMAIN=$(jq -r '.server.domain' "$CONFIG_FILE")
DOMAIN=$(echo "$RAW_DOMAIN" | sed 's~https\?://~~' | sed 's:/*$::' )
PORT=$(jq -r '.server.port' "$CONFIG_FILE")
CLEANUP_TIME=$(jq -r '.cleanup.cleanup_time' "$CONFIG_FILE")

echo "[INFO] domain=$DOMAIN port=$PORT cleanup_time=$CLEANUP_TIME"

# 3. setup systemd service files
echo "4. 配置 systemd 服务 (fastapi + cleanup)"
SERVICE_FILE=/etc/systemd/system/fastapi.service
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
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

CLEANUP_SERVICE=/etc/systemd/system/fastapi-cleanup.service
sudo tee "$CLEANUP_SERVICE" > /dev/null <<EOF
[Unit]
Description=FastAPI Cleanup Service
After=fastapi.service

[Service]
WorkingDirectory=$PROJECT_DIR/server
ExecStart=$VENV_PY cleanup.py
User=$USER
Group=$USER
EOF

CLEANUP_TIMER=/etc/systemd/system/fastapi-cleanup.timer
sudo tee "$CLEANUP_TIMER" > /dev/null <<EOF
[Unit]
Description=Run FastAPI Cleanup Daily

[Timer]
OnCalendar=$CLEANUP_TIME
Persistent=true

[Install]
WantedBy=timers.target
EOF

# 4. Prepare Nginx modification: safe Python helper to insert or update location blocks.
# Use python (from venv) to safely parse and modify text to avoid sed pitfalls.
PY_MODIFY_SCRIPT=$(cat <<'PYCODE'
import sys, re, io

fn = sys.argv[1]
loc = sys.argv[2]   # e.g. /docs
proxy = sys.argv[3] # e.g. http://127.0.0.1:9575
# Read file
s = open(fn, 'r', encoding='utf-8').read()
# pattern to find "location /xxx" block
loc_pat = re.compile(r'(^\s*location\s+' + re.escape(loc) + r'\s*\{)', re.M)
m = loc_pat.search(s)
block = (
    "    location {loc} {{\n"
    "        proxy_pass {proxy};\n"
    "        proxy_set_header Host $host;\n"
    "        proxy_set_header X-Real-IP $remote_addr;\n"
    "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
    "        proxy_set_header X-Forwarded-Proto $scheme;\n"
    "    }}\n"
).format(loc=loc, proxy=proxy)
if m:
    # update existing block's proxy_pass line if present; else inject proxy_pass line
    start = m.start()
    # find matching brace for this location block (simple counting)
    i = m.end()
    depth = 1
    while i < len(s) and depth>0:
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
        i += 1
    block_text = s[m.start():i]
    # replace proxy_pass lines inside block
    new_block_text = re.sub(r'proxy_pass\s+[^;]+;', "proxy_pass %s;" % proxy, block_text)
    # if no proxy_pass existed, insert before ending brace
    if new_block_text == block_text and 'proxy_pass' not in block_text:
        new_block_text = block_text.rstrip()[:-1] + "    proxy_pass %s;\n}\n" % proxy
    s = s[:m.start()] + new_block_text + s[i:]
else:
    # try to find server_name line to insert after
    m2 = re.search(r'(server_name\s+[^\n;]+;)', s)
    if m2:
        insert_pos = m2.end()
        s = s[:insert_pos] + "\n" + block + s[insert_pos:]
    else:
        # not a typical server file; append to end
        s = s + "\n" + block
open(fn, 'w', encoding='utf-8').write(s)
PYCODE
)

# write helper to temp file
PY_HELPER=$(mktemp)
echo "$PY_MODIFY_SCRIPT" > "$PY_HELPER"
chmod +x "$PY_HELPER"

echo "5. 配置 Nginx 反向代理 /docs /upload /get"

BT_CONF="/www/server/panel/vhost/nginx/${DOMAIN}.conf"
NGINX_CONF="/etc/nginx/conf.d/fastapi.conf"

# location list
LOCS=( "/docs" "/upload" "/get" )

if [ -f "$BT_CONF" ]; then
  echo "[INFO] 检测到宝塔配置: $BT_CONF"
  # Ensure backup
  sudo cp "$BT_CONF" "${BT_CONF}.bak.install_$(date +%s)" || true

  # for each location call python helper to safely update or insert
  for L in "${LOCS[@]}"; do
    echo "[INFO] 确保 $L 在 $BT_CONF 中指向 http://127.0.0.1:$PORT"
    sudo "$VENV_PY" "$PY_HELPER" "$BT_CONF" "$L" "http://127.0.0.1:$PORT"
  done

  # If BT config includes a 443 server block and cert paths, also ensure /docs,/upload,/get exist there.
  # We will attempt to detect presence of "listen 443" in the file; if present, python helper above already updated any 'location' occurrences,
  # so nothing more needed. If user wants to add HTTPS blocks, do it via panel (safer).
  echo "[INFO] 已在宝塔配置中添加/更新 location（如果需要 HTTPS，请在宝塔面板中配置证书）"

else
  echo "[INFO] 未检测到宝塔配置，创建/更新独立 Nginx 配置 $NGINX_CONF"

  # ensure conf exists with basic server 80
  if [ ! -f "$NGINX_CONF" ]; then
    sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
}
EOF
  fi

  # for each location ensure present
  for L in "${LOCS[@]}"; do
    # run helper to insert or update
    sudo "$VENV_PY" "$PY_HELPER" "$NGINX_CONF" "$L" "http://127.0.0.1:$PORT"
  done

  # prepare SSL certs (self-signed) under /etc/ssl/<domain>
  SSL_DIR="/etc/ssl/$DOMAIN"
  SSL_CERT="$SSL_DIR/fullchain.pem"
  SSL_KEY="$SSL_DIR/privkey.pem"
  if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
    echo "[INFO] 未找到证书，生成自签名证书到 $SSL_DIR"
    sudo mkdir -p "$SSL_DIR"
    # ensure DOMAIN is safe for CN
    SAFE_CN=$(echo "$DOMAIN" | sed 's/[^A-Za-z0-9\.-]/_/g')
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout "$SSL_KEY" \
      -out "$SSL_CERT" \
      -subj "/CN=${SAFE_CN}"
  fi

  # add HTTPS server block if not present
  if ! sudo grep -q "listen 443 ssl" "$NGINX_CONF" 2>/dev/null; then
    sudo tee -a "$NGINX_CONF" > /dev/null <<EOF

server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate $SSL_CERT;
    ssl_certificate_key $SSL_KEY;
}
EOF
    # insert location blocks into HTTPS server (reuse helper)
    for L in "${LOCS[@]}"; do
      sudo "$VENV_PY" "$PY_HELPER" "$NGINX_CONF" "$L" "http://127.0.0.1:$PORT"
    done
  fi
fi

# cleanup temp python helper
rm -f "$PY_HELPER"

# test nginx
echo "6. 测试并 reload nginx"
sudo nginx -t
sudo systemctl reload nginx

# enable + start systemd
echo "7. 启动并启用 systemd 服务"
sudo systemctl daemon-reload
sudo systemctl enable --now fastapi.service
sudo systemctl enable --now fastapi-cleanup.timer

# 8. test endpoints
echo "8. 测试 FastAPI 本地与域名 /docs"
sleep 2
LOCAL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT/docs || echo "000")
DOMAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/docs || echo "000")
DOMAIN_SSL_STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" https://$DOMAIN/docs || echo "000")

echo "  local http : $LOCAL_STATUS"
echo "  domain http: $DOMAIN_STATUS"
echo "  domain https: $DOMAIN_SSL_STATUS"

if [ "$LOCAL_STATUS" -eq 200 ]; then
  echo "✅ FastAPI 本地 /docs OK"
else
  echo "❌ 本地 /docs 失败 (状态 $LOCAL_STATUS)"
fi

if [ "$DOMAIN_STATUS" -eq 200 ]; then
  echo "✅ 域名 http://$DOMAIN/docs OK"
else
  echo "⚠️ 域名 http://$DOMAIN/docs (状态 $DOMAIN_STATUS)"
fi

if [ "$DOMAIN_SSL_STATUS" -eq 200 ]; then
  echo "✅ 域名 https://$DOMAIN/docs OK"
else
  echo "⚠️ 域名 https://$DOMAIN/docs (状态 $DOMAIN_SSL_STATUS) - 若为宝塔，请在面板配置证书后再测试 HTTPS"
fi

echo "==> install.sh 完成"
