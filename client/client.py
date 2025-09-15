import sqlite3
import hashlib
import time
import requests
import os
import json
from pathlib import Path

# -------------------------------
# 配置
# -------------------------------
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config/config.json")
print(f"[DEBUG] Loading config from {CONFIG_FILE}")
with open(CONFIG_FILE) as f:
    config = json.load(f)

SERVER = f"{config['server']['domain']}:{config['server']['port']}"
print(f"[DEBUG] Server URL: {SERVER}")

CACHE_DB = "cache.db"
os.makedirs("cache", exist_ok=True)  # 可选缓存目录

# -------------------------------
# 客户端 SQLite 缓存初始化
# -------------------------------
def init_cache():
    conn = sqlite3.connect(CACHE_DB, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS images (
            md5 TEXT PRIMARY KEY,
            url TEXT,
            created_at INTEGER
        )
    """)
    conn.commit()
    conn.close()
    print("[DEBUG] Cache database initialized")

init_cache()

# -------------------------------
# 计算文件 MD5
# -------------------------------
def get_md5(file_path):
    file_path = Path(file_path)
    print(f"[DEBUG] Calculating MD5 for: {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"[ERROR] File not found: {file_path}")
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    md5 = md5_hash.hexdigest()
    print(f"[DEBUG] MD5: {md5}")
    return md5

# -------------------------------
# 上传或获取已缓存的 URL
# -------------------------------
def upload_or_get(file_path):
    md5 = get_md5(file_path)
    now = int(time.time())

    # 检查缓存
    conn = sqlite3.connect(CACHE_DB, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT url, created_at FROM images WHERE md5=?", (md5,))
    row = c.fetchone()
    if row:
        url, created_at = row
        print(f"[DEBUG] Found cached URL: {url}")
        conn.close()
        return url

    print(f"[DEBUG] Uploading file to server: {file_path}")
    try:
        with open(file_path, "rb") as f:
            r = requests.post(f"{SERVER}/upload", files={"file": f})
        r.raise_for_status()
        data = r.json()
        url = data.get("url")
        print(f"[DEBUG] Uploaded successfully, URL: {url}")

        # 缓存
        c.execute(
            "INSERT OR REPLACE INTO images (md5, url, created_at) VALUES (?, ?, ?)",
            (md5, url, now)
        )
        conn.commit()
        conn.close()
        return url
    except requests.exceptions.RequestException as e:
        conn.close()
        print(f"[ERROR] Upload failed: {e}")
        raise

# -------------------------------
# 主函数
# -------------------------------
if __name__ == "__main__":
    test_file = r"test.png"
    print(f"[INFO] Starting upload_or_get for: {test_file}")
    try:
        url = upload_or_get(test_file)
        print(f"[INFO] Final URL: {url}")
    except Exception as e:
        print(f"[ERROR] {e}")
