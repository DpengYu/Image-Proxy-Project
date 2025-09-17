# Image Proxy Client

轻量级图片代理客户端，专为第三方项目集成设计。提供简单易用的API来上传图片并获取访问URL。

## 🚀 快速开始

### 安装方式

#### 方式1: 通过Git Submodule (推荐)

```bash
# 添加为子模块
git submodule add https://github.com/DpengYu/Image-Proxy-Project.git image_proxy
cd image_proxy
git sparse-checkout init --cone
git sparse-checkout set image_proxy_client

# 在你的项目中使用
sys.path.append('image_proxy')
from image_proxy_client import quick_upload
```

#### 方式2: 直接复制

```bash
# 克隆仓库
git clone https://github.com/DpengYu/Image-Proxy-Project.git
cd Image-Proxy-Project

# 复制客户端包到你的项目
cp -r image_proxy_client /path/to/your/project/
```

#### 方式3: Pip安装 (需要打包)

```bash
pip install git+https://github.com/DpengYu/Image-Proxy-Project.git#subdirectory=image_proxy_client
```

### 基本使用

#### 1. 快速上传 (推荐)

```python
from image_proxy_client import quick_upload

# 一行代码上传图片
url = quick_upload(
    server_url="http://your-server.com:8000",
    username="your_username", 
    password="your_password",
    image_path="path/to/image.jpg"
)
print(f"图片URL: {url}")
```

#### 2. 使用客户端类

```python
from image_proxy_client import ImageProxyClient

# 创建客户端
with ImageProxyClient("http://your-server.com:8000", "username", "password") as client:
    # 上传图片
    result = client.upload_image("image.jpg")
    print(f"图片URL: {result['url']}")
    print(f"MD5: {result['md5']}")
    
    # 检查服务状态
    if client.is_healthy():
        print("✅ 服务正常")
```

#### 3. 使用配置文件

```python
from image_proxy_client import ImageProxyConfig

# 创建配置文件模板
from image_proxy_client.config import create_config_template
create_config_template("my_config.json")

# 编辑配置文件后使用
config = ImageProxyConfig("my_config.json")
client = config.get_client()

url = client.get_image_url("image.jpg")
```

#### 4. 使用环境变量

```python
import os
from image_proxy_client import load_config_from_env, ImageProxyConfig

# 设置环境变量
os.environ['IMAGE_PROXY_URL'] = 'http://your-server.com:8000'
os.environ['IMAGE_PROXY_USERNAME'] = 'username'
os.environ['IMAGE_PROXY_PASSWORD'] = 'password'

# 从环境变量加载配置
config = ImageProxyConfig()
client = config.get_client()

url = client.get_image_url("image.jpg")
```

## 📖 API文档

### ImageProxyClient

主要的客户端类，提供所有图片操作功能。

#### 初始化参数

- `server_url`: 服务器地址
- `username`: 用户名
- `password`: 密码  
- `timeout`: 超时时间（秒），默认30
- `verify_ssl`: 是否验证SSL证书，默认True

#### 主要方法

- `upload_image(image_path)`: 上传图片，返回详细信息
- `get_image_url(image_path)`: 上传图片，直接返回URL
- `get_image_info(md5)`: 根据MD5获取图片信息
- `is_healthy()`: 检查服务健康状态

### 便捷函数

- `quick_upload(server_url, username, password, image_path)`: 快速上传
- `load_config_from_env()`: 从环境变量加载配置

## 🔧 配置文件格式

```json
{
  "server_url": "http://your-server.com:8000",
  "username": "your_username",
  "password": "your_password", 
  "timeout": 30,
  "verify_ssl": true
}
```

## 🌍 环境变量

支持以下环境变量：

- `IMAGE_PROXY_URL`: 服务器地址
- `IMAGE_PROXY_USERNAME`: 用户名
- `IMAGE_PROXY_PASSWORD`: 密码
- `IMAGE_PROXY_TIMEOUT`: 超时时间
- `IMAGE_PROXY_VERIFY_SSL`: 是否验证SSL (true/false)

## 📋 依赖要求

- Python >= 3.7
- requests >= 2.25.0
- urllib3 >= 1.26.0

## 🎯 集成示例

### Flask Web应用集成

```python
from flask import Flask, request, jsonify
from image_proxy_client import quick_upload

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': '未找到图片文件'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 保存临时文件
    temp_path = f"/tmp/{file.filename}"
    file.save(temp_path)
    
    try:
        # 上传到图片代理服务
        url = quick_upload(
            "http://image-server.com:8000",
            "api_user",
            "api_password", 
            temp_path
        )
        return jsonify({'url': url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.unlink(temp_path)  # 清理临时文件
```

### Django项目集成

```python
# settings.py
import os
from image_proxy_client import ImageProxyConfig

# 图片代理配置
IMAGE_PROXY_CONFIG = ImageProxyConfig()

# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        
        # 保存临时文件
        temp_path = f"/tmp/{image_file.name}"
        with open(temp_path, 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)
        
        try:
            client = settings.IMAGE_PROXY_CONFIG.get_client()
            url = client.get_image_url(temp_path)
            return JsonResponse({'url': url})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            os.unlink(temp_path)
```

### 批量处理脚本

```python
#!/usr/bin/env python3
import os
import glob
from image_proxy_client import ImageProxyClient

def batch_upload(image_dir, server_url, username, password):
    """批量上传图片"""
    with ImageProxyClient(server_url, username, password) as client:
        # 查找所有图片文件
        patterns = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']
        image_files = []
        for pattern in patterns:
            image_files.extend(glob.glob(os.path.join(image_dir, pattern)))
        
        print(f"找到 {len(image_files)} 个图片文件")
        
        # 批量上传
        results = []
        for image_file in image_files:
            try:
                result = client.upload_image(image_file)
                results.append({
                    'file': image_file,
                    'url': result['url'],
                    'md5': result['md5'],
                    'status': 'success'
                })
                print(f"✅ {image_file} -> {result['url']}")
            except Exception as e:
                results.append({
                    'file': image_file,
                    'error': str(e),
                    'status': 'failed'
                })
                print(f"❌ {image_file} 上传失败: {e}")
        
        return results

if __name__ == "__main__":
    results = batch_upload(
        image_dir="./images",
        server_url="http://localhost:8000", 
        username="admin",
        password="password123"
    )
    
    # 输出统计
    success_count = len([r for r in results if r['status'] == 'success'])
    print(f"\n上传完成: 成功 {success_count}, 失败 {len(results) - success_count}")
```

## 🔗 相关链接

- [完整项目文档](https://github.com/DpengYu/Image-Proxy-Project)
- [服务器部署指南](https://github.com/DpengYu/Image-Proxy-Project/blob/main/docs/DEPLOYMENT.md)
- [API文档](https://github.com/DpengYu/Image-Proxy-Project/blob/main/docs/API.md)

## 📝 许可证

MIT License - 详见项目根目录的LICENSE文件

---

💡 **提示**: 这个客户端包是从完整的Image Proxy Project中提取的轻量级版本，专为第三方集成设计。