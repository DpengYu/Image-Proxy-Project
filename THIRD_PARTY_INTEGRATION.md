# 第三方项目集成指南

本指南详细说明如何通过Git命令精准获取Image Proxy Client，并集成到您的项目中。

## 🎯 设计理念

- ✅ **无明文信息泄露**: 配置通过环境变量或配置文件管理
- ✅ **精准获取**: 只获取需要的客户端代码，不下载整个项目
- ✅ **便捷集成**: 支持多种集成方式，适应不同项目需求
- ✅ **标准化**: 遵循Python包管理最佳实践

## 🚀 集成方式

### 方式1: Git Submodule + Sparse Checkout (推荐)

此方式最适合需要版本控制和更新管理的项目。

#### 步骤1: 添加子模块
```bash
# 在你的项目根目录执行
git submodule add https://github.com/DpengYu/Image-Proxy-Project.git third_party/image_proxy
```

#### 步骤2: 配置稀疏检出
```bash
cd third_party/image_proxy

# 启用稀疏检出
git config core.sparseCheckout true

# 只检出客户端包
echo "image_proxy_client/*" > .git/info/sparse-checkout

# 重新检出，只获取客户端代码
git read-tree -m -u HEAD
```

#### 步骤3: 在项目中使用
```python
# 在你的Python代码中
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'third_party/image_proxy'))

from image_proxy_client import quick_upload

# 使用环境变量配置（推荐）
url = quick_upload(
    server_url=os.getenv('IMAGE_PROXY_URL'),
    username=os.getenv('IMAGE_PROXY_USERNAME'), 
    password=os.getenv('IMAGE_PROXY_PASSWORD'),
    image_path="path/to/image.jpg"
)
```

#### 步骤4: 更新子模块
```bash
# 更新到最新版本
cd third_party/image_proxy
git pull origin main

# 或者在主项目中更新所有子模块
git submodule update --remote
```

### 方式2: 直接克隆子目录

适合不需要版本管理的一次性集成。

```bash
# 克隆整个仓库
git clone https://github.com/DpengYu/Image-Proxy-Project.git temp_image_proxy

# 只复制客户端包到你的项目
cp -r temp_image_proxy/image_proxy_client your_project/libs/

# 清理临时目录
rm -rf temp_image_proxy
```

使用方式：
```python
# 添加到Python路径
import sys
sys.path.append('libs')

from image_proxy_client import ImageProxyClient, quick_upload
```

### 方式3: Git Worktree (高级用法)

适合需要同时维护多个版本的场景。

```bash
# 克隆仓库（如果尚未克隆）
git clone https://github.com/DpengYu/Image-Proxy-Project.git image_proxy_source

cd image_proxy_source

# 创建工作树，只包含客户端
git worktree add ../my_project/image_proxy_client main
```

### 方式4: Pip安装 (开发中)

```bash
# 直接从Git仓库安装
pip install git+https://github.com/DpengYu/Image-Proxy-Project.git#subdirectory=image_proxy_client

# 使用
from image_proxy_client import quick_upload
```

## 🔧 配置管理

### 环境变量配置 (推荐)

在您的项目中设置环境变量：

```bash
# .env 文件或系统环境变量
export IMAGE_PROXY_URL="http://your-server.com:8000"
export IMAGE_PROXY_USERNAME="your_username"
export IMAGE_PROXY_PASSWORD="your_password"
export IMAGE_PROXY_TIMEOUT="30"
export IMAGE_PROXY_VERIFY_SSL="true"
```

Python代码：
```python
import os
from image_proxy_client import ImageProxyConfig

# 自动从环境变量加载配置
config = ImageProxyConfig()
client = config.get_client()

# 直接使用
url = client.get_image_url("image.jpg")
```

### 配置文件方式

```python
from image_proxy_client.config import create_config_template, ImageProxyConfig

# 创建配置模板
create_config_template("image_proxy_config.json")

# 编辑配置文件后使用
config = ImageProxyConfig("image_proxy_config.json")
client = config.get_client()
```

## 📦 项目结构建议

### 小型项目结构
```
your_project/
├── main.py
├── requirements.txt
├── .env                     # 环境变量配置
└── libs/
    └── image_proxy_client/  # 复制的客户端包
```

### 大型项目结构
```
your_project/
├── src/
│   └── main.py
├── third_party/             # 第三方依赖
│   └── image_proxy/         # Git submodule
│       └── image_proxy_client/
├── config/
│   └── image_proxy.json     # 配置文件
├── requirements.txt
└── .gitmodules              # Git子模块配置
```

## 🎯 最佳实践

### 1. 环境变量管理

```python
# utils/image_config.py
import os
from image_proxy_client import ImageProxyConfig

def get_image_client():
    """获取配置好的图片客户端"""
    config = ImageProxyConfig()
    
    # 验证必要的环境变量
    required_vars = ['IMAGE_PROXY_URL', 'IMAGE_PROXY_USERNAME', 'IMAGE_PROXY_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"缺少环境变量: {missing_vars}")
    
    return config.get_client()

# 在其他文件中使用
from utils.image_config import get_image_client

def upload_user_avatar(image_path):
    client = get_image_client()
    return client.get_image_url(image_path)
```

