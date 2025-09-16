import requests
import os
import json

# -------------------------------
# 配置
# -------------------------------
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config/config.json")
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"找不到配置文件: {CONFIG_FILE}")

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

SERVER = config.get("server", {}).get("domain").rstrip("/")
USERNAME = config['users'][0]['username']
PASSWORD = config['users'][0]['password']
OUTPUT_FILE = "images_server.db"  # 本地保存数据库名

# -------------------------------
# 下载数据库
# -------------------------------
def download_server_db():
    url = f"{SERVER}/download_db"
    params = {"username": USERNAME, "password": PASSWORD}
    try:
        r = requests.get(url, params=params, stream=True)
        r.raise_for_status()
        with open(OUTPUT_FILE, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"[INFO] 已成功下载服务器数据库到 {OUTPUT_FILE}")
    except requests.RequestException as e:
        print(f"[ERROR] 下载失败: {e}")

# -------------------------------
# 主程序
# -------------------------------
if __name__ == "__main__":
    download_server_db()
