"""Image Proxy Client - 增强版本"""
import hashlib
import requests
import sqlite3
import os
import time
import logging
from pathlib import Path
import json
from typing import Optional, Dict, Any, List


class CacheManager:
    """客户端缓存管理器"""
    
    def __init__(self, cache_file: str = "client_cache.db"):
        self.cache_file = Path(cache_file)
        self.init_cache()
    
    def init_cache(self) -> None:
        """初始化缓存数据库"""
        with sqlite3.connect(self.cache_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    md5 TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    filename TEXT,
                    cached_at INTEGER NOT NULL,
                    access_count INTEGER DEFAULT 0
                )
            """)
            conn.commit()
    
    def get_cached_url(self, md5: str) -> Optional[str]:
        """获取缓存的URL"""
        with sqlite3.connect(self.cache_file) as conn:
            cursor = conn.execute(
                "SELECT url FROM cache WHERE md5 = ?", (md5,)
            )
            row = cursor.fetchone()
            if row:
                # 更新访问计数
                conn.execute(
                    "UPDATE cache SET access_count = access_count + 1 WHERE md5 = ?",
                    (md5,)
                )
                conn.commit()
                return row[0]
        return None
    
    def cache_url(self, md5: str, url: str, filename: str) -> None:
        """缓存URL"""
        with sqlite3.connect(self.cache_file) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache 
                (md5, url, filename, cached_at, access_count)
                VALUES (?, ?, ?, ?, 0)
            """, (md5, url, filename, int(time.time())))
            conn.commit()
    
    def clear_expired_cache(self, expire_days: int = 30) -> int:
        """清理过期缓存"""
        expire_time = int(time.time()) - expire_days * 86400
        with sqlite3.connect(self.cache_file) as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE cached_at < ?", (expire_time,)
            )
            conn.commit()
            return cursor.rowcount


class ImageProxyClient:
    """增强的图片代理客户端"""
    
    def __init__(self, config_file: Optional[str] = None, enable_cache: bool = True):
        # 初始化配置
        self.config = self._load_config(config_file)
        
        # 初始化缓存
        self.cache = CacheManager() if enable_cache else None
        
        # 初始化日志
        self.logger = self._setup_logger()
        
        # 初始化HTTP会话
        self.session = requests.Session()
        self.session.timeout = 30
        
        self.logger.info("图片代理客户端初始化完成")
    
    def _load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        if config_file is None:
            project_root = Path(__file__).resolve().parent.parent
            config_file = project_root / "config" / "config.json"
        
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"找不到配置文件: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 验证配置
        if not config.get("server", {}).get("domain"):
            raise ValueError("配置中缺少 server.domain")
        
        users = config.get("users", [])
        if not users or not users[0].get("username") or not users[0].get("password"):
            raise ValueError("配置中缺少有效的用户信息")
        
        return config
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("image_proxy_client")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    @property
    def server_url(self) -> str:
        """服务器URL"""
        return self.config['server']['domain'].rstrip('/')
    
    @property
    def username(self) -> str:
        """用户名"""
        return self.config["users"][0]["username"]
    
    @property
    def password(self) -> str:
        """密码"""
        return self.config["users"][0]["password"]
    
    def get_file_md5(self, file_path: str) -> str:
        """计算文件MD5"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def upload_or_get(self, file_path: str, use_cache: bool = True) -> Dict[str, Any]:
        """上传图片或获取已存在信息"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"error": f"文件不存在: {file_path}"}
            
            # 计算MD5
            md5 = self.get_file_md5(str(file_path))
            self.logger.info(f"处理文件: {file_path.name}, MD5: {md5}")
            
            # 检查本地缓存
            if use_cache and self.cache:
                cached_url = self.cache.get_cached_url(md5)
                if cached_url:
                    self.logger.info(f"使用缓存URL: {md5}")
                    return {
                        "url": cached_url,
                        "status": "cached",
                        "name": file_path.name
                    }
            
            # 准备请求参数
            params = {
                "username": self.username,
                "password": self.password
            }
            
            # 先查询服务器是否已有
            try:
                self.logger.debug(f"查询服务器图片信息: {md5}")
                response = self.session.get(
                    f"{self.server_url}/info/{md5}",
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # 缓存URL
                    if use_cache and self.cache and "url" in result:
                        self.cache.cache_url(md5, result["url"], file_path.name)
                    self.logger.info(f"服务器已有图片: {md5}")
                    return result
                    
                elif response.status_code == 403:
                    return {"error": "该用户权限不足，请联系管理员"}
                    
                elif response.status_code != 404:
                    return {"error": f"查询失败: {response.status_code} - {response.text}"}
                    
            except requests.RequestException as e:
                self.logger.warning(f"查询图片信息失败: {e}")
                # 继续尝试上传
            
            # 图片不存在，开始上传
            self.logger.info(f"开始上传文件: {file_path.name}")
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "application/octet-stream")}
                
                response = self.session.post(
                    f"{self.server_url}/upload",
                    files=files,
                    params=params,
                    timeout=60
                )
                
                if response.status_code == 403:
                    return {"error": "该用户权限不足，请联系管理员"}
                
                response.raise_for_status()
                result = response.json()
                
                # 缓存URL
                if use_cache and self.cache and "url" in result:
                    self.cache.cache_url(md5, result["url"], file_path.name)
                
                self.logger.info(f"上传成功: {file_path.name}")
                return result
                
        except requests.RequestException as e:
            error_msg = f"网络请求失败: {e}"
            self.logger.error(error_msg)
            return {"error": error_msg}
            
        except Exception as e:
            error_msg = f"处理失败: {e}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def get_image_url(self, file_path: str, use_cache: bool = True) -> str:
        """获取图片URL（简化接口）"""
        result = self.upload_or_get(file_path, use_cache)
        if "url" in result:
            return result["url"]
        elif "error" in result:
            return result["error"]
        return "未知错误"
    
    def close(self) -> None:
        """关闭客户端"""
        if self.session:
            self.session.close()
        self.logger.info("客户端已关闭")

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
    print("test_file: ", test_file)

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
