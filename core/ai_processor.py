"""
AI 智能修复模块
提供高级图像修复功能，使用多尺度融合技术提升效果
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Union

from utils import (
    get_logger,
    create_mask,
    validate_roi,
    load_image,
    save_image,
)
from utils.exceptions import ImageProcessingError
from core.image_processor import ImageProcessor

logger = get_logger()


class AIImageProcessor:
    """
    AI 图像处理器 - 高级多尺度融合修复
    
    使用多尺度修复融合技术，结合多种传统算法
    获得比单一算法更好的修复效果
    
    注意：这是基于传统 OpenCV 算法的高级实现，
    通过多尺度融合和多算法组合来提升修复质量。
    相比单一 TELEA 或 NS 算法有明显改进。
    """
    
    MODELS = {
        'advanced': '高级修复（多尺度融合）',
        'telea': 'TELEA 快速修复',
        'ns': 'NS 纹理修复',
    }
    
    def __init__(self, model_name: str = 'advanced', device: str = 'cpu'):
        """
        初始化 AI 处理器
        
        Args:
            model_name: 模型/算法名称
            device: 运行设备（预留参数）
        """
        self.model_name = model_name
        self.device = device
        
        # 默认使用高级修复
        if model_name == 'lama':
            model_name = 'advanced'
        
        self.traditional_processor = ImageProcessor(algorithm='telea', radius=5)
        
        logger.debug(f"初始化 AIImageProcessor: model={model_name}")
    
    def remove_watermark(
        self,
        image: np.ndarray,
        roi: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        智能去除水印
        
        Args:
            image: 输入图像 (BGR 格式)
            roi: 水印区域 (x, y, width, height)
            
        Returns:
            修复后的图像
        """
        try:
            # 验证 ROI
            height, width = image.shape[:2]
            roi = validate_roi(roi, width, height)
            
            logger.debug(f"高级修复处理水印区域: {roi}")
            
            if self.model_name == 'advanced':
                return self._advanced_inpainting(image, roi)
            else:
                # 使用单一传统算法
                processor = ImageProcessor(algorithm=self.model_name, radius=5)
                return processor.remove_watermark(image, roi)
            
        except Exception as e:
            logger.error(f"高级修复失败: {e}")
            # 出错时回退到传统算法
            logger.info("回退到传统修复算法")
            return self.traditional_processor.remove_watermark(image, roi)
    
    def _advanced_inpainting(
        self,
        image: np.ndarray,
        roi: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        高级修复算法 - 多尺度融合
        
        通过以下步骤提升修复质量：
        1. 多尺度遮罩：使用不同核大小膨胀遮罩
        2. 多算法融合：结合 TELEA 和 NS 算法
        3. 高斯平滑：减少修复痕迹
        4. 智能混合：根据遮罩平滑过渡
        """
        from utils.image_utils import dilate_mask
        
        # 创建基础遮罩
        mask = create_mask(image.shape, roi)
        
        results = []
        weights = []
        
        # 使用用户设置的半径，如果没有设置则使用默认值
        radius = getattr(self, 'radius', 3)
        
        # 小尺度 - 保持细节
        mask_small = dilate_mask(mask, kernel_size=radius)
        if np.any(mask_small > 0):
            result_small = cv2.inpaint(image, mask_small, radius, cv2.INPAINT_TELEA)
            results.append(result_small)
            weights.append(0.4)
        
        # 中等尺度 - 平衡细节和结构
        mask_medium = dilate_mask(mask, kernel_size=radius + 2)
        if np.any(mask_medium > 0):
            result_medium = cv2.inpaint(image, mask_medium, radius + 2, cv2.INPAINT_NS)
            results.append(result_medium)
            weights.append(0.4)
        
        # 大尺度 - 平滑过渡
        mask_large = dilate_mask(mask, kernel_size=radius + 4)
        if np.any(mask_large > 0):
            result_large = cv2.inpaint(image, mask_large, radius + 4, cv2.INPAINT_TELEA)
            results.append(result_large)
            weights.append(0.2)
        
        if not results:
            return image
        
        # 归一化权重并融合
        weights = np.array(weights) / sum(weights)
        fused = np.zeros_like(image, dtype=np.float32)
        for result, weight in zip(results, weights):
            fused += result.astype(np.float32) * weight
        fused = fused.astype(np.uint8)
        
        # 边缘平滑处理 - 使用更大的核
        blurred = cv2.GaussianBlur(fused, (7, 7), 0)
        
        # 根据遮罩混合 - 使用100%覆盖水印区域
        mask_normalized = mask.astype(np.float32) / 255.0
        if len(image.shape) == 3:
            mask_normalized = np.expand_dims(mask_normalized, axis=2)
        
        # 完全替换水印区域
        result = (
            image * (1 - mask_normalized) + 
            blurred * mask_normalized
        ).astype(np.uint8)
        
        return result
    
    def process_file(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        roi: Tuple[int, int, int, int],
        quality: int = 95
    ) -> Path:
        """处理图像文件"""
        image = load_image(input_path)
        result = self.remove_watermark(image, roi)
        output_path = save_image(result, output_path, quality)
        return output_path
    
    @classmethod
    def is_available(cls) -> bool:
        """检查高级修复是否可用"""
        return True
    
    @classmethod
    def get_available_models(cls) -> list:
        """获取可用的模型列表"""
        return list(cls.MODELS.keys())


class HybridProcessor:
    """混合处理器 - 根据情况选择传统算法或高级修复"""
    
    def __init__(self, use_ai: bool = False, ai_device: str = 'cpu', radius: int = 3):
        self.use_ai = use_ai
        self.ai_device = ai_device
        self.radius = radius
        self.traditional_processor = ImageProcessor(radius=radius)
        self.ai_processor = None
        
        if self.use_ai:
            self.ai_processor = AIImageProcessor(model_name='advanced', device=ai_device)
            self.ai_processor.radius = radius  # 传递半径到高级处理器
            logger.info("启用高级修复模式（多尺度融合）")
        else:
            logger.info("使用传统处理模式")
    
    def remove_watermark(self, image: np.ndarray, roi: Tuple[int, int, int, int]) -> np.ndarray:
        if self.use_ai and self.ai_processor:
            return self.ai_processor.remove_watermark(image, roi)
        else:
            return self.traditional_processor.remove_watermark(image, roi)
    
    def process_file(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        roi: Tuple[int, int, int, int],
        quality: int = 95
    ) -> Path:
        image = load_image(input_path)
        result = self.remove_watermark(image, roi)
        output_path = save_image(result, output_path, quality)
        return output_path


def remove_watermark_with_ai(
    image: np.ndarray,
    roi: Tuple[int, int, int, int],
    model_name: str = 'advanced',
    device: str = 'cpu'
) -> np.ndarray:
    """便捷函数：使用高级修复去除水印"""
    processor = AIImageProcessor(model_name=model_name, device=device)
    return processor.remove_watermark(image, roi)
