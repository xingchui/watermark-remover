"""
验证器模块
提供各种验证功能
"""

import re
from pathlib import Path
from typing import List, Union, Optional
from .exceptions import ValidationError


# 支持的图像格式
SUPPORTED_IMAGE_INPUT = ['.png', '.jpg', '.jpeg', '.webp', '.bmp']
SUPPORTED_IMAGE_OUTPUT = ['.png', '.jpg', '.jpeg', '.webp']

# 支持的视频格式
SUPPORTED_VIDEO_INPUT = ['.mp4', '.avi', '.mov', '.flv', '.mkv']
SUPPORTED_VIDEO_OUTPUT = ['.mp4', '.avi', '.mov']


def validate_file_exists(path: Union[str, Path]) -> Path:
    """
    验证文件是否存在
    
    Args:
        path: 文件路径
        
    Returns:
        Path对象
        
    Raises:
        ValidationError: 文件不存在
    """
    path = Path(path)
    
    if not path.exists():
        raise ValidationError(f"文件不存在: {path}")
    
    if not path.is_file():
        raise ValidationError(f"不是文件: {path}")
    
    return path


def validate_directory_exists(path: Union[str, Path]) -> Path:
    """
    验证目录是否存在
    
    Args:
        path: 目录路径
        
    Returns:
        Path对象
        
    Raises:
        ValidationError: 目录不存在
    """
    path = Path(path)
    
    if not path.exists():
        raise ValidationError(f"目录不存在: {path}")
    
    if not path.is_dir():
        raise ValidationError(f"不是目录: {path}")
    
    return path


def validate_image_file(
    path: Union[str, Path],
    check_format: bool = True
) -> Path:
    """
    验证图像文件
    
    Args:
        path: 文件路径
        check_format: 是否检查格式
        
    Returns:
        Path对象
        
    Raises:
        ValidationError: 验证失败
    """
    path = validate_file_exists(path)
    
    if check_format:
        ext = path.suffix.lower()
        if ext not in SUPPORTED_IMAGE_INPUT:
            raise ValidationError(
                f"不支持的图像格式: {ext}. "
                f"支持的格式: {', '.join(SUPPORTED_IMAGE_INPUT)}"
            )
    
    return path


def validate_video_file(
    path: Union[str, Path],
    check_format: bool = True
) -> Path:
    """
    验证视频文件
    
    Args:
        path: 文件路径
        check_format: 是否检查格式
        
    Returns:
        Path对象
        
    Raises:
        ValidationError: 验证失败
    """
    path = validate_file_exists(path)
    
    if check_format:
        ext = path.suffix.lower()
        if ext not in SUPPORTED_VIDEO_INPUT:
            raise ValidationError(
                f"不支持的视频格式: {ext}. "
                f"支持的格式: {', '.join(SUPPORTED_VIDEO_INPUT)}"
            )
    
    return path


def validate_roi(
    roi: tuple,
    image_width: int,
    image_height: int
) -> tuple:
    """
    验证 ROI 区域
    
    Args:
        roi: (x, y, width, height)
        image_width: 图像宽度
        image_height: 图像高度
        
    Returns:
        验证后的 ROI
        
    Raises:
        ValidationError: 验证失败
    """
    if not isinstance(roi, (tuple, list)) or len(roi) != 4:
        raise ValidationError(f"ROI 必须是包含4个元素的元组或列表: {roi}")
    
    x, y, w, h = roi
    
    # 检查类型
    if not all(isinstance(v, (int, float)) for v in [x, y, w, h]):
        raise ValidationError(f"ROI 值必须是数字: {roi}")
    
    # 转换为整数
    x, y, w, h = int(x), int(y), int(w), int(h)
    
    # 检查范围
    if x < 0 or y < 0:
        raise ValidationError(f"ROI 坐标不能为负: ({x}, {y})")
    
    if w <= 0 or h <= 0:
        raise ValidationError(f"ROI 宽高必须大于0: ({w}, {h})")
    
    if x >= image_width or y >= image_height:
        raise ValidationError(
            f"ROI 起点超出图像范围: ({x}, {y}) > ({image_width}, {image_height})"
        )
    
    # 限制在图像范围内
    w = min(w, image_width - x)
    h = min(h, image_height - y)
    
    return (x, y, w, h)


