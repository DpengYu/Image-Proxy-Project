from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
import hashlib, os, sqlite3, time, json

# 读取配置
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config/config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

SERVER_DOMAIN = config["server"]["domain"]
UPLOAD_DIR = "uploads"
DB_FILE = "images.db"
EXPIRE_DAYS = config["cleanup"]["expire_days"]

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS images (
            md5 TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

@app.post("/upload")
async def upload_image(file: UploadFile):
    content = await file.read()
    md5 = get_md5(content)
    now = int(time.time())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT path, created_at FROM images WHERE md5=?", (md5,))
    row = c.fetchone()

    if row and now - row[1] < EXPIRE_DAYS*86400:
        conn.close()
        return {"url": f"/get/{md5}", "expire_at": row[1]+EXPIRE_DAYS*86400}

    filename = f"{md5}.png"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(content)

    c.execute("INSERT OR REPLACE INTO images (md5, path, created_at) VALUES (?, ?, ?)",
              (md5, path, now))
    conn.commit()
    conn.close()
    return {"url": f"/get/{md5}", "expire_at": now + EXPIRE_DAYS*86400}

@app.get("/get/{md5}")
async def get_image(md5: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT path, created_at FROM images WHERE md5=?", (md5,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    if int(time.time()) - row[1] > EXPIRE_DAYS*86400:
        raise HTTPException(status_code=410, detail="Expired")
    return FileResponse(row[0])
