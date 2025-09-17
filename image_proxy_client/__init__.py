"""
Image Proxy Client - 第三方集成包
轻量级图片代理客户端，专为第三方项目集成设计

使用方法:
    from image_proxy_client import ImageProxyClient, quick_upload
    
    # 快速上传
    url = quick_upload("http://your-server.com", "username", "password", "image.jpg")
    
    # 使用客户端类
    with ImageProxyClient("http://your-server.com", "username", "password") as client:
        url = client.upload_image("image.jpg")

版本: 1.0.0
作者: Image Proxy Project
仓库: https://github.com/DpengYu/Image-Proxy-Project
"""

__version__ = "1.0.0"
__author__ = "Image Proxy Project"
__email__ = ""
__url__ = "https://github.com/DpengYu/Image-Proxy-Project"

from .client import ImageProxyClient, quick_upload
from .config import ImageProxyConfig, load_config_from_env

__all__ = [
    "ImageProxyClient",
    "quick_upload", 
    "ImageProxyConfig",
    "load_config_from_env"
]