"""
Image Proxy Client - 核心客户端类
提供图片上传和管理功能的轻量级客户端
"""

import requests
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Union
import logging

# 禁用requests的警告
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

logger = logging.getLogger(__name__)


class ImageProxyClient:
    """
    图片代理客户端
    
    用于与Image Proxy服务器进行交互，上传图片并获取访问URL
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
            server_url: 服务器地址 (如: http://your-server.com:8000)
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
    
    def upload_image(self, image_path: Union[str, Path]) -> Dict[str, Any]:
        """
        上传图片到服务器
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            包含url、md5等信息的字典
            
        Raises:
            FileNotFoundError: 文件不存在
            requests.RequestException: 网络请求异常
            ValueError: 服务器响应异常
            
        Example:
            >>> client = ImageProxyClient("http://server.com", "user", "pass")
            >>> result = client.upload_image("image.jpg")
            >>> print(result['url'])
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        if not image_path.is_file():
            raise ValueError(f"路径不是文件: {image_path}")
        
        # 准备请求参数
        params = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            with open(image_path, 'rb') as f:
                files = {"file": (image_path.name, f, "application/octet-stream")}
                
                response = self.session.post(
                    f"{self.server_url}/upload",
                    files=files,
                    params=params,
                    timeout=self.timeout
                )
            
            # 检查响应状态
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise ValueError("认证失败: 用户名或密码错误")
            elif response.status_code == 413:
                raise ValueError("文件过大")
            elif response.status_code == 415:
                raise ValueError("不支持的文件类型")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', f'HTTP {response.status_code}')
                except:
                    error_msg = f'HTTP {response.status_code}: {response.text}'
                raise ValueError(f"上传失败: {error_msg}")
                
        except requests.RequestException as e:
            raise requests.RequestException(f"网络请求失败: {e}")
    
    def get_image_url(self, image_path: Union[str, Path]) -> str:
        """
        上传图片并直接返回URL (简化接口)
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            图片访问URL
            
        Example:
            >>> client = ImageProxyClient("http://server.com", "user", "pass") 
            >>> url = client.get_image_url("image.jpg")
            >>> print(url)
        """
        result = self.upload_image(image_path)
        url = result.get('url')
        if not url:
            raise ValueError("服务器未返回图片URL")
        return url
    
    def get_image_info(self, md5: str) -> Dict[str, Any]:
        """
        获取图片信息
        
        Args:
            md5: 图片MD5值
            
        Returns:
            图片信息字典
        """
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
        elif response.status_code == 404:
            raise ValueError("图片不存在")
        elif response.status_code == 401:
            raise ValueError("认证失败")
        else:
            raise ValueError(f"获取信息失败: HTTP {response.status_code}")
    
    def is_healthy(self) -> bool:
        """
        检查服务健康状态
        
        Returns:
            服务是否正常运行
        """
        try:
            response = self.session.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def close(self):
        """关闭连接，释放资源"""
        if hasattr(self, 'session') and self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def quick_upload(server_url: str, username: str, password: str, 
                image_path: str, timeout: int = 30) -> str:
    """
    快速上传函数 - 单行调用接口
    
    Args:
        server_url: 服务器地址
        username: 用户名
        password: 密码
        image_path: 图片路径
        timeout: 超时时间
        
    Returns:
        图片URL
        
    Example:
        >>> from image_proxy_client import quick_upload
        >>> url = quick_upload("http://server.com", "user", "pass", "image.jpg")
        >>> print(f"图片URL: {url}")
    """
    client = ImageProxyClient(server_url, username, password, timeout)
    try:
        return client.get_image_url(image_path)
    finally:
        client.close()


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