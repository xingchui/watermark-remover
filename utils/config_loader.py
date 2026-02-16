"""
配置加载模块
负责读取和解析 YAML 配置文件
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from .exceptions import ConfigError


class ConfigLoader:
    """配置加载器"""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls, config_path: Optional[str] = None):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，默认查找当前目录的 config.yaml
        """
        if not self._config:
            self.load(config_path)
    
    def load(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            ConfigError: 配置文件不存在或格式错误
        """
        if config_path is None:
            # 默认查找 config.yaml
            config_path = self._find_config_file()
        
        config_file = Path(config_path)
        if not config_file.exists():
            raise ConfigError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ConfigError(f"读取配置文件失败: {e}")
        
        # 处理相对路径
        self._resolve_paths(config_file.parent)
        
        return self._config
    
    def _find_config_file(self) -> str:
        """查找配置文件"""
        # 当前工作目录
        cwd = Path.cwd()
        config_file = cwd / 'config.yaml'
        if config_file.exists():
            return str(config_file)
        
        # 脚本所在目录
        script_dir = Path(__file__).parent.parent
        config_file = script_dir / 'config.yaml'
        if config_file.exists():
            return str(config_file)
        
        raise ConfigError("未找到 config.yaml 配置文件")
    
    def _resolve_paths(self, base_dir: Path):
        """将相对路径转换为绝对路径"""
        path_keys = [
            ('paths', 'temp_dir'),
            ('paths', 'log_dir'),
            ('paths', 'output_dir'),
        ]
        
        for section, key in path_keys:
            if section in self._config and key in self._config[section]:
                path = Path(self._config[section][key])
                if not path.is_absolute():
                    self._config[section][key] = str(base_dir / path)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项，支持点号分隔的路径
        
        Args:
            key: 配置键，如 "processing.image.quality"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config.copy()
    
    def reload(self) -> Dict[str, Any]:
        """重新加载配置"""
        self._config = {}
        return self.load()


def get_config(key: Optional[str] = None, default: Any = None) -> Any:
    """
    便捷函数：获取配置
    
    Args:
        key: 配置键
        default: 默认值
        
    Returns:
        配置值或配置字典
    """
    loader = ConfigLoader()
    if key is None:
        return loader.config
    return loader.get(key, default)