### 2. 错误处理

```python
from image_proxy_client import quick_upload
import logging

def safe_upload_image(image_path):
    """安全的图片上传，带完整错误处理"""
    try:
        url = quick_upload(
            server_url=os.getenv('IMAGE_PROXY_URL'),
            username=os.getenv('IMAGE_PROXY_USERNAME'),
            password=os.getenv('IMAGE_PROXY_PASSWORD'),
            image_path=image_path
        )
        logging.info(f"图片上传成功: {image_path} -> {url}")
        return url
    
    except FileNotFoundError:
        logging.error(f"文件不存在: {image_path}")
        return None
    except ValueError as e:
        logging.error(f"上传参数错误: {e}")
        return None
    except Exception as e:
        logging.error(f"上传失败: {e}")
        return None
```

### 3. 异步集成

```python
import asyncio
import concurrent.futures
from image_proxy_client import ImageProxyClient

class AsyncImageProxy:
    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self.client = None
    
    async def upload_image(self, image_path):
        """异步上传图片"""
        if not self.client:
            from utils.image_config import get_image_client
            self.client = get_image_client()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.client.get_image_url, 
            image_path
        )

# 使用示例
async def main():
    proxy = AsyncImageProxy()
    url = await proxy.upload_image("image.jpg")
    print(f"异步上传完成: {url}")
```

## 🔄 版本管理

### 锁定版本

```bash
# 在子模块中锁定特定版本
cd third_party/image_proxy
git checkout v1.0.0  # 或特定commit hash

# 提交锁定的版本
cd ../../
git add third_party/image_proxy
git commit -m "锁定image_proxy版本到v1.0.0"
```

### 自动更新检查

```python
# scripts/check_updates.py
import subprocess
import os

def check_image_proxy_updates():
    """检查image_proxy客户端是否有更新"""
    try:
        os.chdir('third_party/image_proxy')
        
        # 获取当前版本
        current = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        
        # 获取远程最新版本
        subprocess.run(['git', 'fetch', 'origin'], check=True)
        latest = subprocess.check_output(['git', 'rev-parse', 'origin/main']).decode().strip()
        
        if current != latest:
            print("🔄 发现image_proxy客户端更新")
            print(f"当前版本: {current[:8]}")
            print(f"最新版本: {latest[:8]}")
            print("运行 'git submodule update --remote' 更新")
        else:
            print("✅ image_proxy客户端已是最新版本")
            
    except Exception as e:
        print(f"❌ 检查更新失败: {e}")
    finally:
        os.chdir('../../')

if __name__ == "__main__":
    check_image_proxy_updates()
```

## 🧪 测试集成

```python
# tests/test_image_integration.py
import unittest
import os
from unittest.mock import patch, MagicMock

class TestImageProxyIntegration(unittest.TestCase):
    
    @patch.dict(os.environ, {
        'IMAGE_PROXY_URL': 'http://test-server.com',
        'IMAGE_PROXY_USERNAME': 'test_user',
        'IMAGE_PROXY_PASSWORD': 'test_pass'
    })
    def test_config_from_env(self):
        """测试从环境变量加载配置"""
        from image_proxy_client import ImageProxyConfig
        
        config = ImageProxyConfig()
        self.assertEqual(config.get('server_url'), 'http://test-server.com')
        self.assertEqual(config.get('username'), 'test_user')
    
    @patch('image_proxy_client.client.requests.Session')
    def test_upload_success(self, mock_session):
        """测试上传成功场景"""
        # Mock成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'url': 'http://test.com/image.jpg'}
        
        mock_session.return_value.post.return_value = mock_response
        
        from image_proxy_client import quick_upload
        
        # 创建测试图片文件
        with open('test_image.jpg', 'w') as f:
            f.write('test')
        
        try:
            url = quick_upload('http://test.com', 'user', 'pass', 'test_image.jpg')
            self.assertEqual(url, 'http://test.com/image.jpg')
        finally:
            os.unlink('test_image.jpg')

if __name__ == '__main__':
    unittest.main()
```

## 📚 常见问题

### Q: 如何处理子模块更新？
A: 使用 `git submodule update --remote` 更新到最新版本，或使用 `git checkout <version>` 切换到特定版本。

### Q: 能否只下载特定文件？
A: 可以使用sparse-checkout功能，如示例中所示，只检出 `image_proxy_client` 目录。

### Q: 如何避免路径冲突？
A: 建议将客户端代码放在专门的目录（如 `third_party/`、`libs/`），并通过sys.path管理导入路径。

### Q: 是否支持离线使用？
A: 是的，一旦获取了客户端代码，就可以离线使用，只需要在运行时连接到图片代理服务器。

---

💡 **提示**: 推荐使用Git Submodule + 环境变量的方式，这样既能保持代码的版本管理，又能避免敏感信息泄露。