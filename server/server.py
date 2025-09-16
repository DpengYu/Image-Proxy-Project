from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
import hashlib, os, sqlite3, time, json
from PIL import Image  # 用于获取图片尺寸

# -------------------------------
# 读取配置
# -------------------------------
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config/config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

UPLOAD_DIR = "uploads"
DB_FILE = "images.db"
EXPIRE_DAYS = config.get("cleanup", {}).get("expire_days", 7)

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
            original_name TEXT NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            access_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------------
# 计算 MD5
# -------------------------------
def get_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

# -------------------------------
# 上传接口
# -------------------------------
@app.post("/upload")
async def upload_image(file: UploadFile):
    content = await file.read()
    md5 = get_md5(content)
    now = int(time.time())

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT path, created_at FROM images WHERE md5=?", (md5,))
    row = c.fetchone()

    # 图片未过期直接返回 URL
    if row and now - row[1] < EXPIRE_DAYS*86400:
        conn.close()
        return {"url": f"/get/{md5}", "expire_at": row[1]+EXPIRE_DAYS*86400}

    # 保存文件
    filename = f"{md5}.png"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)

    # 获取图片尺寸
    try:
        img = Image.open(path)
        width, height = img.size
    except Exception:
        width = height = 0

    c.execute("""
        INSERT OR REPLACE INTO images 
        (md5, path, original_name, width, height, created_at, access_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (md5, path, file.filename, width, height, now, 0))

    conn.commit()
    conn.close()
    return {"url": f"/get/{md5}", "expire_at": now + EXPIRE_DAYS*86400,
            "width": width, "height": height, "original_name": file.filename}

# -------------------------------
# 获取接口
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
    now = int(time.time())
    if now - created_at > EXPIRE_DAYS*86400:
        conn.close()
        raise HTTPException(status_code=410, detail="Expired")

    # 更新访问次数
    c.execute("UPDATE images SET access_count=? WHERE md5=?", (access_count+1, md5))
    conn.commit()
    conn.close()

    return FileResponse(path)
