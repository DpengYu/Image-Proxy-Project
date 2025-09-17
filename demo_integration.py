#!/usr/bin/env python3
"""
第三方集成演示脚本
展示如何在第三方项目中使用 image_proxy_client 包
"""

import os
import sys
from pathlib import Path

# 将image_proxy_client包添加到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def demo_basic_usage():
    """演示基本使用方法"""
    print("=== 演示1: 基本使用方法 ===")
    
    try:
        from image_proxy_client import quick_upload
        
        print("✅ 成功导入 image_proxy_client.quick_upload")
        print("使用方法:")
        print("""
from image_proxy_client import quick_upload

url = quick_upload(
    server_url="http://your-server.com:8000",
    username="your_username",
    password="your_password", 
    image_path="path/to/image.jpg"
)
print(f"图片URL: {url}")
        """)
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")


def demo_client_class():
    """演示客户端类使用"""
    print("\n=== 演示2: 客户端类使用 ===")
    
    try:
        from image_proxy_client import ImageProxyClient
        
        print("✅ 成功导入 ImageProxyClient")
        print("使用方法:")
        print("""
from image_proxy_client import ImageProxyClient

with ImageProxyClient("http://server.com", "user", "pass") as client:
    # 检查服务健康状态
    if client.is_healthy():
        print("✅ 服务正常")
        
        # 上传图片
        result = client.upload_image("image.jpg")
        print(f"图片URL: {result['url']}")
        print(f"MD5: {result['md5']}")
    else:
        print("❌ 服务异常")
        """)
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")


def demo_config_management():
    """演示配置管理"""
    print("\n=== 演示3: 配置管理 ===")
    
    try:
        from image_proxy_client import ImageProxyConfig
        from image_proxy_client.config import create_config_template
        
        print("✅ 成功导入配置管理模块")
        
        # 演示创建配置模板
        print("\n1. 创建配置文件模板:")
        print("""
from image_proxy_client.config import create_config_template
create_config_template("my_config.json")
        """)
        
        # 演示环境变量配置
        print("\n2. 环境变量配置:")
        print("""
import os

# 设置环境变量
os.environ['IMAGE_PROXY_URL'] = 'http://your-server.com:8000'
os.environ['IMAGE_PROXY_USERNAME'] = 'username'
os.environ['IMAGE_PROXY_PASSWORD'] = 'password'

# 自动从环境变量加载配置
from image_proxy_client import ImageProxyConfig
config = ImageProxyConfig()
client = config.get_client()
        """)
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")


def demo_environment_variables():
    """演示环境变量使用"""
    print("\n=== 演示4: 环境变量配置 ===")
    
    # 设置演示用的环境变量
    demo_env = {
        'IMAGE_PROXY_URL': 'http://demo-server.com:8000',
        'IMAGE_PROXY_USERNAME': 'demo_user',
        'IMAGE_PROXY_PASSWORD': 'demo_pass',
        'IMAGE_PROXY_TIMEOUT': '30',
        'IMAGE_PROXY_VERIFY_SSL': 'true'
    }
    
    # 临时设置环境变量
    for key, value in demo_env.items():
        os.environ[key] = value
    
    try:
        from image_proxy_client import ImageProxyConfig
        
        config = ImageProxyConfig()
        print("✅ 成功从环境变量加载配置:")
        print(f"  服务器地址: {config.get('server_url')}")
        print(f"  用户名: {config.get('username')}")
        print(f"  超时时间: {config.get('timeout')}")
        print(f"  SSL验证: {config.get('verify_ssl')}")
        
        print("\n环境变量配置的优势:")
        print("- ✅ 不会在代码中暴露敏感信息")
        print("- ✅ 支持不同环境的配置")
        print("- ✅ 遵循12-Factor App原则")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    finally:
        # 清理演示环境变量
        for key in demo_env.keys():
            os.environ.pop(key, None)


def demo_git_integration():
    """演示Git集成方式"""
    print("\n=== 演示5: Git集成方式 ===")
    
    print("推荐的Git集成方式:")
    print("\n1. Git Submodule + Sparse Checkout (推荐):")
    print("""
# 添加子模块
git submodule add https://github.com/DpengYu/Image-Proxy-Project.git third_party/image_proxy

# 配置稀疏检出，只获取客户端代码
cd third_party/image_proxy
git config core.sparseCheckout true
echo "image_proxy_client/*" > .git/info/sparse-checkout
git read-tree -m -u HEAD

# 在Python中使用
import sys
sys.path.insert(0, 'third_party/image_proxy')
from image_proxy_client import quick_upload
    """)
    
    print("\n2. 直接复制包:")
    print("""
# 克隆并复制
git clone https://github.com/DpengYu/Image-Proxy-Project.git temp
cp -r temp/image_proxy_client your_project/libs/
rm -rf temp

# 使用
sys.path.append('libs')
from image_proxy_client import ImageProxyClient
    """)
    
    print("\n3. Pip安装:")
    print("""
# 从Git仓库安装
pip install git+https://github.com/DpengYu/Image-Proxy-Project.git#subdirectory=image_proxy_client

# 直接使用
from image_proxy_client import quick_upload
    """)


def demo_best_practices():
    """演示最佳实践"""
    print("\n=== 演示6: 最佳实践 ===")
    
    print("1. 创建配置工具函数:")
    print("""
# utils/image_config.py
import os
from image_proxy_client import ImageProxyConfig

def get_image_client():
    config = ImageProxyConfig()
    
    # 验证必要的环境变量
    required_vars = ['IMAGE_PROXY_URL', 'IMAGE_PROXY_USERNAME', 'IMAGE_PROXY_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"缺少环境变量: {missing_vars}")
    
    return config.get_client()

# 在其他地方使用
from utils.image_config import get_image_client

def upload_avatar(image_path):
    client = get_image_client()
    return client.get_image_url(image_path)
    """)
    
    print("\n2. 错误处理:")
    print("""
def safe_upload_image(image_path):
    try:
        url = quick_upload(
            server_url=os.getenv('IMAGE_PROXY_URL'),
            username=os.getenv('IMAGE_PROXY_USERNAME'),
            password=os.getenv('IMAGE_PROXY_PASSWORD'),
            image_path=image_path
        )
        return url
    except FileNotFoundError:
        print(f"文件不存在: {image_path}")
        return None
    except ValueError as e:
        print(f"参数错误: {e}")
        return None
    except Exception as e:
        print(f"上传失败: {e}")
        return None
    """)


def main():
    """主演示函数"""
    print("🚀 Image Proxy Client 第三方集成演示")
    print("=" * 50)
    
    # 检查包是否存在
    package_path = Path(__file__).parent / "image_proxy_client"
    if not package_path.exists():
        print("❌ 未找到 image_proxy_client 包")
        print("请确保已正确获取了客户端代码")
        return
    
    print(f"✅ 找到客户端包: {package_path}")
    
    # 运行各个演示
    demo_basic_usage()
    demo_client_class()
    demo_config_management()
    demo_environment_variables()
    demo_git_integration()
    demo_best_practices()
    
    print("\n" + "=" * 50)
    print("📖 详细文档:")
    print("- 客户端包文档: image_proxy_client/README.md")
    print("- 集成指南: THIRD_PARTY_INTEGRATION.md")
    print("- 项目主页: https://github.com/DpengYu/Image-Proxy-Project")
    print("\n💡 提示: 推荐使用Git Submodule + 环境变量的方式")


if __name__ == "__main__":
    main()