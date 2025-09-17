"""Image Proxy Client - 统一客户端"""
import hashlib
import requests
import os
import logging
from pathlib import Path
import json
from typing import Optional, Dict, Any, Union


"""Image Proxy Client - 统一客户端"""
import hashlib
import requests
import os
import logging
from pathlib import Path
import json
from typing import Optional, Dict, Any, Union

# 禁用requests的警告
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except (ImportError, AttributeError):
    pass


class ImageProxyClient:
    """
    图片代理客户端
    
    用于与Image Proxy服务器进行交互，上传图片并获取访问URL
    """
    
    def __init__(self, 
                 server_url: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 config_file: Optional[str] = None,
                 timeout: int = 30,
                 verify_ssl: bool = True):
        """
        初始化客户端
        
        Args:
            server_url: 服务器地址 (如: http://your-server.com:8000)
            username: 用户名
            password: 密码
            config_file: 配置文件路径，优先级低于直接参数
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证SSL证书
        """
        # 初始化配置
        if server_url and username and password:
            # 使用直接参数
            self.server_url = server_url.rstrip('/')
            self.username = username
            self.password = password
        else:
            # 从配置文件加载
            config = self._load_config(config_file)
            self.server_url = config['server']['domain'].rstrip('/')
            self.username = config["users"][0]["username"]
            self.password = config["users"][0]["password"]
        
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # 创建session复用连接
        self.session = requests.Session()
        self.session.verify = verify_ssl
        
        # 初始化日志
        self.logger = self._setup_logger()
        
        self.logger.info("图片代理客户端初始化完成")
    
    def _load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        if config_file is None:
            project_root = Path(__file__).resolve().parent.parent
            config_file = str(project_root / "config" / "config.json")
        
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
    
    def get_file_md5(self, file_path: Union[str, Path]) -> str:
        """计算文件MD5"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
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
    
    def upload_or_get(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """上传图片或获取已存在信息"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"error": f"文件不存在: {file_path}"}
            
            # 计算MD5
            md5 = self.get_file_md5(file_path)
            self.logger.info(f"处理文件: {file_path.name}, MD5: {md5}")
            
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
            return self.upload_image(file_path)
                
        except requests.RequestException as e:
            error_msg = f"网络请求失败: {e}"
            self.logger.error(error_msg)
            return {"error": error_msg}
            
        except Exception as e:
            error_msg = f"处理失败: {e}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def get_image_url(self, image_path: Union[str, Path]) -> str:
        """
        上传图片并直接返回URL (简化接口)
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            图片访问URL
        """
        result = self.upload_or_get(image_path)
        if "url" in result:
            return result["url"]
        elif "error" in result:
            return result["error"]
        return "未知错误"
    
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
        self.logger.info("客户端已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# -------------------------------
# 便捷函数
# -------------------------------

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
        >>> url = quick_upload("http://server.com", "user", "pass", "image.jpg")
        >>> print(f"图片URL: {url}")
    """
    client = ImageProxyClient(server_url, username, password, timeout=timeout)
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


# -------------------------------
# 兼容接口（使用配置文件）
# -------------------------------

def upload_or_get(file_path: str, config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    上传图片或获取已存在信息。
    返回字典，包含 status、url、name、width、height、access_count、expire_at 等信息，
    或 error 键表示失败。
    """
    client = ImageProxyClient(config_file=config_file)
    try:
        return client.upload_or_get(file_path)
    finally:
        client.close()


def get_image_url(file_path: str, config_file: Optional[str] = None) -> str:
    """
    输入图片路径，返回完整可访问 URL。
    权限不足或出错时，返回提示字符串。
    """
    client = ImageProxyClient(config_file=config_file)
    try:
        return client.get_image_url(file_path)
    finally:
        client.close()


# -------------------------------
# 测试
# -------------------------------
if __name__ == "__main__":
    print("请准备您自己的测试图片文件，然后修改以下示例代码:")
    print("test_file = Path('your_image.png')")
    print("暂时禁用测试代码，请手动配置图片路径")
    
    # 取消注释以下代码并更改图片路径
    # test_file = Path("your_image.png")
    # if test_file.exists():
    #     info = upload_or_get(str(test_file))
    #     if "error" in info:
    #         print(info["error"])
    #     else:
    #         print("图片信息:")
    #         print(f"Status: {info.get('status')}")
    #         print(f"URL: {info.get('url')}")
    #         print(f"Original Name: {info.get('name')}")
    #         print(f"Size: {info.get('width')}x{info.get('height')}")
    #         print(f"Access Count: {info.get('access_count')}")
    #         print(f"Expire At: {info.get('expire_at')}")
    #
    #     url = get_image_url(str(test_file))
    #     print(f"\n✅ 简化接口 URL: {url}")
    # else:
    #     print("测试图片不存在，请准备一个图片文件")
