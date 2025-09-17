"""
测试安全工具模块
"""
import unittest
import tempfile
import os
from pathlib import Path
import sys

# 添加服务器模块到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

try:
    from security_utils import SecurityManager, FileValidator, RateLimiter
except ImportError:
    SecurityManager = None
    FileValidator = None
    RateLimiter = None


class TestSecurityManager(unittest.TestCase):
    """安全管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        if SecurityManager is None:
            self.skipTest("SecurityManager 模块不可用")
        self.security_manager = SecurityManager("test_secret_key_32_characters_long")
    
    def test_generate_and_verify_token(self):
        """测试token生成和验证"""
        import time
        
        username = "testuser"
        password = "testpass"
        md5 = "test_md5_hash"
        expire = int(time.time()) + 3600  # 1小时后过期
        
        # 生成token
        token = self.security_manager.generate_token(username, password, md5, expire)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)
        
        # 验证token
        result = self.security_manager.verify_token(token)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], username)
        self.assertEqual(result[1], password)
        self.assertEqual(result[2], md5)
    
    def test_invalid_token(self):
        """测试无效token"""
        # 测试完全无效的token
        result = self.security_manager.verify_token("invalid_token")
        self.assertIsNone(result)
        
        # 测试空token
        result = self.security_manager.verify_token("")
        self.assertIsNone(result)
    
    def test_expired_token(self):
        """测试过期token"""
        import time
        
        username = "testuser"
        password = "testpass"
        md5 = "test_md5_hash"
        expire = int(time.time()) - 3600  # 1小时前过期
        
        # 生成过期token
        token = self.security_manager.generate_token(username, password, md5, expire)
        
        # 验证过期token
        result = self.security_manager.verify_token(token)
        self.assertIsNone(result)
    
    def test_data_md5(self):
        """测试数据MD5计算"""
        test_data = b"Hello, World!"
        md5 = self.security_manager.get_data_md5(test_data)
        
        # 验证MD5格式
        self.assertEqual(len(md5), 32)
        self.assertTrue(all(c in "0123456789abcdef" for c in md5))
        
        # 验证相同数据产生相同MD5
        md5_2 = self.security_manager.get_data_md5(test_data)
        self.assertEqual(md5, md5_2)
        
        # 验证不同数据产生不同MD5
        md5_3 = self.security_manager.get_data_md5(b"Different data")
        self.assertNotEqual(md5, md5_3)


class TestFileValidator(unittest.TestCase):
    """文件验证器测试"""
    
    def setUp(self):
        """测试前准备"""
        if FileValidator is None:
            self.skipTest("FileValidator 模块不可用")
        self.validator = FileValidator(max_size_mb=1, allowed_types=["image/png", "image/jpeg"])
    
    def test_file_size_validation(self):
        """测试文件大小验证"""
        # 测试正常大小文件
        small_data = b"x" * 1024  # 1KB
        result = self.validator.validate_file(small_data, "test.png")
        self.assertTrue(result["valid"])
        
        # 测试超大文件
        large_data = b"x" * (2 * 1024 * 1024)  # 2MB
        result = self.validator.validate_file(large_data, "test.png")
        self.assertFalse(result["valid"])
        self.assertTrue(any("大小超限" in error for error in result["errors"]))
    
    def test_filename_validation(self):
        """测试文件名验证"""
        test_data = b"test"
        
        # 测试安全文件名
        result = self.validator.validate_file(test_data, "normal_file.png")
        self.assertTrue(result["valid"] or any("文件类型" in error for error in result["errors"]))
        
        # 测试危险文件名
        dangerous_names = ["../../../etc/passwd", "test/../file.png", "test\\file.png"]
        for name in dangerous_names:
            result = self.validator.validate_file(test_data, name)
            self.assertFalse(result["valid"])
            self.assertTrue(any("文件名包含非法字符" in error for error in result["errors"]))
    
    def test_file_type_detection(self):
        """测试文件类型检测"""
        # PNG文件头
        png_data = b'\x89PNG\r\n\x1a\n' + b'x' * 100
        result = self.validator.validate_file(png_data, "test.png")
        self.assertTrue(result["valid"])
        
        # JPEG文件头
        jpeg_data = b'\xff\xd8\xff' + b'x' * 100
        result = self.validator.validate_file(jpeg_data, "test.jpg")
        self.assertTrue(result["valid"])
        
        # 不支持的文件类型
        unknown_data = b'unknown file content'
        result = self.validator.validate_file(unknown_data, "test.txt")
        self.assertFalse(result["valid"])
        self.assertTrue(any("不支持的文件类型" in error for error in result["errors"]))


class TestRateLimiter(unittest.TestCase):
    """速率限制器测试"""
    
    def setUp(self):
        """测试前准备"""
        if RateLimiter is None:
            self.skipTest("RateLimiter 模块不可用")
        self.rate_limiter = RateLimiter(max_requests=3, window_seconds=60)
    
    def test_normal_requests(self):
        """测试正常请求"""
        client_id = "test_client"
        
        # 前3个请求应该被允许
        for i in range(3):
            allowed = self.rate_limiter.is_allowed(client_id)
            self.assertTrue(allowed, f"第{i+1}个请求应该被允许")
        
        # 第4个请求应该被拒绝
        allowed = self.rate_limiter.is_allowed(client_id)
        self.assertFalse(allowed, "第4个请求应该被拒绝")
    
    def test_multiple_clients(self):
        """测试多客户端"""
        # 不同客户端应该有独立的限制
        for i in range(3):
            client_id = f"client_{i}"
            for j in range(3):
                allowed = self.rate_limiter.is_allowed(client_id)
                self.assertTrue(allowed, f"客户端{i}的第{j+1}个请求应该被允许")
    
    def test_cleanup(self):
        """测试清理功能"""
        client_id = "test_client"
        
        # 发送一些请求
        for _ in range(3):
            self.rate_limiter.is_allowed(client_id)
        
        # 验证记录存在
        self.assertIn(client_id, self.rate_limiter.requests)
        
        # 执行清理
        self.rate_limiter.cleanup()
        
        # 由于时间窗口内，记录应该还在
        self.assertIn(client_id, self.rate_limiter.requests)


if __name__ == "__main__":
    unittest.main()