def validate_quality(quality: int) -> int:
    """
    验证图像质量参数
    
    Args:
        quality: 质量值 (1-100)
        
    Returns:
        验证后的质量值
        
    Raises:
        ValidationError: 验证失败
    """
    try:
        quality = int(quality)
    except (TypeError, ValueError):
        raise ValidationError(f"质量值必须是整数: {quality}")
    
    if quality < 1 or quality > 100:
        raise ValidationError(f"质量值必须在 1-100 之间: {quality}")
    
    return quality


def validate_inpainting_radius(radius: int) -> int:
    """
    验证修复半径参数
    
    Args:
        radius: 修复半径
        
    Returns:
        验证后的半径值
        
    Raises:
        ValidationError: 验证失败
    """
    try:
        radius = int(radius)
    except (TypeError, ValueError):
        raise ValidationError(f"修复半径必须是整数: {radius}")
    
    if radius < 1 or radius > 50:
        raise ValidationError(f"修复半径建议在 1-50 之间: {radius}")
    
    return radius


def validate_algorithm(algorithm: str) -> str:
    """
    验证修复算法
    
    Args:
        algorithm: 算法名称
        
    Returns:
        验证后的算法名称（小写）
        
    Raises:
        ValidationError: 验证失败
    """
    valid_algorithms = ['telea', 'ns']
    
    algorithm = algorithm.lower().strip()
    
    if algorithm not in valid_algorithms:
        raise ValidationError(
            f"不支持的算法: {algorithm}. "
            f"支持的算法: {', '.join(valid_algorithms)}"
        )
    
    return algorithm


def validate_output_path(
    path: Union[str, Path],
    must_not_exist: bool = False
) -> Path:
    """
    验证输出路径
    
    Args:
        path: 输出路径
        must_not_exist: 是否要求文件不存在
        
    Returns:
        Path对象
        
    Raises:
        ValidationError: 验证失败
    """
    path = Path(path)
    
    # 检查父目录
    parent = path.parent
    if parent.exists() and not parent.is_dir():
        raise ValidationError(f"父路径不是目录: {parent}")
    
    # 检查文件是否存在
    if must_not_exist and path.exists():
        raise ValidationError(f"输出文件已存在: {path}")
    
    return path


def get_supported_image_formats() -> List[str]:
    """获取支持的图像格式列表"""
    return SUPPORTED_IMAGE_INPUT.copy()


def get_supported_video_formats() -> List[str]:
    """获取支持的视频格式列表"""
    return SUPPORTED_VIDEO_INPUT.copy()


def is_supported_image_format(path: Union[str, Path]) -> bool:
    """检查是否为支持的图像格式"""
    ext = Path(path).suffix.lower()
    return ext in SUPPORTED_IMAGE_INPUT


def is_supported_video_format(path: Union[str, Path]) -> bool:
    """检查是否为支持的视频格式"""
    ext = Path(path).suffix.lower()
    return ext in SUPPORTED_VIDEO_INPUT


# AI/高级修复算法标识
AI_ALGORITHM_KEYWORDS = {'advanced', 'ai', 'lama', '智能', '高级'}


def is_ai_algorithm(algorithm: Optional[str]) -> bool:
    """
    检查是否为 AI/高级修复算法

    Args:
        algorithm: 算法名称

    Returns:
        是否为 AI 算法
    """
    if not algorithm:
        return False

    algorithm_lower = algorithm.lower()
    return any(keyword in algorithm_lower for keyword in AI_ALGORITHM_KEYWORDS)
