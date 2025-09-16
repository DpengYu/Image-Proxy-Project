import os
import json
import sqlite3
import hashlib
import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from PIL import Image  # 获取图片尺寸

# -------------------------------
# 配置
# -------------------------------
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config/config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

SERVER_DOMAIN = config["server"]["domain"]
UPLOAD_DIR = "uploads"
DB_FILE = "images.db"
EXPIRE_DAYS = config["cleanup"]["expire_days"]

os.makedirs(UPLOAD_DIR, exist_ok=True)
app = FastAPI()


# -------------------------------
# 数据库初始化 / 升级
# -------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 创建 images 表，如果列不存在则新增（安全升级旧数据库）
    c.execute("""
        CREATE TABLE IF NOT EXISTS images (
            md5 TEXT PRIMARY KEY,
            filename TEXT,
            path TEXT NOT NULL,
            width INTEGER,
            height INTEGER,
            created_at INTEGER NOT NULL,
            access_count INTEGER DEFAULT 0
        )
    """)
    # 检查旧版表结构，如果缺少新字段，尝试 ALTER TABLE
    columns = [row[1] for row in c.execute("PRAGMA table_info(images)").fetchall()]
    if "filename" not in columns:
        c.execute("ALTER TABLE images ADD COLUMN filename TEXT")
    if "width" not in columns:
        c.execute("ALTER TABLE images ADD COLUMN width INTEGER")
    if "height" not in columns:
        c.execute("ALTER TABLE images ADD COLUMN height INTEGER")
    if "access_count" not in columns:
        c.execute("ALTER TABLE images ADD COLUMN access_count INTEGER DEFAULT 0")
    conn.commit()
    conn.close()


init_db()


# -------------------------------
# MD5计算
# -------------------------------
def get_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


# -------------------------------
# 上传图片
# -------------------------------
@app.post("/upload")
async def upload_image(file: UploadFile):
    content = await file.read()
    md5 = get_md5(content)
    now = int(time.time())

    # 获取原始文件名
    filename_original = Path(file.filename).name

    # 获取图片尺寸
    try:
        img = Image.open(Path(file.filename))
        width, height = img.size
    except Exception:
        width = height = None

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT path, created_at FROM images WHERE md5=?", (md5,))
    row = c.fetchone()

    if row and now - row[1] < EXPIRE_DAYS * 86400:
        conn.close()
        return {"url": f"/get/{md5}", "expire_at": row[1] + EXPIRE_DAYS * 86400}

    # 保存文件
    filename_save = f"{md5}.png"
    path_save = os.path.join(UPLOAD_DIR, filename_save)
    with open(path_save, "wb") as f:
        f.write(content)

    # 写入数据库
    c.execute(
        "INSERT OR REPLACE INTO images (md5, filename, path, width, height, created_at, access_count) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (md5, filename_original, path_save, width, height, now, 0)
    )
    conn.commit()
    conn.close()

    return {"url": f"/get/{md5}", "expire_at": now + EXPIRE_DAYS * 86400}


# -------------------------------
# 获取图片
# -------------------------------
@app.get("/get/{md5}")
async def get_image(md5: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT path, created_at, access_count FROM images WHERE md5=?", (md5,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Not found")
    path, created_at, access_count = row

    if int(time.time()) - created_at > EXPIRE_DAYS * 86400:
        conn.close()
        raise HTTPException(status_code=410, detail="Expired")

    # 更新访问次数
    c.execute("UPDATE images SET access_count=? WHERE md5=?", (access_count + 1, md5))
    conn.commit()
    conn.close()

    return FileResponse(path)
