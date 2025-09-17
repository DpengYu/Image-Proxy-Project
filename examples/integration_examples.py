"""
第三方项目集成示例
展示如何在不同类型的项目中集成Image Proxy服务
"""
import os
import sys
from pathlib import Path

# 添加客户端路径
sys.path.insert(0, str(Path(__file__).parent.parent / "client"))

try:
    # 在此处添加您的客户端包路径
    sys.path.insert(0, str(Path(__file__).parent.parent / "image_proxy_client"))
    from image_proxy_client import quick_upload, ImageProxyClient
    CLIENT_AVAILABLE = True
except ImportError:
    CLIENT_AVAILABLE = False
    print("⚠️ 客户端不可用，请检查 image_proxy_client 包")


def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===")
    
    if not CLIENT_AVAILABLE:
        return
    
    # 使用环境变量配置（推荐）
    import os
    os.environ['IMAGE_PROXY_URL'] = "http://localhost:8000"
    os.environ['IMAGE_PROXY_USERNAME'] = "admin"
    os.environ['IMAGE_PROXY_PASSWORD'] = "admin123"
    
    # 上传图片（需要准备测试图片）
    test_image = Path(__file__).parent.parent / "test_image.png"  # 您需要准备这个文件
    if test_image.exists():
        url = quick_upload(
            os.environ['IMAGE_PROXY_URL'],
            os.environ['IMAGE_PROXY_USERNAME'], 
            os.environ['IMAGE_PROXY_PASSWORD'],
            str(test_image)
        )
        if url:
            print(f"✅ 上传成功: {url}")
        else:
            print("❌ 上传失败")
    else:
        print("⚠️ 测试图片不存在，请准备 test_image.png")


def example_batch_upload():
    """批量上传示例"""
    print("\n=== 批量上传示例 ===")
    
    if not SIMPLE_CLIENT_AVAILABLE:
        return
    
    with SimpleImageProxy("http://localhost:8000", "admin", "admin123") as client:
        # 模拟批量上传
        image_files = ["img1.jpg", "img2.png", "img3.gif"]
        
        for image_file in image_files:
            # 这里是模拟，实际使用时替换为真实文件路径
            print(f"📤 准备上传: {image_file}")
            # url = client.upload_image(image_file)
            # if url:
            #     print(f"✅ {image_file} -> {url}")
            # else:
            #     print(f"❌ {image_file} 上传失败")


def example_web_framework():
    """Web框架集成示例"""
    print("\n=== Web框架集成示例 ===")
    
    # Flask示例
    flask_code = '''
from flask import Flask, request, jsonify
from image_proxy_simple import setup_image_proxy, upload_image

app = Flask(__name__)

# 配置图片代理服务
setup_image_proxy("http://localhost:8000", "admin", "admin123")

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """上传图片API"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    
    # 保存临时文件
    temp_path = f"temp_{file.filename}"
    file.save(temp_path)
    
    try:
        # 上传到图片代理服务
        url = upload_image(temp_path)
        if url:
            return jsonify({'success': True, 'url': url})
        else:
            return jsonify({'error': '上传失败'}), 500
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    app.run(debug=True)
'''
    
    print("Flask集成代码:")
    print(flask_code)
    
    # Django示例
    django_code = '''
# Django views.py
from django.http import JsonResponse
from django.views import View
from image_proxy_simple import setup_image_proxy, upload_image

# 在settings.py或__init__.py中配置
setup_image_proxy("http://localhost:8000", "admin", "admin123")

class ImageUploadView(View):
    def post(self, request):
        if 'file' not in request.FILES:
            return JsonResponse({'error': '没有文件'}, status=400)
        
        file = request.FILES['file']
        
        # 保存临时文件
        temp_path = f"temp_{file.name}"
        with open(temp_path, 'wb+') as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
        
        try:
            url = upload_image(temp_path)
            if url:
                return JsonResponse({'success': True, 'url': url})
            else:
                return JsonResponse({'error': '上传失败'}, status=500)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
'''
    
    print("\nDjango集成代码:")
    print(django_code)


