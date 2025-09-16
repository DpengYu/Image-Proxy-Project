import os
import sqlite3
import time
import json
import hashlib
import hmac
import base64
from io import BytesIO
from fastapi import FastAPI, UploadFile, HTTPException, Query
from fastapi.responses import FileResponse
from PIL import Image

# -------------------------------
# 配置
# -------------------------------
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config/config.json")
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

SERVER_DOMAIN = config["server"]["domain"].rstrip("/")
UPLOAD_DIR = "uploads"
DB_FILE = "images.db"
EXPIRE_DAYS = config["cleanup"]["expire_days"]
USERS = {u['username']: u['password'] for u in config.get("users", [])}
SECRET_KEY = b"SuperSecretKey123"  # HMAC密钥

os.makedirs(UPLOAD_DIR, exist_ok=True)
app = FastAPI()

# -------------------------------
# 数据库初始化
# -------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS images (
            md5 TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            original_name TEXT,
            width INTEGER,
            height INTEGER,
            access_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------------
# 权限校验
# -------------------------------
def check_auth(username: str = Query(...), password: str = Query(...)):
    if USERS.get(username) != password:
        raise HTTPException(status_code=403, detail="权限不足，请联系管理员")
    return username, password

# -------------------------------
# 工具函数
# -------------------------------
def get_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def get_image_size(data: bytes):
    try:
        image = Image.open(BytesIO(data))
        return image.size
    except:
        return None, None

def generate_token(username: str, password: str, md5: str, expire: int):
    msg = f"{username}:{password}:{md5}:{expire}".encode("utf-8")
    digest = hmac.new(SECRET_KEY, msg, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(digest + b":" + msg).decode("utf-8")
    return token

def verify_token(token: str):
    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8"))
        digest, msg = decoded.split(b":", 1)
        expected_digest = hmac.new(SECRET_KEY, msg, hashlib.sha256).digest()
        if not hmac.compare_digest(digest, expected_digest):
            return None
        username, password, md5, expire_str = msg.decode("utf-8").split(":")
        if int(expire_str) < int(time.time()):
            return None
        return username, password, md5
    except Exception:
        return None

# -------------------------------
# 上传接口 /upload
# -------------------------------
@app.post("/upload")
async def upload_image(file: UploadFile, username: str = Query(...), password: str = Query(...)):
    check_auth(username, password)
    content = await file.read()
    md5 = get_md5(content)
    now = int(time.time())
    width, height = get_image_size(content)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 1. 查询是否已有
    c.execute("SELECT md5, path, created_at, original_name, width, height, access_count FROM images WHERE md5=?", (md5,))
    row = c.fetchone()
    if row:
        md5_exist, path, created_at, name, w, h, access_count = row
        conn.close()
        expire_time = created_at + EXPIRE_DAYS*86400
        token = generate_token(username, password, md5_exist, expire_time)
        return {
            "url": f"{SERVER_DOMAIN}/secure_get/{md5_exist}?token={token}",
            "expire_at": expire_time,
            "name": name,
            "width": w,
            "height": h,
            "access_count": access_count,
            "status": "existing"
        }

    # 2. 保存新文件
    filename = f"{md5}.png"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)

    c.execute("""
        INSERT INTO images (md5, path, created_at, original_name, width, height, access_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (md5, path, now, file.filename, width, height, 0))
    conn.commit()
    conn.close()

    expire_time = now + EXPIRE_DAYS*86400
    token = generate_token(username, password, md5, expire_time)
    return {
        "url": f"{SERVER_DOMAIN}/secure_get/{md5}?token={token}",
        "expire_at": expire_time,
        "name": file.filename,
        "width": width,
        "height": height,
        "access_count": 0,
        "status": "uploaded"
    }

# -------------------------------
# 加密访问接口 /secure_get/{md5}
# -------------------------------
@app.get("/secure_get/{md5}")
async def secure_get(md5: str, token: str):
    result = verify_token(token)
    if not result:
        raise HTTPException(status_code=403, detail="无效或过期的 token")
    username, password, md5_token = result
    if md5 != md5_token:
        raise HTTPException(status_code=403, detail="Token与图片不匹配")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT path, access_count FROM images WHERE md5=?", (md5,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Not found")
    path, access_count = row
    c.execute("UPDATE images SET access_count=? WHERE md5=?", (access_count+1, md5))
    conn.commit()
    conn.close()
    return FileResponse(path)

# -------------------------------
# 查询图片信息接口 /info/{md5}
# -------------------------------
@app.get("/info/{md5}")
async def get_image_info(md5: str, username: str = Query(...), password: str = Query(...)):
    check_auth(username, password)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT md5, created_at, original_name, width, height, access_count FROM images WHERE md5=?", (md5,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    md5_exist, created_at, name, width, height, access_count = row
    expire_time = created_at + EXPIRE_DAYS*86400
    token = generate_token(username, password, md5_exist, expire_time)
    return {
        "url": f"{SERVER_DOMAIN}/secure_get/{md5_exist}?token={token}",
        "expire_at": expire_time,
        "name": name,
        "width": width,
        "height": height,
        "access_count": access_count,
        "status": "existing"
    }

# -------------------------------
# 下载数据库接口 /download_db
# -------------------------------
@app.get("/download_db")
async def download_db(username: str = Query(...), password: str = Query(...)):
    check_auth(username, password)
    if not os.path.exists(DB_FILE):
        raise HTTPException(status_code=404, detail="Database not found")
    return FileResponse(DB_FILE, filename="images.db", media_type="application/octet-stream")
