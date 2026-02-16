"""
图像处理模块
提供图像去水印核心功能
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Union
from utils import (
    load_image,
    save_image,
    create_mask,
    dilate_mask,
    validate_roi,
    validate_algorithm,
    validate_quality,
    validate_inpainting_radius,
    get_config,
    get_logger,
)
from utils.exceptions import ImageProcessingError

logger = get_logger()


class ImageProcessor:
    """图像处理器"""
    
    # OpenCV Inpainting 算法映射
    ALGORITHMS = {
        'telea': cv2.INPAINT_TELEA,
        'ns': cv2.INPAINT_NS,
    }
    
    def __init__(
        self,
        algorithm: Optional[str] = None,
        radius: Optional[int] = None,
        quality: Optional[int] = None
    ):
        """
        初始化图像处理器
        
        Args:
            algorithm: 修复算法 ('telea' 或 'ns')
            radius: 修复半径
            quality: 输出质量 (1-100)
        """
        self.algorithm = validate_algorithm(
            algorithm or get_config('processing.image.algorithm', 'telea')
        )
        self.radius = validate_inpainting_radius(
            radius or get_config('processing.image.inpainting_radius', 3)
        )
        self.quality = validate_quality(
            quality or get_config('processing.image.quality', 95)
        )
        
        logger.debug(
            f"初始化 ImageProcessor: algorithm={self.algorithm}, "
            f"radius={self.radius}, quality={self.quality}"
        )
    
    def remove_watermark(
        self,
        image: np.ndarray,
        roi: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        去除图像水印
        
        Args:
            image: 输入图像 (OpenCV BGR格式)
            roi: 水印区域 (x, y, width, height)
            
        Returns:
            处理后的图像
            
        Raises:
            ImageProcessingError: 处理失败
        """
        try:
            # 验证 ROI
            height, width = image.shape[:2]
            roi = validate_roi(roi, width, height)
            
            logger.debug(f"处理水印区域: {roi}")
            
            # 创建遮罩
            mask = create_mask(image.shape, roi)
            
            # 膨胀遮罩（扩大修复区域以获得更好效果）
            mask = dilate_mask(mask, kernel_size=self.radius)
            
            # 执行修复
            result = self._inpaint(image, mask)
            
            logger.debug("水印去除完成")
            return result
            
        except Exception as e:
            logger.error(f"去除水印失败: {e}")
            raise ImageProcessingError(f"去除水印失败: {e}")
    
    def _inpaint(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> np.ndarray:
        """
        执行 OpenCV Inpainting
        
        Args:
            image: 输入图像
            mask: 遮罩图像
            
        Returns:
            修复后的图像
        """
        # 获取算法
        algorithm = self.ALGORITHMS.get(self.algorithm, cv2.INPAINT_TELEA)
        
        # 处理多通道图像
        if len(image.shape) == 3 and image.shape[2] == 3:
            # BGR 图像
            result = cv2.inpaint(image, mask, self.radius, algorithm)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            # BGRA 图像 - 分离Alpha通道
            bgr = image[:, :, :3]
            alpha = image[:, :, 3]
            
            # 修复BGR通道
            result_bgr = cv2.inpaint(bgr, mask, self.radius, algorithm)
            
            # 合并Alpha通道
            result = np.dstack([result_bgr, alpha])
        else:
            # 灰度图像
            result = cv2.inpaint(image, mask, self.radius, algorithm)
        
        return result
    
    def process_file(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        roi: Tuple[int, int, int, int]
    ) -> Path:
        """
        处理图像文件
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            roi: 水印区域
            
        Returns:
            输出文件路径
        """
        logger.info(f"处理图像: {input_path}")
        
        # 加载图像
        image = load_image(input_path)
        
        # 处理
        result = self.remove_watermark(image, roi)
        
        # 保存
        output_path = save_image(result, output_path, self.quality)
        
        logger.info(f"图像处理完成: {output_path}")
        return output_path
    
    def preview_mask(
        self,
        image_shape: Tuple[int, ...],
        roi: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        预览遮罩效果
        
        Args:
            image_shape: 图像形状
            roi: 水印区域
            
        Returns:
            遮罩图像（用于预览）
        """
        mask = create_mask(image_shape, roi)
        return dilate_mask(mask, kernel_size=self.radius)


def remove_watermark_from_image(
    image: np.ndarray,
    roi: Tuple[int, int, int, int],
    algorithm: str = 'telea',
    radius: int = 3
) -> np.ndarray:
    """
    便捷函数：去除图像水印
    
    Args:
        image: 输入图像
        roi: 水印区域
        algorithm: 修复算法
        radius: 修复半径
        
    Returns:
        处理后的图像
    """
    processor = ImageProcessor(algorithm=algorithm, radius=radius)
    return processor.remove_watermark(image, roi)
