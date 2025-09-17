#!/usr/bin/env python3
"""
Image Proxy Client - 独立单文件客户端
专为第三方用户快速获取转URL工具设计

使用方法:
1. 命令行: python image_proxy_client.py -s http://your-server.com -u username -p password /path/to/image.jpg
2. 模块导入: from image_proxy_client import quick_upload
3. 配置文件: 创建 client_config.json 配置后直接使用

版本: 1.0.0
依赖: requests (pip install requests)
"""

import sys
import os
import json
import argparse
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Union

try:
    import requests
except ImportError:
    print("❌ 缺少依赖: requests")
    print("请运行: pip install requests")
    sys.exit(1)

# 禁用SSL警告
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass


class ImageProxyClient:
    """独立的图片代理客户端"""
    
    def __init__(self, server_url: str, username: str, password: str, 
                 timeout: int = 30, verify_ssl: bool = True):
        """
        初始化客户端
        
        Args:
            server_url: 服务器地址 (如: http://localhost:8000)
            username: 用户名
            password: 密码
            timeout: 超时时间(秒)
            verify_ssl: 是否验证SSL证书
        """
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        self.session = requests.Session()
        self.session.verify = verify_ssl
    
    def upload_image(self, image_path: Union[str, Path]) -> Dict[str, Any]:
        """
        上传图片
        
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
    
    def get_image_url(self, image_path: Union[str, Path]) -> str:
        """
        上传图片并直接返回URL字符串 (简化接口)
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            图片访问URL
            
        Raises:
            同 upload_image()
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
        """检查服务健康状态"""
        try:
            response = self.session.get(f"{self.server_url}/health", timeout=5)
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


def calculate_md5(file_path: Union[str, Path]) -> str:
    """计算文件MD5值"""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def load_config(config_file: str = "client_config.json") -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置字典
    """
    config_path = Path(config_file)
    if not config_path.exists():
        # 创建默认配置
        default_config = {
            "server_url": "http://localhost:8000",
            "username": "admin", 
            "password": "password123",
            "timeout": 30,
            "verify_ssl": True
        }
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            print(f"✅ 已创建默认配置文件: {config_path}")
            print("请编辑配置文件后重新运行")
        except Exception as e:
            print(f"❌ 创建配置文件失败: {e}")
        return default_config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        sys.exit(1)


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
        >>> url = quick_upload("http://localhost:8000", "admin", "pass123", "image.jpg")
        >>> print(f"图片URL: {url}")
    """
    client = ImageProxyClient(server_url, username, password, timeout)
    try:
        return client.get_image_url(image_path)
    finally:
        client.close()


def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(
        description="Image Proxy Client - 图片转URL工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s -s http://localhost:8000 -u admin -p password123 image.jpg
  %(prog)s --config my_config.json image.jpg
  %(prog)s --health -s http://localhost:8000
  
配置文件格式 (client_config.json):
{
  "server_url": "http://localhost:8000",
  "username": "admin",
  "password": "password123", 
  "timeout": 30,
  "verify_ssl": true
}
        """
    )
    
    # 服务器配置
    parser.add_argument("-s", "--server", help="服务器地址 (如: http://localhost:8000)")
    parser.add_argument("-u", "--username", help="用户名")
    parser.add_argument("-p", "--password", help="密码")
    parser.add_argument("-t", "--timeout", type=int, default=30, help="超时时间(秒)")
    parser.add_argument("--no-ssl-verify", action="store_true", help="跳过SSL证书验证")
    
    # 配置文件
    parser.add_argument("-c", "--config", help="配置文件路径 (默认: client_config.json)")
    
    # 操作参数
    parser.add_argument("image_path", nargs="?", help="图片文件路径")
    parser.add_argument("--health", action="store_true", help="检查服务健康状态")
    parser.add_argument("--info", help="获取指定MD5的图片信息")
    parser.add_argument("--md5", help="计算文件MD5值")
    
    # 输出选项
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式，只输出结果")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出")
    
    args = parser.parse_args()
    
    # 处理MD5计算
    if args.md5:
        try:
            md5_value = calculate_md5(args.md5)
            if args.quiet:
                print(md5_value)
            else:
                print(f"文件 {args.md5} 的MD5: {md5_value}")
        except Exception as e:
            print(f"❌ 计算MD5失败: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    # 获取配置
    config = {}
    if args.config or (not args.server and not args.health):
        config_file = args.config or "client_config.json"
        config = load_config(config_file)
    
    # 构建客户端参数
    server_url = args.server or config.get("server_url")
    username = args.username or config.get("username")
    password = args.password or config.get("password")
    timeout = args.timeout if args.timeout != 30 else config.get("timeout", 30)
    verify_ssl = not args.no_ssl_verify and config.get("verify_ssl", True)
    
    # 验证必要参数
    if not server_url:
        print("❌ 缺少服务器地址，请使用 -s 参数或配置文件", file=sys.stderr)
        sys.exit(1)
    
    # 创建客户端
    if args.health:
        # 健康检查不需要认证信息
        client = ImageProxyClient(server_url, "", "", timeout, verify_ssl)
    else:
        if not username or not password:
            print("❌ 缺少用户名或密码，请使用 -u/-p 参数或配置文件", file=sys.stderr)
            sys.exit(1)
        # 确保参数不为None
        username = username or ""
        password = password or ""
        client = ImageProxyClient(server_url, username, password, timeout, verify_ssl)
    
    try:
        # 健康检查
        if args.health:
            is_healthy = client.is_healthy()
            if args.json:
                print(json.dumps({"healthy": is_healthy}, ensure_ascii=False))
            elif args.quiet:
                print("OK" if is_healthy else "ERROR")
            else:
                print(f"服务状态: {'✅ 正常' if is_healthy else '❌ 异常'}")
            sys.exit(0 if is_healthy else 1)
        
        # 获取图片信息
        if args.info:
            try:
                info = client.get_image_info(args.info)
                if args.json:
                    print(json.dumps(info, ensure_ascii=False, indent=2))
                else:
                    print(f"图片信息 (MD5: {args.info}):")
                    for key, value in info.items():
                        print(f"  {key}: {value}")
            except Exception as e:
                if not args.quiet:
                    print(f"❌ 获取图片信息失败: {e}", file=sys.stderr)
                sys.exit(1)
            return
        
        # 上传图片
        if not args.image_path:
            print("❌ 请指定图片文件路径", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        
        if not args.quiet:
            print(f"正在上传图片: {args.image_path}")
        
        try:
            result = client.upload_image(args.image_path)
            
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            elif args.quiet:
                print(result.get('url', ''))
            else:
                print(f"✅ 上传成功!")
                print(f"图片URL: {result.get('url')}")
                print(f"MD5: {result.get('md5')}")
                if result.get('cached'):
                    print("ℹ️  文件已存在缓存中")
                
        except Exception as e:
            if not args.quiet:
                print(f"❌ 上传失败: {e}", file=sys.stderr)
            sys.exit(1)
            
    finally:
        client.close()


if __name__ == "__main__":
    main()