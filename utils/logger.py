"""
日志工具模块
提供统一的日志记录功能
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from .config_loader import get_config


class Logger:
    """日志管理器"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """设置日志"""
        self._logger = logging.getLogger('watermark_remover')
        self._logger.setLevel(logging.DEBUG)
        
        # 清除现有处理器
        self._logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器 - 添加编码处理
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        # 设置编码避免中文乱码
        try:
            console_handler.stream.reconfigure(encoding='utf-8')
        except:
            pass
        self._logger.addHandler(console_handler)
        
        # 文件处理器
        log_dir = get_config('paths.log_dir', './logs')
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        log_file = Path(log_dir) / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
    
    @property
    def logger(self) -> logging.Logger:
        """获取日志记录器"""
        return self._logger
    
    def debug(self, msg: str):
        """调试日志"""
        self._logger.debug(msg)
    
    def info(self, msg: str):
        """信息日志"""
        self._logger.info(msg)
    
    def warning(self, msg: str):
        """警告日志"""
        self._logger.warning(msg)
    
    def error(self, msg: str):
        """错误日志"""
        self._logger.error(msg)
    
    def critical(self, msg: str):
        """严重错误日志"""
        self._logger.critical(msg)


# 全局日志实例
_logger_instance: Optional[Logger] = None


def get_logger() -> Logger:
    """获取日志实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    assert _logger_instance is not None
    return _logger_instance


# 便捷函数
def debug(msg: str):
    """调试日志"""
    get_logger().debug(msg)


def info(msg: str):
    """信息日志"""
    get_logger().info(msg)


def warning(msg: str):
    """警告日志"""
    get_logger().warning(msg)


def error(msg: str):
    """错误日志"""
    get_logger().error(msg)


def critical(msg: str):
    """严重错误日志"""
    get_logger().critical(msg)
