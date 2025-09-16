import os
import sqlite3
import time
import json
import hashlib
from io import BytesIO
from fastapi import FastAPI, UploadFile, HTTPException, Query, Depends
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

os.makedirs(UPLOAD_DIR, exist_ok=True)
app = FastAPI()

# -------------------------------
# 数据库初始化/升级
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
    return True

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

# -------------------------------
# 上传接口 /upload
# -------------------------------
@app.post("/upload")
async def upload_image(file: UploadFile, auth: bool = Depends(check_auth)):
    content = await file.read()
    md5 = get_md5(content)
    now = int(time.time())
    width, height = get_image_size(content)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 先检查服务器数据库是否已有该图片
    c.execute("SELECT md5, path, created_at, original_name, width, height, access_count FROM images WHERE md5=?", (md5,))
    row = c.fetchone()
    if row:
        md5_exist, path, created_at, name, w, h, access_count = row
        conn.close()
        return {
            "url": f"/get/{md5_exist}",
            "expire_at": created_at + EXPIRE_DAYS*86400,
            "name": name,
            "width": w,
            "height": h,
            "access_count": access_count,
            "status": "existing"
        }

    # 不存在则保存文件
    filename = f"{md5}.png"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)

    # 插入数据库
    c.execute("""
        INSERT INTO images (md5, path, created_at, original_name, width, height, access_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (md5, path, now, file.filename, width, height, 0))
    conn.commit()
    conn.close()

    return {
        "url": f"/get/{md5}",
        "expire_at": now + EXPIRE_DAYS*86400,
        "name": file.filename,
        "width": width,
        "height": height,
        "access_count": 0,
        "status": "uploaded"
    }

# -------------------------------
# 获取图片接口 /get/{md5}
# -------------------------------
@app.get("/get/{md5}")
async def get_image(md5: str, auth: bool = Depends(check_auth)):
    now = int(time.time())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT path, created_at, access_count FROM images WHERE md5=?", (md5,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Not found")

    path, created_at, access_count = row
    if now - created_at > EXPIRE_DAYS*86400:
        conn.close()
        raise HTTPException(status_code=410, detail="Expired")

    # 更新访问次数
    c.execute("UPDATE images SET access_count=? WHERE md5=?", (access_count+1, md5))
    conn.commit()
    conn.close()
    return FileResponse(path)

# -------------------------------
# 查询图片信息接口 /info/{md5}
# -------------------------------
@app.get("/info/{md5}")
async def get_image_info(md5: str, auth: bool = Depends(check_auth)):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT md5, created_at, original_name, width, height, access_count FROM images WHERE md5=?", (md5,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    md5_exist, created_at, name, width, height, access_count = row
    return {
        "url": f"/get/{md5_exist}",
        "expire_at": created_at + EXPIRE_DAYS*86400,
        "name": name,
        "width": width,
        "height": height,
        "access_count": access_count
    }

# -------------------------------
# 下载数据库接口 /download_db
# -------------------------------
@app.get("/download_db")
async def download_db(auth: bool = Depends(check_auth)):
    if not os.path.exists(DB_FILE):
        raise HTTPException(status_code=404, detail="Database not found")
    return FileResponse(DB_FILE, filename="images.db", media_type="application/octet-stream")
