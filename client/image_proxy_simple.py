"""
Image Proxy Project - 第三方调用便捷接口
简化外部项目接入图片代理服务的复杂度
"""
import requests
import hashlib
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
import logging

# 禁用requests的警告
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass  # urllib3不可用时忽略

logger = logging.getLogger(__name__)


class SimpleImageProxy:
    """
    简化的图片代理客户端
    专为第三方项目快速集成设计
    """
    
    def __init__(self, 
                 server_url: str,
                 username: str,
                 password: str,
                 timeout: int = 30,
                 verify_ssl: bool = True):
        """
        初始化客户端
        
        Args:
            server_url: 服务器地址，如 "https://your-domain.com"
            username: 用户名
            password: 密码
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证SSL证书
        """
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # 创建session复用连接
        self.session = requests.Session()
        self.session.verify = verify_ssl
    
    def upload_image(self, image_path: Union[str, Path]) -> Optional[str]:
        """
        上传图片并返回URL
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            图片访问URL，失败时返回None
            
        Example:
            >>> proxy = SimpleImageProxy("https://img.example.com", "user", "pass")
            >>> url = proxy.upload_image("/path/to/image.jpg")
            >>> print(url)  # https://img.example.com/secure_get/abc123?token=xyz
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                logger.error(f"图片文件不存在: {image_path}")
                return None
            
            # 准备上传参数
            params = {
                "username": self.username,
                "password": self.password
            }
            
            with open(image_path, 'rb') as f:
                files = {"file": (image_path.name, f, "application/octet-stream")}
                
                response = self.session.post(
                    f"{self.server_url}/upload",
                    files=files,
                    params=params,
                    timeout=self.timeout
                )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('url')
            else:
                logger.error(f"上传失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"上传异常: {e}")
            return None
    
    def get_image_info(self, md5: str) -> Optional[Dict[str, Any]]:
        """
        获取图片信息
        
        Args:
            md5: 图片MD5值
            
        Returns:
            图片信息字典，失败时返回None
        """
        try:
            params = {
                "username": self.username,
                "password": self.password
            }
            
            response = self.session.get(
                f"{self.server_url}/info/{md5}",
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取图片信息失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取图片信息异常: {e}")
            return None
    
    def is_healthy(self) -> bool:
        """
        检查服务是否健康
        
        Returns:
            服务是否正常
        """
        try:
            response = self.session.get(
                f"{self.server_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def close(self):
        """关闭连接"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ImageProxyConfig:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "image_proxy_config.json"
        self.config = self._load_or_create_config()
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """加载或创建配置文件"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")
        
        # 创建默认配置
        default_config = {
            "server_url": "http://localhost:8000",
            "username": "admin",
            "password": "password123",
            "timeout": 30,
            "verify_ssl": True
        }
        
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def get_client(self) -> SimpleImageProxy:
        """根据配置创建客户端"""
        return SimpleImageProxy(
            server_url=self.config["server_url"],
            username=self.config["username"],
            password=self.config["password"],
            timeout=self.config.get("timeout", 30),
            verify_ssl=self.config.get("verify_ssl", True)
        )


# 全局便捷函数
_default_client: Optional[SimpleImageProxy] = None
_default_config: Optional[ImageProxyConfig] = None


def setup_image_proxy(server_url: str, username: str, password: str, **kwargs):
    """
    全局配置图片代理服务
    
    Args:
        server_url: 服务器地址
        username: 用户名
        password: 密码
        **kwargs: 其他配置参数
    
    Example:
        >>> from image_proxy_simple import setup_image_proxy, upload_image
        >>> setup_image_proxy("https://img.example.com", "user", "pass")
        >>> url = upload_image("/path/to/image.jpg")
    """
    global _default_client
    if _default_client:
        _default_client.close()
    
    _default_client = SimpleImageProxy(
        server_url=server_url,
        username=username,
        password=password,
        **kwargs
    )


def setup_from_config(config_file: Optional[str] = None):
    """
    从配置文件设置图片代理服务
    
    Args:
        config_file: 配置文件路径
    
    Example:
        >>> from image_proxy_simple import setup_from_config, upload_image
        >>> setup_from_config("my_config.json")
        >>> url = upload_image("/path/to/image.jpg")
    """
    global _default_client, _default_config
    
    _default_config = ImageProxyConfig(config_file)
    if _default_client:
        _default_client.close()
    
    _default_client = _default_config.get_client()


def upload_image(image_path: Union[str, Path]) -> Optional[str]:
    """
    上传图片的便捷函数
    
    Args:
        image_path: 图片路径
        
    Returns:
        图片URL或None
        
    Example:
        >>> url = upload_image("/path/to/image.jpg")
        >>> if url:
        >>>     print(f"图片URL: {url}")
    """
    if not _default_client:
        raise RuntimeError("请先调用 setup_image_proxy() 或 setup_from_config() 进行配置")
    
    return _default_client.upload_image(image_path)


def get_image_info(md5: str) -> Optional[Dict[str, Any]]:
    """
    获取图片信息的便捷函数
    
    Args:
        md5: 图片MD5
        
    Returns:
        图片信息字典或None
    """
    if not _default_client:
        raise RuntimeError("请先调用 setup_image_proxy() 或 setup_from_config() 进行配置")
    
    return _default_client.get_image_info(md5)


def is_service_healthy() -> bool:
    """
    检查服务健康状态的便捷函数
    
    Returns:
        服务是否正常
    """
    if not _default_client:
        return False
    
    return _default_client.is_healthy()


# 计算文件MD5的工具函数
def calculate_md5(file_path: Union[str, Path]) -> str:
    """
    计算文件MD5值
    
    Args:
        file_path: 文件路径
        
    Returns:
        MD5字符串
    """
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


if __name__ == "__main__":
    # 示例用法
    print("Image Proxy Simple Client 示例")
    
    # 方法1: 直接配置
    print("\n=== 方法1: 直接配置 ===")
    setup_image_proxy("http://localhost:8000", "admin", "password123")
    
    # 检查服务
    if is_service_healthy():
        print("✅ 服务正常")
    else:
        print("❌ 服务不可用")
    
    # 方法2: 使用配置文件
    print("\n=== 方法2: 配置文件 ===")
    # setup_from_config("config.json")
    
    # 方法3: 直接使用客户端
    print("\n=== 方法3: 直接使用客户端 ===")
    with SimpleImageProxy("http://localhost:8000", "admin", "password123") as client:
        print(f"服务状态: {'正常' if client.is_healthy() else '异常'}")