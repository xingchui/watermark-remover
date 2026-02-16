"""
缓存管理模块
管理临时文件和内存缓存
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Union, Dict, Any
from utils import ensure_dir, delete_file, get_config, get_logger
from utils.exceptions import CacheError

logger = get_logger()


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, temp_dir: Optional[Union[str, Path]] = None):
        """
        初始化缓存管理器
        
        Args:
            temp_dir: 临时目录路径
        """
        self.temp_dir = Path(temp_dir or get_config('paths.temp_dir', './temp'))
        self.max_memory_size = self._parse_size(
            get_config('cache.max_memory_size', '512MB')
        )
        self.cleanup_on_exit = get_config('cache.cleanup_on_exit', True)
        
        # 确保临时目录存在
        ensure_dir(self.temp_dir)
        
        # 内存缓存
        self._memory_cache: Dict[str, Any] = {}
        self._memory_usage = 0
        
        logger.debug(f"初始化 CacheManager: temp_dir={self.temp_dir}")
    
    def _parse_size(self, size_str: str) -> int:
        """
        解析大小字符串为字节数
        
        Args:
            size_str: 大小字符串（如 '512MB'）
            
        Returns:
            字节数
        """
        size_str = size_str.upper().strip()
        
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4,
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                try:
                    return int(float(size_str[:-len(suffix)]) * multiplier)
                except ValueError:
                    break
        
        # 默认返回 512MB
        return 512 * 1024 * 1024
    
    def create_temp_dir(self, prefix: str = "wmr_") -> Path:
        """
        创建临时目录
        
        Args:
            prefix: 目录名前缀
            
        Returns:
            临时目录路径
        """
        temp_path = Path(tempfile.mkdtemp(prefix=prefix, dir=self.temp_dir))
        logger.debug(f"创建临时目录: {temp_path}")
        return temp_path
    
    def create_temp_file(
        self,
        suffix: str = "",
        prefix: str = "wmr_"
    ) -> Path:
        """
        创建临时文件
        
        Args:
            suffix: 文件后缀
            prefix: 文件名前缀
            
        Returns:
            临时文件路径
        """
        fd, path = tempfile.mkstemp(
            suffix=suffix,
            prefix=prefix,
            dir=self.temp_dir
        )
        os.close(fd)
        
        logger.debug(f"创建临时文件: {path}")
        return Path(path)
    
    def cleanup_temp_dir(self, temp_path: Union[str, Path]):
        """
        清理临时目录
        
        Args:
            temp_path: 临时目录路径
        """
        temp_path = Path(temp_path)
        
        if temp_path.exists() and temp_path.is_dir():
            try:
                shutil.rmtree(temp_path)
                logger.debug(f"清理临时目录: {temp_path}")
            except Exception as e:
                logger.warning(f"清理临时目录失败: {temp_path} - {e}")
    
    def cleanup_temp_file(self, temp_path: Union[str, Path]):
        """
        清理临时文件
        
        Args:
            temp_path: 临时文件路径
        """
        delete_file(temp_path, ignore_errors=True)
    
    def cleanup_all(self):
        """清理所有临时文件和目录"""
        if not self.temp_dir.exists():
            return
        
        try:
            for item in self.temp_dir.iterdir():
                delete_file(item, ignore_errors=True)
            logger.info(f"清理所有临时文件: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    def set_memory_cache(self, key: str, data: Any, size: int):
        """
        设置内存缓存
        
        Args:
            key: 缓存键
            data: 缓存数据
            size: 数据大小（字节）
        """
        # 检查是否超过内存限制
        if size > self.max_memory_size:
            raise CacheError(f"数据大小 ({size} bytes) 超过内存限制")
        
        # 清理空间（简单的 LRU 策略）
        while self._memory_usage + size > self.max_memory_size:
            if not self._memory_cache:
                break
            # 删除最早的缓存
            oldest_key = next(iter(self._memory_cache))
            self._remove_memory_cache(oldest_key)
        
        # 存储数据
        self._memory_cache[key] = {
            'data': data,
            'size': size,
        }
        self._memory_usage += size
        
        logger.debug(f"内存缓存: key={key}, size={size}")
    
    def get_memory_cache(self, key: str) -> Optional[Any]:
        """
        获取内存缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存数据或 None
        """
        if key in self._memory_cache:
            # 移到末尾（LRU更新）
            entry = self._memory_cache.pop(key)
            self._memory_cache[key] = entry
            return entry['data']
        return None
    
    def _remove_memory_cache(self, key: str):
        """移除内存缓存项"""
        if key in self._memory_cache:
            size = self._memory_cache[key]['size']
            del self._memory_cache[key]
            self._memory_usage -= size
    
    def clear_memory_cache(self):
        """清空内存缓存"""
        self._memory_cache.clear()
        self._memory_usage = 0
        logger.debug("清空内存缓存")
    
    def get_memory_usage(self) -> int:
        """获取当前内存使用量"""
        return self._memory_usage
    
    def get_disk_usage(self) -> int:
        """获取临时目录磁盘使用量"""
        total = 0
        
        if not self.temp_dir.exists():
            return 0
        
        for dirpath, dirnames, filenames in os.walk(self.temp_dir):
            for f in filenames:
                fp = Path(dirpath) / f
                try:
                    total += fp.stat().st_size
                except:
                    pass
        
        return total
    
    def __del__(self):
        """析构时清理"""
        if self.cleanup_on_exit:
            self.cleanup_all()
