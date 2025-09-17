# 第三方集成指南

Image Proxy Project 统一客户端集成指南，适用于各种第三方项目。

## 🚀 推荐集成方式

### 方式1: 直接复制文件（推荐）

最简单直接的集成方式：

```bash
# 下载客户端文件
wget https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/client/client.py

# 或使用curl
curl -O https://raw.githubusercontent.com/DpengYu/Image-Proxy-Project/main/client/client.py

# 复制到您的项目中
cp client.py your_project/utils/
```

使用示例：
```python
from utils.client import quick_upload

# 单行代码上传图片
url = quick_upload(
    "http://your-server.com:8000",
    "username", "password", 
    "image.jpg"
)
print(f"图片URL: {url}")
```

### 方式2: Git Submodule

适合需要跟随更新的项目：

```bash
# 添加为子模块
git submodule add https://github.com/DpengYu/Image-Proxy-Project.git image_proxy

# 设置sparse-checkout只获取客户端
cd image_proxy
git config core.sparseCheckout true
echo "client/*" > .git/info/sparse-checkout
git read-tree -m -u HEAD

# 在您的项目中使用
import sys
sys.path.append('image_proxy')
from client.client import quick_upload

url = quick_upload("http://server.com", "user", "pass", "image.jpg")
```

### 方式3: 项目内置

将客户端作为项目的一部分：

```bash
# 克隆完整项目
git clone https://github.com/DpengYu/Image-Proxy-Project.git temp_image_proxy

# 复制客户端到您的项目
cp -r temp_image_proxy/client your_project/libs/image_proxy_client

# 清理临时文件
rm -rf temp_image_proxy
```

项目结构：
```
your_project/
├── src/
├── libs/
│   └── image_proxy_client/
│       ├── client.py
│       └── README.md
└── requirements.txt
```

使用示例：
```python
from libs.image_proxy_client.client import ImageProxyClient, quick_upload

# 方式1: 配置文件
with ImageProxyClient() as client:
    url = client.get_image_url("image.jpg")

# 方式2: 直接传参
url = quick_upload("http://server.com", "user", "pass", "image.jpg")
```

## 📋 配置管理

### 配置文件方式

创建配置文件 `config/image_proxy.json`：

```json
{
  "server": {
    "domain": "http://your-server.com:8000"
  },
  "users": [
    {
      "username": "your_username",
      "password": "your_password"
    }
  ]
}
```

使用配置：
```python
from client import ImageProxyClient

# 指定配置文件
client = ImageProxyClient(config_file="config/image_proxy.json")
url = client.get_image_url("image.jpg")
client.close()
```

### 环境变量方式

```python
import os
from client import ImageProxyClient

# 设置环境变量
os.environ['IMAGE_PROXY_URL'] = 'http://your-server.com:8000'
os.environ['IMAGE_PROXY_USERNAME'] = 'username'
os.environ['IMAGE_PROXY_PASSWORD'] = 'password'

# 通过参数传递
client = ImageProxyClient(
    server_url=os.getenv('IMAGE_PROXY_URL'),
    username=os.getenv('IMAGE_PROXY_USERNAME'),
    password=os.getenv('IMAGE_PROXY_PASSWORD')
)
```

## 🎯 各种框架集成示例

### Flask集成

```python
from flask import Flask, request, jsonify, current_app
from client import quick_upload
import tempfile
import os

app = Flask(__name__)

# 配置
app.config['IMAGE_PROXY_URL'] = 'http://your-server.com:8000'
app.config['IMAGE_PROXY_USER'] = 'api_user'
app.config['IMAGE_PROXY_PASS'] = 'api_password'

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': '未找到图片文件'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        file.save(tmp.name)
        
        try:
            url = quick_upload(
                current_app.config['IMAGE_PROXY_URL'],
                current_app.config['IMAGE_PROXY_USER'],
                current_app.config['IMAGE_PROXY_PASS'],
                tmp.name
            )
            return jsonify({'url': url})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            os.unlink(tmp.name)
```

### Django集成

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from client import quick_upload
import tempfile
import os

@csrf_exempt
def upload_image(request):
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持POST请求'}, status=405)
    
    if 'image' not in request.FILES:
        return JsonResponse({'error': '未找到图片文件'}, status=400)
    
    image_file = request.FILES['image']
    
    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        for chunk in image_file.chunks():
            tmp.write(chunk)
        tmp.flush()
        
        try:
            url = quick_upload(
                "http://your-server.com:8000",
                "api_user", "api_password",
                tmp.name
            )
            return JsonResponse({'url': url})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            os.unlink(tmp.name)
```

### FastAPI集成

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from client import quick_upload
import tempfile
import os

app = FastAPI()

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # 检查文件类型
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="文件必须是图片类型")
    
    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp.flush()
        
        try:
            url = quick_upload(
                "http://your-server.com:8000",
                "api_user", "api_password",
                tmp.name
            )
            return {"url": url, "filename": file.filename}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            os.unlink(tmp.name)
```

## 🛠️ 高级使用

### 批量上传

```python
from client import ImageProxyClient
import os

def batch_upload(image_dir, server_url, username, password):
    results = []
    
    with ImageProxyClient(server_url, username, password) as client:
        for filename in os.listdir(image_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                file_path = os.path.join(image_dir, filename)
                try:
                    result = client.upload_image(file_path)
                    results.append({
                        'filename': filename,
                        'url': result['url'],
                        'status': 'success'
                    })
                except Exception as e:
                    results.append({
                        'filename': filename,
                        'error': str(e),
                        'status': 'failed'
                    })
    
    return results

# 使用
results = batch_upload(
    "/path/to/images",
    "http://your-server.com:8000",
    "username", "password"
)

for result in results:
    if result['status'] == 'success':
        print(f"✅ {result['filename']}: {result['url']}")
    else:
        print(f"❌ {result['filename']}: {result['error']}")
```

### 错误处理

```python
from client import ImageProxyClient
import requests

def safe_upload(image_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            with ImageProxyClient() as client:
                if not client.is_healthy():
                    raise Exception("服务器不可用")
                
                return client.get_image_url(image_path)
                
        except requests.RequestException as e:
            print(f"网络错误 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise
        except Exception as e:
            print(f"上传失败: {e}")
            raise

# 使用
try:
    url = safe_upload("image.jpg")
    print(f"上传成功: {url}")
except Exception as e:
    print(f"最终失败: {e}")
```

## 📝 注意事项

1. **依赖要求**: 确保安装了 `requests` 库
2. **配置安全**: 不要在代码中硬编码密码，使用环境变量或配置文件
3. **错误处理**: 始终进行适当的错误处理
4. **资源清理**: 使用上下文管理器或手动调用 `close()` 方法
5. **版本兼容**: 客户端向后兼容，支持旧版本接口

## 🔧 故障排除

### 常见问题

1. **导入错误**: 确保 `client.py` 文件在正确的路径
2. **网络错误**: 检查服务器地址和网络连接
3. **认证失败**: 验证用户名和密码是否正确
4. **文件不存在**: 确保图片文件路径正确
5. **权限问题**: 确保有读取图片文件的权限

### 调试技巧

```python
import logging
from client import ImageProxyClient

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 测试连接
with ImageProxyClient() as client:
    if client.is_healthy():
        print("✅ 服务器连接正常")
    else:
        print("❌ 服务器连接失败")
```