# Image Proxy Client

统一的图片代理客户端，专为简化集成设计。支持配置文件和直接参数两种方式。

## 🚀 快速开始

### 基本使用

```python
from client import ImageProxyClient, quick_upload

# 方式1：使用配置文件
with ImageProxyClient() as client:
    url = client.get_image_url("image.jpg")
    print(f"图片URL: {url}")

# 方式2：直接传参
with ImageProxyClient("http://server.com", "user", "pass") as client:
    result = client.upload_image("image.jpg")
    print(f"图片信息: {result}")

# 方式3：快速上传
url = quick_upload("http://server.com", "user", "pass", "image.jpg")
print(f"图片URL: {url}")
```

### 配置文件

默认读取 `../config/config.json`：

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

## 📖 API参考

### ImageProxyClient类

#### 初始化
```python
ImageProxyClient(
    server_url=None,     # 服务器地址
    username=None,       # 用户名
    password=None,       # 密码
    config_file=None,    # 配置文件路径
    timeout=30,          # 超时时间（秒）
    verify_ssl=True      # 是否验证SSL
)
```

#### 主要方法

- **upload_image(image_path)**: 上传图片，返回详细信息
- **get_image_url(image_path)**: 上传图片，直接返回URL
- **upload_or_get(file_path)**: 上传或获取已存在的图片信息
- **get_image_info(md5)**: 根据MD5获取图片信息
- **is_healthy()**: 检查服务健康状态

### 便捷函数

```python
# 快速上传
quick_upload(server_url, username, password, image_path, timeout=30)

# 计算MD5
calculate_md5(file_path)

# 使用配置文件的兼容接口
upload_or_get(file_path, config_file=None)
get_image_url(file_path, config_file=None)
```

## 🔧 集成示例

### Flask应用
```python
from flask import Flask, request, jsonify
from client import quick_upload

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    temp_path = f"/tmp/{file.filename}"
    file.save(temp_path)
    
    try:
        url = quick_upload(
            "http://image-server.com:8000",
            "api_user", "api_pass", temp_path
        )
        return jsonify({'url': url})
    finally:
        os.unlink(temp_path)
```

### 命令行工具
```python
#!/usr/bin/env python3
import sys
from client import quick_upload

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python upload.py <image_path>")
        sys.exit(1)
    
    url = quick_upload(
        "http://localhost:8000",
        "admin", "password", 
        sys.argv[1]
    )
    print(f"上传成功: {url}")
```

## 特性

- ✅ 统一客户端设计，支持多种使用方式
- ✅ 移除SQLite缓存，简化架构
- ✅ 支持上下文管理器，自动资源清理
- ✅ 完善的错误处理和日志记录
- ✅ 支持SSL验证控制
- ✅ 兼容旧版本接口

## 依赖要求

- Python >= 3.7
- requests >= 2.25.0
- 配置文件：../config/config.json