"""
水印检测模块
提供自动水印检测功能（基础实现）
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List
from utils import get_logger
from utils.exceptions import ImageProcessingError

logger = get_logger()


class WatermarkDetector:
    """水印检测器"""
    
    def __init__(
        self,
        threshold: float = 0.8,
        min_area: int = 100
    ):
        """
        初始化水印检测器
        
        Args:
            threshold: 检测阈值
            min_area: 最小区域面积
        """
        self.threshold = threshold
        self.min_area = min_area
        
        logger.debug(f"初始化 WatermarkDetector: threshold={threshold}")
    
    def detect(
        self,
        image: np.ndarray,
        hint_region: Optional[Tuple[int, int, int, int]] = None
    ) -> List[Tuple[int, int, int, int]]:
        """
        检测图像中的水印区域
        
        注意：这是基础实现，实际水印检测是一个复杂的问题，
        通常需要机器学习或特定启发式算法。
        
        当前实现基于简单的图像特征检测：
        - 高对比度区域
        - 边缘密度
        - 颜色一致性
        
        Args:
            image: 输入图像
            hint_region: 提示区域（优先在此区域内搜索）
            
        Returns:
            检测到的水印区域列表 [(x, y, w, h), ...]
        """
        logger.debug("开始水印检测")
        
        detections = []
        
        # 如果提供了提示区域，只在该区域内搜索
        if hint_region:
            x, y, w, h = hint_region
            roi_image = image[y:y+h, x:x+w]
            local_detections = self._detect_in_region(roi_image)
            
            # 转换回全局坐标
            for lx, ly, lw, lh in local_detections:
                detections.append((x + lx, y + ly, lw, lh))
        else:
            # 在四个角落搜索常见的水印位置
            height, width = image.shape[:2]
            
            # 定义角落区域
            corner_regions = [
                (0, 0, width // 4, height // 4),  # 左上
                (width * 3 // 4, 0, width // 4, height // 4),  # 右上
                (0, height * 3 // 4, width // 4, height // 4),  # 左下
                (width * 3 // 4, height * 3 // 4, width // 4, height // 4),  # 右下
                (width // 3, height * 3 // 4, width // 3, height // 4),  # 底部中央
            ]
            
            for region in corner_regions:
                x, y, w, h = region
                # 确保不越界
                w = min(w, width - x)
                h = min(h, height - y)
                
                if w > 0 and h > 0:
                    roi_image = image[y:y+h, x:x+w]
                    local_detections = self._detect_in_region(roi_image)
                    
                    for lx, ly, lw, lh in local_detections:
                        detections.append((x + lx, y + ly, lw, lh))
        
        logger.debug(f"检测到 {len(detections)} 个可能的水印区域")
        return detections
    
    def _detect_in_region(
        self,
        image: np.ndarray
    ) -> List[Tuple[int, int, int, int]]:
        """
        在指定区域内检测水印
        
        Args:
            image: 区域图像
            
        Returns:
            检测到的区域列表
        """
        detections = []
        
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 边缘检测
            edges = cv2.Canny(gray, 50, 150)
            
            # 形态学操作连接边缘
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            
            # 查找轮廓
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # 过滤小区域
                if area < self.min_area:
                    continue
                
                # 获取边界框
                x, y, w, h = cv2.boundingRect(contour)
                
                # 宽高比检查（水印通常是扁平的）
                aspect_ratio = float(w) / h if h > 0 else 0
                if aspect_ratio > 5 or aspect_ratio < 0.2:
                    continue
                
                # 计算区域得分
                score = self._calculate_score(gray[y:y+h, x:x+w])
                
                if score > self.threshold:
                    detections.append((x, y, w, h))
            
        except Exception as e:
            logger.warning(f"区域检测失败: {e}")
        
        return detections
    
    def _calculate_score(self, region: np.ndarray) -> float:
        """
        计算区域的水印可能性得分
        
        Args:
            region: 区域图像（灰度）
            
        Returns:
            得分 (0-1)
        """
        if region.size == 0:
            return 0.0
        
        # 计算特征
        mean = np.mean(region)
        std = np.std(region)
        
        # 高对比度区域更有可能是水印
        contrast_score = min(std / 50.0, 1.0)
        
        # 检查边缘密度
        edges = cv2.Canny(region, 50, 150)
        edge_density = np.sum(edges > 0) / region.size
        edge_score = min(edge_density * 10, 1.0)
        
        # 综合得分
        score = (contrast_score + edge_score) / 2.0
        
        return score
    
    def detect_text_regions(
        self,
        image: np.ndarray
    ) -> List[Tuple[int, int, int, int]]:
        """
        检测可能的文本水印区域
        
        基于 MSER (Maximally Stable Extremal Regions) 算法
        
        Args:
            image: 输入图像
            
        Returns:
            文本区域列表
        """
        regions = []
        
        try:
            # 转换为灰度
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 创建 MSER 检测器
            mser = cv2.MSER_create()
            
            # 检测区域
            msers, bboxes = mser.detectRegions(gray)
            
            # 过滤区域
            for bbox in bboxes:
                x, y, w, h = bbox
                
                # 过滤太小的区域
                if w < 10 or h < 10:
                    continue
                
                # 过滤太大的区域
                if w > gray.shape[1] // 2 or h > gray.shape[0] // 2:
                    continue
                
                # 宽高比检查
                aspect_ratio = float(w) / h
                if 0.1 < aspect_ratio < 10:
                    regions.append((x, y, w, h))
            
        except Exception as e:
            logger.warning(f"文本区域检测失败: {e}")
        
        return regions