def example_cli_tool():
    """命令行工具示例"""
    print("\n=== 命令行工具示例 ===")
    
    cli_script = '''#!/usr/bin/env python3
"""
图片上传命令行工具
用法: python image_upload_cli.py <image_file>
"""
import sys
import argparse
from pathlib import Path
from image_proxy_simple import setup_image_proxy, upload_image

def main():
    parser = argparse.ArgumentParser(description='图片上传工具')
    parser.add_argument('image', help='图片文件路径')
    parser.add_argument('--server', default='http://localhost:8000', help='服务器地址')
    parser.add_argument('--username', default='admin', help='用户名')
    parser.add_argument('--password', default='admin123', help='密码')
    
    args = parser.parse_args()
    
    # 检查文件
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"❌ 文件不存在: {image_path}")
        return 1
    
    # 配置服务
    setup_image_proxy(args.server, args.username, args.password)
    
    # 上传图片
    print(f"📤 正在上传: {image_path.name}")
    url = upload_image(str(image_path))
    
    if url:
        print(f"✅ 上传成功!")
        print(f"🔗 URL: {url}")
        return 0
    else:
        print("❌ 上传失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())
'''
    
    print("命令行工具代码:")
    print(cli_script)


def example_background_task():
    """后台任务示例"""
    print("\n=== 后台任务示例 ===")
    
    celery_task = '''
# Celery任务示例
from celery import Celery
from image_proxy_simple import setup_image_proxy, upload_image

app = Celery('image_processor')

# 配置图片代理服务
setup_image_proxy("http://localhost:8000", "admin", "admin123")

@app.task
def process_and_upload_image(image_path, user_id):
    """异步处理并上传图片"""
    try:
        # 这里可以添加图片处理逻辑
        # 如: 压缩、裁剪、添加水印等
        
        # 上传到图片代理服务
        url = upload_image(image_path)
        
        if url:
            # 保存URL到数据库
            # save_image_url_to_db(user_id, url)
            return {'success': True, 'url': url}
        else:
            return {'success': False, 'error': '上传失败'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

# 使用示例
# result = process_and_upload_image.delay('/path/to/image.jpg', user_id=123)
'''
    
    print("Celery后台任务代码:")
    print(celery_task)


def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    error_handling_code = '''
from image_proxy_simple import SimpleImageProxy
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_with_retry(image_path, max_retries=3):
    """带重试的上传函数"""
    
    client = SimpleImageProxy("http://localhost:8000", "admin", "admin123")
    
    for attempt in range(max_retries):
        try:
            # 检查服务健康状态
            if not client.is_healthy():
                logger.warning(f"服务不健康，重试 {attempt + 1}/{max_retries}")
                time.sleep(2 ** attempt)  # 指数退避
                continue
            
            # 尝试上传
            url = client.upload_image(image_path)
            if url:
                logger.info(f"上传成功: {url}")
                return url
            else:
                logger.warning(f"上传失败，重试 {attempt + 1}/{max_retries}")
                
        except Exception as e:
            logger.error(f"上传异常: {e}, 重试 {attempt + 1}/{max_retries}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    logger.error("所有重试均失败")
    return None

# 使用示例
url = upload_with_retry("/path/to/image.jpg")
if url:
    print(f"最终上传成功: {url}")
else:
    print("上传最终失败")
'''
    
    print("错误处理代码:")
    print(error_handling_code)


def example_config_management():
    """配置管理示例"""
    print("\n=== 配置管理示例 ===")
    
    config_code = '''
# config.py - 项目配置管理
import os
from image_proxy_simple import setup_image_proxy

class ImageProxyConfig:
    """图片代理配置管理"""
    
    def __init__(self):
        # 从环境变量读取配置
        self.server_url = os.getenv('IMAGE_PROXY_URL', 'http://localhost:8000')
        self.username = os.getenv('IMAGE_PROXY_USER', 'admin')
        self.password = os.getenv('IMAGE_PROXY_PASS', 'admin123')
        self.timeout = int(os.getenv('IMAGE_PROXY_TIMEOUT', '30'))
        
    def setup(self):
        """初始化图片代理服务"""
        setup_image_proxy(
            server_url=self.server_url,
            username=self.username,
            password=self.password,
            timeout=self.timeout
        )
        print(f"图片代理服务已配置: {self.server_url}")

# 使用示例
config = ImageProxyConfig()
config.setup()

# 环境变量配置示例
# export IMAGE_PROXY_URL="https://img.yourcompany.com"
# export IMAGE_PROXY_USER="your_username"
# export IMAGE_PROXY_PASS="your_password"
'''
    
    print("配置管理代码:")
    print(config_code)


def main():
    """运行所有示例"""
    print("🎯 Image Proxy Project 第三方集成示例")
    print("=" * 50)
    
    example_basic_usage()
    example_batch_upload()
    example_web_framework()
    example_cli_tool()
    example_background_task()
    example_error_handling()
    example_config_management()
    
    print("\n" + "=" * 50)
    print("📚 更多集成方式：")
    print("1. 复制 client/image_proxy_simple.py 到您的项目")
    print("2. 根据需要修改配置和错误处理")
    print("3. 参考上述示例代码进行集成")
    print("4. 查看完整文档: README.md")


if __name__ == "__main__":
    main()