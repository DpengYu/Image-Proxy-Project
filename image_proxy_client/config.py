"""
Image Proxy Client - 配置管理模块
提供配置文件加载和环境变量支持
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ImageProxyConfig:
    """配置管理器，支持文件和环境变量配置"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为 "image_proxy_config.json"
        """
        self.config_file = config_file or "image_proxy_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置，优先级：环境变量 > 配置文件 > 默认值"""
        # 先尝试从配置文件加载
        config = self._load_from_file()
        
        # 环境变量覆盖配置文件
        config.update(self._load_from_env())
        
        return config
    
    def _load_from_file(self) -> Dict[str, Any]:
        """从配置文件加载"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"已加载配置文件: {config_path}")
                return config
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")
        
        # 返回默认配置
        return self._get_default_config()
    
    def _load_from_env(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        env_config = {}
        
        # 环境变量映射
        env_mapping = {
            'IMAGE_PROXY_URL': 'server_url',
            'IMAGE_PROXY_USERNAME': 'username', 
            'IMAGE_PROXY_PASSWORD': 'password',
            'IMAGE_PROXY_TIMEOUT': 'timeout',
            'IMAGE_PROXY_VERIFY_SSL': 'verify_ssl'
        }
        
        for env_key, config_key in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value:
                # 类型转换
                if config_key == 'timeout':
                    try:
                        env_config[config_key] = int(env_value)
                    except ValueError:
                        logger.warning(f"环境变量 {env_key} 值无效，忽略")
                elif config_key == 'verify_ssl':
                    env_config[config_key] = env_value.lower() in ('true', '1', 'yes', 'on')
                else:
                    env_config[config_key] = env_value
        
        if env_config:
            logger.info(f"已从环境变量加载配置: {list(env_config.keys())}")
        
        return env_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "server_url": "http://localhost:8000",
            "username": "admin",
            "password": "password123",
            "timeout": 30,
            "verify_ssl": True
        }
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置，为None时保存当前配置
        """
        config_to_save = config or self.config
        
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到: {config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def get_client(self):
        """
        根据配置创建客户端实例
        
        Returns:
            ImageProxyClient实例
        """
        from .client import ImageProxyClient
        
        required_keys = ['server_url', 'username', 'password']
        missing_keys = [key for key in required_keys if not self.config.get(key)]
        
        if missing_keys:
            raise ValueError(f"配置缺少必要参数: {missing_keys}")
        
        return ImageProxyClient(
            server_url=self.config['server_url'],
            username=self.config['username'],
            password=self.config['password'],
            timeout=self.config.get('timeout', 30),
            verify_ssl=self.config.get('verify_ssl', True)
        )
    
    def update_config(self, **kwargs):
        """
        更新配置
        
        Args:
            **kwargs: 要更新的配置项
        """
        self.config.update(kwargs)
    
    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)
    
    def __getitem__(self, key: str):
        """支持字典式访问"""
        return self.config[key]
    
    def __setitem__(self, key: str, value):
        """支持字典式设置"""
        self.config[key] = value


def load_config_from_env() -> Dict[str, Any]:
    """
    直接从环境变量加载配置的便捷函数
    
    Returns:
        配置字典
        
    Example:
        >>> import os
        >>> os.environ['IMAGE_PROXY_URL'] = 'http://server.com'
        >>> os.environ['IMAGE_PROXY_USERNAME'] = 'user'
        >>> os.environ['IMAGE_PROXY_PASSWORD'] = 'pass'
        >>> config = load_config_from_env()
    """
    config_manager = ImageProxyConfig()
    return config_manager.config


def create_config_template(file_path: str = "image_proxy_config.json"):
    """
    创建配置文件模板
    
    Args:
        file_path: 配置文件路径
    """
    template_config = {
        "server_url": "http://your-server.com:8000",
        "username": "your_username", 
        "password": "your_password",
        "timeout": 30,
        "verify_ssl": True,
        "_comment": {
            "server_url": "图片代理服务器地址",
            "username": "用户名",
            "password": "密码",
            "timeout": "请求超时时间（秒）",
            "verify_ssl": "是否验证SSL证书"
        }
    }
    
    try:
        config_path = Path(file_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(template_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 配置模板已创建: {config_path}")
        print("请编辑配置文件，填入正确的服务器信息")
        
    except Exception as e:
        print(f"❌ 创建配置模板失败: {e}")
        raise