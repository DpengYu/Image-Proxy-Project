"""
安全工具模块
提供加密、验证、安全检查等功能
"""
import hashlib
import hmac
import base64
import secrets
import time
import re
from typing import Optional, Tuple, Dict, Any
from pathlib import Path


class SecurityManager:
    """安全管理器"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode("utf-8")
    
    def generate_token(self, username: str, password: str, md5: str, expire: int) -> str:
        """生成安全token"""
        msg = f"{username}:{password}:{md5}:{expire}".encode("utf-8")
        digest = hmac.new(self.secret_key, msg, hashlib.sha256).digest()
        token = base64.urlsafe_b64encode(digest + b":" + msg).decode("utf-8")
        return token
    
    def verify_token(self, token: str) -> Optional[Tuple[str, str, str]]:
        """验证token"""
        try:
            decoded = base64.urlsafe_b64decode(token.encode("utf-8"))
            digest, msg = decoded.split(b":", 1)
            expected_digest = hmac.new(self.secret_key, msg, hashlib.sha256).digest()
            
            if not hmac.compare_digest(digest, expected_digest):
                return None
                
            username, password, md5, expire_str = msg.decode("utf-8").split(":")
            if int(expire_str) < int(time.time()):
                return None
                
            return username, password, md5
        except Exception:
            return None
    
    @staticmethod
    def generate_secret_key() -> str:
        """生成安全的密钥"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_file_md5(file_path: Path) -> str:
        """计算文件MD5"""
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    @staticmethod
    def get_data_md5(data: bytes) -> str:
        """计算数据MD5"""
        return hashlib.md5(data).hexdigest()


class FileValidator:
    """文件验证器"""
    
    def __init__(self, max_size_mb: float = 10, allowed_types: Optional[list] = None):
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.allowed_types = allowed_types or ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    def validate_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """验证文件"""
        result = {"valid": True, "errors": []}
        
        # 检查文件大小
        if len(file_data) > self.max_size_bytes:
            result["valid"] = False
            result["errors"].append(f"文件大小超限，最大允许 {self.max_size_bytes / 1024 / 1024:.1f}MB")
        
        # 检查文件名
        if not self._is_safe_filename(filename):
            result["valid"] = False
            result["errors"].append("文件名包含非法字符")
        
        # 检查文件类型
        file_type = self._detect_file_type(file_data)
        if file_type not in self.allowed_types:
            result["valid"] = False
            result["errors"].append(f"不支持的文件类型，支持: {', '.join(self.allowed_types)}")
        
        return result
    
    def _is_safe_filename(self, filename: str) -> bool:
        """检查文件名是否安全"""
        # 检查路径遍历攻击
        if ".." in filename or "/" in filename or "\\" in filename:
            return False
        
        # 检查特殊字符
        safe_pattern = re.compile(r'^[a-zA-Z0-9_\-\.\s]+$')
        return bool(safe_pattern.match(filename))
    
    def _detect_file_type(self, file_data: bytes) -> str:
        """检测文件类型"""
        # 通过文件头检测
        if file_data.startswith(b'\xff\xd8\xff'):
            return "image/jpeg"
        elif file_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return "image/png"
        elif file_data.startswith(b'GIF87a') or file_data.startswith(b'GIF89a'):
            return "image/gif"
        elif file_data.startswith(b'RIFF') and b'WEBP' in file_data[:12]:
            return "image/webp"
        else:
            return "unknown"


class RateLimiter:
    """简单的内存速率限制器"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {client_id: [timestamp, ...]}
    
    def is_allowed(self, client_id: str) -> bool:
        """检查是否允许请求"""
        now = time.time()
        
        # 清理过期记录
        if client_id in self.requests:
            self.requests[client_id] = [
                t for t in self.requests[client_id] 
                if now - t < self.window_seconds
            ]
        else:
            self.requests[client_id] = []
        
        # 检查请求数量
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # 记录请求
        self.requests[client_id].append(now)
        return True
    
    def cleanup(self) -> None:
        """清理过期记录"""
        now = time.time()
        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                t for t in self.requests[client_id] 
                if now - t < self.window_seconds
            ]
            if not self.requests[client_id]:
                del self.requests[client_id]


if __name__ == "__main__":
    # 测试安全工具
    print("生成随机密钥:", SecurityManager.generate_secret_key())
    
    # 测试文件验证
    validator = FileValidator()
    test_result = validator.validate_file(b"test data", "test.txt")
    print("文件验证结果:", test_result)