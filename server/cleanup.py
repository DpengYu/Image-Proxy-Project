import sqlite3, os, time, json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config/config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

UPLOAD_DIR = "uploads"
DB_FILE = "images.db"
EXPIRE_DAYS = config["cleanup"]["expire_days"]

def cleanup():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    expire_time = int(time.time()) - EXPIRE_DAYS*86400
    c.execute("SELECT path FROM images WHERE created_at < ?", (expire_time,))
    rows = c.fetchall()
    for (path,) in rows:
        if os.path.exists(path):
            os.remove(path)
    c.execute("DELETE FROM images WHERE created_at < ?", (expire_time,))
    conn.commit()
    conn.close()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cleanup finished, {len(rows)} files removed.")

if __name__ == "__main__":
    if config["cleanup"]["enable"]:
        cleanup()
