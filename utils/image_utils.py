"""
图像工具模块
提供图像处理辅助功能
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Union, List
from PIL import Image
from .exceptions import ImageProcessingError
from .logger import get_logger

logger = get_logger()


def load_image(path: Union[str, Path]) -> np.ndarray:
    """
    加载图像文件
    
    Args:
        path: 图像文件路径
        
    Returns:
        OpenCV格式图像 (BGR)
        
    Raises:
        ImageProcessingError: 加载失败
    """
    path = Path(path)
    
    if not path.exists():
        raise ImageProcessingError(f"图像文件不存在: {path}")
    
    # 使用 PIL 加载以支持更多格式
    try:
        pil_image = Image.open(path)
        # 转换为RGB
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        # 转换为OpenCV格式 (BGR)
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return image
    except Exception as e:
        # 回退到OpenCV
        image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ImageProcessingError(f"无法加载图像: {path} - {e}")
        return image


def save_image(
    image: np.ndarray,
    path: Union[str, Path],
    quality: int = 95
) -> Path:
    """
    保存图像文件
    
    Args:
        image: OpenCV格式图像
        path: 保存路径
        quality: JPEG质量 (1-100)
        
    Returns:
        保存的文件路径
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    ext = path.suffix.lower()
    
    try:
        # 使用 PIL 保存以支持中文路径
        # 将 BGR 转换为 RGB
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        pil_image = Image.fromarray(image_rgb)
        
        # 根据扩展名保存
        if ext in ['.jpg', '.jpeg']:
            pil_image.save(path, quality=quality, optimize=True)
        elif ext == '.webp':
            pil_image.save(path, quality=quality)
        else:
            # PNG 等其他格式
            pil_image.save(path)
        
        logger.debug(f"保存图像: {path}")
        return path
        
    except Exception as e:
        raise ImageProcessingError(f"保存图像失败: {e}")


def get_image_size(path: Union[str, Path]) -> Tuple[int, int]:
    """
    获取图像尺寸（不加载完整图像）
    
    Args:
        path: 图像文件路径
        
    Returns:
        (宽度, 高度)
    """
    path = Path(path)
    
    try:
        with Image.open(path) as img:
            return img.size
    except Exception as e:
        # 回退到OpenCV
        image = cv2.imread(str(path))
        if image is None:
            raise ImageProcessingError(f"无法读取图像: {path}")
        height, width = image.shape[:2]
        return width, height


def resize_image(
    image: np.ndarray,
    max_size: Optional[int] = None,
    scale: Optional[float] = None
) -> np.ndarray:
    """
    调整图像大小
    
    Args:
        image: 输入图像
        max_size: 最大边长（保持比例）
        scale: 缩放比例
        
    Returns:
        调整后的图像
    """
    if scale is not None:
        new_width = int(image.shape[1] * scale)
        new_height = int(image.shape[0] * scale)
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    if max_size is not None:
        height, width = image.shape[:2]
        max_dim = max(height, width)
        
        if max_dim <= max_size:
            return image
        
        scale = max_size / max_dim
        new_width = int(width * scale)
        new_height = int(height * scale)
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    return image


def create_mask(
    image_shape: Tuple[int, ...],
    roi: Tuple[int, int, int, int]
) -> np.ndarray:
    """
    创建水印遮罩
    
    Args:
        image_shape: 图像形状 (height, width) 或 (height, width, channels)
        roi: 区域 (x, y, width, height)
        
    Returns:
        二值遮罩图像
    """
    height, width = image_shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    
    x, y, w, h = roi
    
    # 确保坐标在范围内
    x = max(0, x)
    y = max(0, y)
    x2 = min(width, x + w)
    y2 = min(height, y + h)
    
    if x2 > x and y2 > y:
        mask[y:y2, x:x2] = 255
    
    return mask


def dilate_mask(
    mask: np.ndarray,
    kernel_size: int = 3
) -> np.ndarray:
    """
    膨胀遮罩（扩大修复区域）
    
    Args:
        mask: 输入遮罩
        kernel_size: 膨胀核大小
        
    Returns:
        膨胀后的遮罩
    """
    if kernel_size <= 0:
        return mask
    
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    return cv2.dilate(mask, kernel, iterations=1)


def convert_to_rgba(image: np.ndarray) -> np.ndarray:
    """
    将图像转换为RGBA格式
    
    Args:
        image: 输入图像
        
    Returns:
        RGBA格式图像
    """
    if len(image.shape) == 2:
        # 灰度图转RGBA
        return cv2.cvtColor(image, cv2.COLOR_GRAY2RGBA)
    elif image.shape[2] == 3:
        # BGR转RGBA
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
    elif image.shape[2] == 4:
        # BGRA转RGBA
        return cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
    
    return image


def convert_to_bgr(image: np.ndarray) -> np.ndarray:
    """
    将图像转换为BGR格式（OpenCV默认）
    
    Args:
        image: 输入图像
        
    Returns:
        BGR格式图像
    """
    if len(image.shape) == 2:
        # 灰度图转BGR
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.shape[2] == 4:
        # BGRA转BGR
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    elif image.shape[2] == 3:
        # 已经是BGR
        return image
    
    return image


def get_image_info(path: Union[str, Path]) -> dict:
    """
    获取图像信息
    
    Args:
        path: 图像文件路径
        
    Returns:
        包含图像信息的字典
    """
    path = Path(path)
    
    try:
        with Image.open(path) as img:
            info = {
                'path': str(path),
                'format': img.format,
                'mode': img.mode,
                'width': img.width,
                'height': img.height,
                'size': (img.width, img.height),
            }
            
            # 尝试获取DPI
            if 'dpi' in img.info:
                info['dpi'] = img.info['dpi']
            
            return info
            
    except Exception as e:
        # 回退到OpenCV
        image = cv2.imread(str(path))
        if image is None:
            raise ImageProcessingError(f"无法读取图像信息: {path}")
        
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) > 2 else 1
        
        return {
            'path': str(path),
            'format': path.suffix.upper().lstrip('.'),
            'mode': 'BGR' if channels == 3 else 'GRAY',
            'width': width,
            'height': height,
            'size': (width, height),
            'channels': channels,
        }


def validate_image(path: Union[str, Path]) -> bool:
    """
    验证文件是否为有效图像
    
    Args:
        path: 文件路径
        
    Returns:
        是否有效
    """
    path = Path(path)
    
    if not path.exists():
        return False
    
    try:
        # 尝试用 PIL 打开
        with Image.open(path) as img:
            img.verify()
            return True
    except:
        # 回退到 OpenCV
        try:
            image = cv2.imread(str(path))
            return image is not None
        except:
            return False
