import sqlite3, hashlib, time, requests, os, json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config/config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

SERVER = f"http://{config['server']['domain']}:{config['server']['port']}"
CACHE_DB = "cache.db"
EXPIRE_DAYS = config["cleanup"]["expire_days"]

def init_cache():
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            md5 TEXT PRIMARY KEY,
            url TEXT,
            expire_at INTEGER
        )
    """)
    conn.commit()
    conn.close()

def get_md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def upload_or_get(path):
    md5 = get_md5(path)
    now = int(time.time())
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute("SELECT url, expire_at FROM cache WHERE md5=?", (md5,))
    row = c.fetchone()
    if row and now < row[1]:
        conn.close()
        return SERVER + row[0]

    with open(path, "rb") as f:
        r = requests.post(SERVER+"/upload", files={"file": f})
        data = r.json()
    url, expire_at = data["url"], data["expire_at"]
    c.execute("INSERT OR REPLACE INTO cache (md5,url,expire_at) VALUES(?,?,?)",
              (md5,url,expire_at))
    conn.commit()
    conn.close()
    return SERVER + url

if __name__ == "__main__":
    init_cache()
    url = upload_or_get("test.png")
    print("图片 URL:", url)
