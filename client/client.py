import hashlib
import requests
import os
from pathlib import Path
import json
from typing import Optional, Dict

# -------------------------------
# 动态获取项目根目录
# -------------------------------
def get_project_root() -> Path:
    """获取项目根目录（假设 client/ 在项目根目录下）"""
    return Path(__file__).resolve().parent.parent

PROJECT_ROOT = get_project_root()
CONFIG_FILE = PROJECT_ROOT / "config" / "config.json"

# -------------------------------
# 读取配置
# -------------------------------
if not CONFIG_FILE.exists():
    raise FileNotFoundError(f"找不到配置文件: {CONFIG_FILE}")

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

SERVER = config['server']['domain'].rstrip('/')
USER_INFO = config.get("users", [{}])[0]
USERNAME = USER_INFO.get("username", "")
PASSWORD = USER_INFO.get("password", "")
if not USERNAME or not PASSWORD:
    raise ValueError("config.json 中未配置有效的用户信息")

# -------------------------------
# 工具函数
# -------------------------------
def get_md5(file_path: str) -> str:
    """计算文件 MD5"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

# -------------------------------
# 上传或获取 URL（原始接口）
# -------------------------------
def upload_or_get(file_path: str) -> Dict:
    """
    上传图片或获取已存在信息。
    返回字典，包含 status、url、name、width、height、access_count、expire_at 等信息，
    或 error 键表示失败。
    """
    md5 = get_md5(file_path)
    params = {"username": USERNAME, "password": PASSWORD}

    # 查询服务器是否已有图片
    try:
        r = requests.get(f"{SERVER}/info/{md5}", params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 403:
            return {"error": "该用户权限不足，请联系管理员"}
        elif r.status_code != 404:
            return {"error": f"查询失败: {r.status_code} {r.text}"}
    except requests.RequestException as e:
        return {"error": f"查询图片信息失败: {e}"}

    # 图片不存在，上传
    try:
        with open(file_path, "rb") as f:
            r = requests.post(f"{SERVER}/upload", files={"file": f}, params=params, timeout=30)
            if r.status_code == 403:
                return {"error": "该用户权限不足，请联系管理员"}
            r.raise_for_status()
            return r.json()
    except requests.RequestException as e:
        return {"error": f"上传失败: {e}"}

# -------------------------------
# 对外简化接口（只返回 URL 字符串）
# -------------------------------
def get_image_url(file_path: str) -> str:
    """
    输入图片路径，返回完整可访问 URL。
    权限不足或出错时，返回提示字符串。
    """
    info = upload_or_get(file_path)
    if "url" in info:
        return info["url"]
    elif "error" in info:
        return info["error"]
    return "未知错误"

# -------------------------------
# 测试
# -------------------------------
if __name__ == "__main__":
    # 示例本地测试文件
    test_file = PROJECT_ROOT / "example.png"

    # 原始字典接口
    info = upload_or_get(test_file)
    if "error" in info:
        print(info["error"])
    else:
        print("图片信息:")
        print(f"Status: {info.get('status')}")
        print(f"URL: {info.get('url')}")
        print(f"Original Name: {info.get('name')}")
        print(f"Size: {info.get('width')}x{info.get('height')}")
        print(f"Access Count: {info.get('access_count')}")
        print(f"Expire At: {info.get('expire_at')}")

    # 简化 URL 接口
    url = get_image_url(test_file)
    print(f"\n✅ 简化接口 URL: {url}")
