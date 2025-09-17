"""
环境变量配置加载器
支持从环境变量、.env文件和JSON配置文件加载配置
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("提示: 安装 python-dotenv 以支持 .env 文件")

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器，支持多种配置源"""
    
    def __init__(self, config_file: Optional[str] = None, env_file: Optional[str] = None):
        self.config_file = config_file
        self.env_file = env_file
        
        # 加载环境变量
        if DOTENV_AVAILABLE and env_file:
            load_dotenv(env_file)
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置，优先级：环境变量 > .env文件 > JSON配置文件 > 默认值"""
        
        # 1. 先从JSON文件加载基础配置
        config = self._load_json_config()
        
        # 2. 用环境变量覆盖配置
        config = self._override_with_env(config)
        
        # 3. 验证必要配置
        self._validate_config(config)
        
        return config
    
    def _load_json_config(self) -> Dict[str, Any]:
        """从JSON文件加载配置"""
        if not self.config_file or not Path(self.config_file).exists():
            logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
            return self._get_default_config()
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"从配置文件加载: {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _override_with_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """用环境变量覆盖配置"""
        
        # 服务器配置
        if os.getenv("SERVER_DOMAIN"):
            config.setdefault("server", {})["domain"] = os.getenv("SERVER_DOMAIN")
        if os.getenv("SERVER_PORT"):
            config.setdefault("server", {})["port"] = int(os.getenv("SERVER_PORT"))
        
        # 安全配置
        if os.getenv("SECRET_KEY"):
            config.setdefault("security", {})["secret_key"] = os.getenv("SECRET_KEY")
        if os.getenv("MAX_FILE_SIZE_MB"):
            config.setdefault("security", {}).setdefault("upload", {})["max_file_size_mb"] = float(os.getenv("MAX_FILE_SIZE_MB"))
        
        # 清理配置
        if os.getenv("CLEANUP_ENABLE"):
            config.setdefault("cleanup", {})["enable"] = os.getenv("CLEANUP_ENABLE").lower() == "true"
        if os.getenv("CLEANUP_EXPIRE_DAYS"):
            config.setdefault("cleanup", {})["expire_days"] = int(os.getenv("CLEANUP_EXPIRE_DAYS"))
        if os.getenv("CLEANUP_TIME"):
            config.setdefault("cleanup", {})["cleanup_time"] = os.getenv("CLEANUP_TIME")
        
        # 日志配置
        if os.getenv("LOG_LEVEL"):
            config.setdefault("logging", {})["level"] = os.getenv("LOG_LEVEL")
        if os.getenv("LOG_FILE"):
            config.setdefault("logging", {})["file"] = os.getenv("LOG_FILE")
        
        # 数据库配置
        if os.getenv("DB_FILE"):
            config["db_file"] = os.getenv("DB_FILE")
        
        # 用户配置（支持单个用户从环境变量）
        username = os.getenv("DEFAULT_USERNAME")
        password = os.getenv("DEFAULT_PASSWORD")
        if username and password:
            config.setdefault("users", [])
            # 如果没有用户或第一个用户为空，则使用环境变量
            if not config["users"] or not config["users"][0].get("username"):
                config["users"] = [{"username": username, "password": password}]
        
        logger.info("应用环境变量配置覆盖")
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "server": {
                "domain": "http://localhost",
                "port": 8000
            },
            "cleanup": {
                "enable": True,
                "expire_days": 30,
                "cleanup_time": "03:00:00"
            },
            "security": {
                "secret_key": "CHANGE_THIS_TO_A_RANDOM_32_CHAR_STRING",
                "upload": {
                    "max_file_size_mb": 10,
                    "allowed_types": ["image/jpeg", "image/png", "image/gif", "image/webp"]
                },
                "rate_limit": {
                    "max_requests": 100,
                    "window_seconds": 60
                }
            },
            "logging": {
                "level": "INFO",
                "file": None,
                "max_size_mb": 100,
                "backup_count": 5
            },
            "users": [
                {
                    "username": "admin",
                    "password": "CHANGE_THIS_PASSWORD"
                }
            ]
        }
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证配置"""
        errors = []
        
        # 验证服务器配置
        server = config.get("server", {})
        if not server.get("domain"):
            errors.append("server.domain 不能为空")
        
        port = server.get("port")
        if not isinstance(port, int) or not (1 <= port <= 65535):
            errors.append("server.port 必须是1-65535之间的整数")
        
        # 验证安全配置
        security = config.get("security", {})
        secret_key = security.get("secret_key")
        if not secret_key or secret_key in ["CHANGE_THIS_TO_A_RANDOM_32_CHAR_STRING", "your_32_character_secret_key_here_change_this"]:
            errors.append("必须设置有效的 security.secret_key")
        
        # 验证用户配置
        users = config.get("users", [])
        if not users:
            errors.append("至少需要配置一个用户")
        else:
            user = users[0]
            if not user.get("username") or not user.get("password"):
                errors.append("用户名和密码不能为空")
            
            if user.get("password") in ["CHANGE_THIS_PASSWORD", "change_this_password"]:
                errors.append("必须修改默认密码")
        
        if errors:
            error_msg = "配置验证失败:\\n" + "\\n".join(f"- {error}" for error in errors)
            raise ValueError(error_msg)


def load_config(config_file: Optional[str] = None, env_file: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置的便捷函数
    
    Args:
        config_file: JSON配置文件路径
        env_file: .env文件路径
        
    Returns:
        合并后的配置字典
    """
    loader = ConfigLoader(config_file, env_file)
    return loader.load_config()


if __name__ == "__main__":
    # 测试配置加载
    try:
        config = load_config()
        print("✅ 配置加载成功")
        print(f"服务器: {config['server']['domain']}:{config['server']['port']}")
        print(f"用户数: {len(config['users'])}")
        print(f"密钥长度: {len(config['security']['secret_key'])}")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")