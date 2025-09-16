#!/bin/bash
set -euo pipefail

echo "==> Start install.sh"

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PY="$PROJECT_DIR/venv/bin/python"

# helper: exit with message
die(){ echo "[FATAL] $*"; exit 1; }

# 0. check python venv
if [ ! -x "$VENV_PY" ]; then
  die "虚拟环境未准备好，请先创建: python3 -m venv $PROJECT_DIR/venv && source $PROJECT_DIR/venv/bin/activate"
fi

# 1. 安装/升级 Python 包
echo "1. 安装/升级 Python 包 (在 venv 中)"
"$VENV_PY" -m pip install --upgrade pip setuptools wheel
"$VENV_PY" -m pip install -r "$PROJECT_DIR/requirements.txt"

# 2. 系统工具检查
echo "2. 检查系统命令 (nginx, openssl, jq)"
for cmd in nginx openssl jq; do
  if ! command -v $cmd >/dev/null 2>&1; then
    echo "[INFO] $cmd 未安装，尝试安装"
    sudo apt update && sudo apt install -y $cmd
  fi
done

# 3. 日志目录
echo "3. 创建日志目录 /var/log/image_proxy"
sudo mkdir -p /var/log/image_proxy
sudo touch /var/log/image_proxy/fastapi.log
sudo chown "$USER":"$USER" /var/log/image_proxy/fastapi.log

# 4. 读取配置
CONFIG_FILE="$PROJECT_DIR/config/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
  die "找不到配置文件 $CONFIG_FILE"
fi

RAW_DOMAIN=$(jq -r '.server.domain' "$CONFIG_FILE")
DOMAIN=$(echo "$RAW_DOMAIN" | sed 's~https\?://~~' | sed 's:/*$::')
PORT=$(jq -r '.server.port' "$CONFIG_FILE")
CLEANUP_TIME=$(jq -r '.cleanup.cleanup_time' "$CONFIG_FILE")

echo "[INFO] domain=$DOMAIN port=$PORT cleanup_time=$CLEANUP_TIME"

# 5. systemd 服务
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

# 6. Nginx 配置（宝塔或独立）
echo "5. 配置 Nginx 反向代理 /docs /upload /get /secure_get"
BT_CONF="/www/server/panel/vhost/nginx/${DOMAIN}.conf"
NGINX_CONF="/etc/nginx/conf.d/fastapi.conf"
LOCS=( "/docs" "/upload" "/get" ”/secure_get“ "/download_db" )

PY_MODIFY_SCRIPT=$(cat <<'PYCODE'
import sys, re
fn, loc, proxy = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(fn,'r',encoding='utf-8').read()
loc_pat = re.compile(r'(^\s*location\s+'+re.escape(loc)+r'\s*\{)', re.M)
m = loc_pat.search(s)
block = ("    location {loc} {{\n"
         "        proxy_pass {proxy};\n"
         "        proxy_set_header Host $host;\n"
         "        proxy_set_header X-Real-IP $remote_addr;\n"
         "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
         "        proxy_set_header X-Forwarded-Proto $scheme;\n"
         "    }}\n").format(loc=loc,proxy=proxy)
if m:
    start = m.start(); i = m.end(); depth=1
    while i < len(s) and depth>0:
        if s[i]=='{': depth+=1
        elif s[i]=='}': depth-=1
        i+=1
    block_text = s[m.start():i]
    new_block_text = re.sub(r'proxy_pass\s+[^;]+;', "proxy_pass %s;" % proxy, block_text)
    if new_block_text==block_text and 'proxy_pass' not in block_text:
        new_block_text = block_text.rstrip()[:-1]+"    proxy_pass %s;\n}\n"%proxy
    s=s[:m.start()]+new_block_text+s[i:]
else:
    m2=re.search(r'(server_name\s+[^\n;]+;)',s)
    if m2: insert_pos=m2.end(); s=s[:insert_pos]+"\n"+block+s[insert_pos:]
    else: s=s+"\n"+block
open(fn,'w',encoding='utf-8').write(s)
PYCODE
)

PY_HELPER=$(mktemp)
echo "$PY_MODIFY_SCRIPT" > "$PY_HELPER"
chmod +x "$PY_HELPER"

if [ -f "$BT_CONF" ]; then
  echo "[INFO] 检测到宝塔配置: $BT_CONF"
  sudo cp "$BT_CONF" "${BT_CONF}.bak.install_$(date +%s)" || true
  for L in "${LOCS[@]}"; do
    sudo "$VENV_PY" "$PY_HELPER" "$BT_CONF" "$L" "http://127.0.0.1:$PORT"
  done
else
  echo "[INFO] 未检测到宝塔配置，创建/更新独立 Nginx 配置 $NGINX_CONF"
  sudo mkdir -p "$(dirname "$NGINX_CONF")"
  sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
}
EOF
  for L in "${LOCS[@]}"; do
    sudo "$VENV_PY" "$PY_HELPER" "$NGINX_CONF" "$L" "http://127.0.0.1:$PORT"
  done
fi

rm -f "$PY_HELPER"

echo "6. 测试并 reload nginx"
sudo nginx -t
sudo systemctl reload nginx

echo "7. 启动并启用 systemd 服务"
sudo systemctl daemon-reload
sudo systemctl enable --now fastapi.service
sudo systemctl enable --now fastapi-cleanup.timer

echo "8. 测试 FastAPI 本地与域名 /docs"
sleep 2
LOCAL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT/docs || echo "000")
DOMAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/docs || echo "000")
DOMAIN_SSL_STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" https://$DOMAIN/docs || echo "000")

echo "  local http : $LOCAL_STATUS"
echo "  domain http: $DOMAIN_STATUS"
echo "  domain https: $DOMAIN_SSL_STATUS"
echo "==> install.sh 完成"
