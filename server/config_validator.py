"""
配置验证模块
验证配置文件的完整性和安全性
"""
import json
import re
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            raise ConfigValidationError(f"配置文件不存在: {self.config_path}")
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ConfigValidationError(f"读取配置文件失败: {e}")
    
    def validate(self) -> None:
        """验证配置文件"""
        self._validate_server_config()
        self._validate_cleanup_config()
        self._validate_users_config()
        self._validate_security_config()
    
    def _validate_server_config(self) -> None:
        """验证服务器配置"""
        server = self.config.get("server", {})
        
        # 验证domain
        domain = server.get("domain", "")
        if not domain:
            raise ConfigValidationError("server.domain 不能为空")
        
        # 验证domain格式
        if not re.match(r'^https?://[a-zA-Z0-9\-\._]+', domain):
            raise ConfigValidationError("server.domain 格式不正确，应包含协议（http://或https://）")
        
        # 验证port
        port = server.get("port")
        if not isinstance(port, int) or not (1 <= port <= 65535):
            raise ConfigValidationError("server.port 必须是1-65535之间的整数")
    
    def _validate_cleanup_config(self) -> None:
        """验证清理配置"""
        cleanup = self.config.get("cleanup", {})
        
        # 验证enable
        enable = cleanup.get("enable")
        if not isinstance(enable, bool):
            raise ConfigValidationError("cleanup.enable 必须是布尔值")
        
        # 验证expire_days
        expire_days = cleanup.get("expire_days")
        if not isinstance(expire_days, int) or expire_days < 1:
            raise ConfigValidationError("cleanup.expire_days 必须是大于0的整数")
        
        # 验证cleanup_time
        cleanup_time = cleanup.get("cleanup_time", "")
        if not re.match(r'^\d{2}:\d{2}:\d{2}$', cleanup_time):
            raise ConfigValidationError("cleanup.cleanup_time 格式不正确，应为HH:MM:SS")
    
    def _validate_users_config(self) -> None:
        """验证用户配置"""
        users = self.config.get("users", [])
        if not isinstance(users, list):
            raise ConfigValidationError("users 必须是数组")
        
        if not users:
            raise ConfigValidationError("至少需要配置一个用户")
        
        usernames = set()
        for i, user in enumerate(users):
            if not isinstance(user, dict):
                raise ConfigValidationError(f"users[{i}] 必须是对象")
            
            username = user.get("username", "")
            password = user.get("password", "")
            
            if not username or not isinstance(username, str):
                raise ConfigValidationError(f"users[{i}].username 不能为空")
            
            if not password or not isinstance(password, str):
                raise ConfigValidationError(f"users[{i}].password 不能为空")
            
            # 检查用户名唯一性
            if username in usernames:
                raise ConfigValidationError(f"用户名重复: {username}")
            usernames.add(username)
            
            # 验证密码强度
            if len(password) < 6:
                raise ConfigValidationError(f"用户 {username} 的密码长度至少6位")
    
    def _validate_security_config(self) -> None:
        """验证安全配置"""
        security = self.config.get("security", {})
        
        # 检查是否配置了secret_key
        secret_key = security.get("secret_key")
        if not secret_key:
            raise ConfigValidationError("security.secret_key 不能为空，请配置强密钥")
        
        if len(secret_key) < 32:
            raise ConfigValidationError("security.secret_key 长度至少32位")
        
        # 验证上传限制
        upload = security.get("upload", {})
        max_file_size = upload.get("max_file_size_mb", 10)
        if not isinstance(max_file_size, (int, float)) or max_file_size <= 0:
            raise ConfigValidationError("security.upload.max_file_size_mb 必须是大于0的数字")
        
        allowed_types = upload.get("allowed_types", [])
        if not isinstance(allowed_types, list):
            raise ConfigValidationError("security.upload.allowed_types 必须是数组")
    
    def get_validated_config(self) -> Dict[str, Any]:
        """获取验证后的配置"""
        self.validate()
        return self.config


def validate_config_file(config_path: str) -> Dict[str, Any]:
    """验证配置文件并返回配置"""
    validator = ConfigValidator(config_path)
    return validator.get_validated_config()


if __name__ == "__main__":
    # 测试配置验证
    config_file = os.path.join(os.path.dirname(__file__), "../config/config.json")
    try:
        config = validate_config_file(config_file)
        print("✅ 配置验证通过")
    except ConfigValidationError as e:
        print(f"❌ 配置验证失败: {e}")