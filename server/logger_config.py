"""
日志配置模块
提供统一的日志配置和管理
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


class LoggerManager:
    """日志管理器"""
    
    def __init__(self, 
                 name: str = "image_proxy",
                 level: str = "INFO",
                 log_file: Optional[str] = None,
                 max_size_mb: int = 100,
                 backup_count: int = 5):
        self.name = name
        self.level = getattr(logging, level.upper())
        self.log_file = log_file
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.backup_count = backup_count
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志器"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        if self.log_file:
            try:
                # 确保日志目录存在
                log_path = Path(self.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.handlers.RotatingFileHandler(
                    self.log_file,
                    maxBytes=self.max_size_bytes,
                    backupCount=self.backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(self.level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"无法创建文件日志处理器: {e}")
        
        return logger
    
    def get_logger(self) -> logging.Logger:
        """获取日志器"""
        return self.logger


# 全局日志器实例
_logger_instance: Optional[LoggerManager] = None


def setup_logger(config: dict) -> logging.Logger:
    """设置全局日志器"""
    global _logger_instance
    
    log_config = config.get("logging", {})
    _logger_instance = LoggerManager(
        level=log_config.get("level", "INFO"),
        log_file=log_config.get("file"),
        max_size_mb=log_config.get("max_size_mb", 100),
        backup_count=log_config.get("backup_count", 5)
    )
    
    return _logger_instance.get_logger()


def get_logger() -> logging.Logger:
    """获取全局日志器"""
    if _logger_instance is None:
        # 创建默认日志器
        default_manager = LoggerManager()
        return default_manager.get_logger()
    return _logger_instance.get_logger()


if __name__ == "__main__":
    # 测试日志功能
    logger = LoggerManager(log_file="test.log").get_logger()
    logger.info("测试信息日志")
    logger.warning("测试警告日志")
    logger.error("测试错误日志")