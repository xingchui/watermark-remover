"""
异常定义模块
自定义项目异常类
"""


class WatermarkRemoverError(Exception):
    """基础异常类"""
    pass


class ConfigError(WatermarkRemoverError):
    """配置错误"""
    pass


class ImageProcessingError(WatermarkRemoverError):
    """图像处理错误"""
    pass


class VideoProcessingError(WatermarkRemoverError):
    """视频处理错误"""
    pass


class FileOperationError(WatermarkRemoverError):
    """文件操作错误"""
    pass


class ValidationError(WatermarkRemoverError):
    """验证错误"""
    pass


class CacheError(WatermarkRemoverError):
    """缓存错误"""
    pass


class TaskError(WatermarkRemoverError):
    """任务错误"""
    pass
