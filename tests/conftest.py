"""
测试配置文件
"""
import pytest
import os
import tempfile
import json
from pathlib import Path

# 测试配置
TEST_CONFIG = {
    "server": {
        "domain": "http://localhost",
        "port": 8000
    },
    "cleanup": {
        "enable": False,  # 测试时禁用清理
        "expire_days": 1,
        "cleanup_time": "03:00:00"
    },
    "security": {
        "secret_key": "test_secret_key_for_testing_only_32_chars",
        "upload": {
            "max_file_size_mb": 5,
            "allowed_types": ["image/jpeg", "image/png", "image/gif", "image/webp"]
        },
        "rate_limit": {
            "max_requests": 1000,  # 测试时放宽限制
            "window_seconds": 60
        }
    },
    "logging": {
        "level": "DEBUG",
        "file": None,
        "max_size_mb": 10,
        "backup_count": 1
    },
    "users": [
        {
            "username": "testuser",
            "password": "testpass123"
        }
    ]
}

@pytest.fixture
def temp_config_file():
    """创建临时配置文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(TEST_CONFIG, f, indent=2)
        config_file = f.name
    
    yield config_file
    
    # 清理
    if os.path.exists(config_file):
        os.unlink(config_file)

@pytest.fixture
def temp_upload_dir():
    """创建临时上传目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        upload_dir = Path(temp_dir) / "uploads"
        upload_dir.mkdir()
        yield str(upload_dir)

@pytest.fixture
def test_image_file():
    """创建测试图片文件"""
    from PIL import Image
    import io
    
    # 创建一个简单的测试图片
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
        f.write(img_bytes.getvalue())
        image_file = f.name
    
    yield image_file
    
    # 清理
    if os.path.exists(image_file):
        os.unlink(image_file)

@pytest.fixture
def temp_db_file():
    """创建临时数据库文件"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_file = f.name
    
    yield db_file
    
    # 清理
    if os.path.exists(db_file):
        os.unlink(db_file)