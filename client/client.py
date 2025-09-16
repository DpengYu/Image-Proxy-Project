import hashlib
import requests
import os
from pathlib import Path
import json

# -------------------------------
# 配置
# -------------------------------
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../config/config.json")
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"找不到配置文件: {CONFIG_FILE}")

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

SERVER = config['server']['domain'].rstrip('/')
USER_INFO = config.get("users", [{}])[0]
USERNAME = USER_INFO.get("username", "")
PASSWORD = USER_INFO.get("password", "")
if not USERNAME or not PASSWORD:
    raise ValueError("config.json 中未配置有效的用户")

# -------------------------------
# 工具函数
# -------------------------------
def get_md5(file_path):
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

# -------------------------------
# 上传或获取 URL
# -------------------------------
def upload_or_get(file_path):
    md5 = get_md5(file_path)
    params = {"username": USERNAME, "password": PASSWORD}

    # 1. 查询服务器是否已有图片
    try:
        r = requests.get(f"{SERVER}/info/{md5}", params=params)
        if r.status_code == 200:
            return r.json()
        elif r.status_code != 404:
            r.raise_for_status()
    except requests.RequestException as e:
        print(f"[WARN] 查询图片信息失败: {e}")

    # 2. 图片不存在服务器，则上传
    with open(file_path, "rb") as f:
        r = requests.post(f"{SERVER}/upload", files={"file": f}, params=params)
        r.raise_for_status()
    return r.json()

# -------------------------------
# 测试
# -------------------------------
if __name__ == "__main__":
    test_file = "example.png"
    info = upload_or_get(test_file)
    print("图片信息:")
    print(f"Status: {info.get('status')}")
    print(f"URL: {info.get('url')}")
    print(f"Original Name: {info.get('name')}")
    print(f"Size: {info.get('width')}x{info.get('height')}")
    print(f"Access Count: {info.get('access_count')}")
    print(f"Expire At: {info.get('expire_at')}")
