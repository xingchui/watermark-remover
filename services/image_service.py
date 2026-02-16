"""
图像服务模块
提供图像处理业务逻辑封装
"""

from pathlib import Path
from typing import Optional, Tuple, Union, Callable, List
from core import ImageProcessor
from utils import (
    validate_image_file,
    validate_output_path,
    validate_roi,
    generate_output_path,
    get_config,
    get_logger,
    list_files,
)
from utils.exceptions import ImageProcessingError
from services.task_scheduler import TaskScheduler, TaskType, Task

logger = get_logger()


class ImageService:
    """图像服务"""
    
    def __init__(
        self,
        scheduler: Optional[TaskScheduler] = None,
        output_dir: Optional[str] = None
    ):
        """
        初始化图像服务
        
        Args:
            scheduler: 任务调度器
            output_dir: 默认输出目录
        """
        self.scheduler = scheduler
        self.output_dir = output_dir or get_config('paths.output_dir', './output')
        
        # 创建图像处理器
        self.processor = ImageProcessor()
        
        logger.debug("初始化 ImageService")
    
    def process(
        self,
        input_path: Union[str, Path],
        roi: Tuple[int, int, int, int],
        output_path: Optional[Union[str, Path]] = None,
        algorithm: Optional[str] = None,
        radius: Optional[int] = None,
        quality: Optional[int] = None
    ) -> Path:
        """
        处理单张图像
        
        Args:
            input_path: 输入图像路径
            roi: 水印区域 (x, y, width, height)
            output_path: 输出路径（None则自动生成）
            algorithm: 修复算法
            radius: 修复半径
            quality: 输出质量
            
        Returns:
            输出文件路径
        """
        # 验证输入文件
        input_path = validate_image_file(input_path)
        
        # 生成输出路径
        if output_path is None:
            output_path = generate_output_path(
                input_path, self.output_dir, suffix="_removed"
            )
        else:
            output_path = Path(output_path)
            validate_output_path(output_path.parent)
        
        # 验证 ROI
        from utils.image_utils import load_image, get_image_size
        width, height = get_image_size(input_path)
        roi = validate_roi(roi, width, height)
        
        logger.info(f"处理图像: {input_path} -> {output_path}")
        
        # 创建处理器
        processor = ImageProcessor(
            algorithm=algorithm,
            radius=radius,
            quality=quality
        )
        
        # 处理
        output_path = processor.process_file(input_path, output_path, roi)
        
        return output_path
    
    def process_async(
        self,
        input_path: Union[str, Path],
        roi: Tuple[int, int, int, int],
        output_path: Optional[Union[str, Path]] = None,
        algorithm: Optional[str] = None,
        radius: Optional[int] = None,
        quality: Optional[int] = None
    ) -> str:
        """
        异步处理图像（添加到任务队列）
        
        Args:
            input_path: 输入图像路径
            roi: 水印区域
            output_path: 输出路径
            algorithm: 修复算法
            radius: 修复半径
            quality: 输出质量
            
        Returns:
            任务ID
        """
        if not self.scheduler:
            raise ImageProcessingError("未提供任务调度器")
        
        # 验证输入
        input_path = validate_image_file(input_path)
        
        # 生成输出路径
        if output_path is None:
            output_path = generate_output_path(
                input_path, self.output_dir, suffix="_removed"
            )
        else:
            output_path = Path(output_path)
        
        # 添加任务
        params = {
            'roi': roi,
            'algorithm': algorithm,
            'radius': radius,
            'quality': quality,
        }
        
        task_id = self.scheduler.add_task(
            TaskType.IMAGE,
            str(input_path),
            str(output_path),
            params
        )
        
        logger.debug(f"添加图像处理任务: {task_id}")
        
        return task_id
    
    def process_batch(
        self,
        input_paths: List[Union[str, Path]],
        roi: Tuple[int, int, int, int],
        algorithm: Optional[str] = None,
        radius: Optional[int] = None,
        quality: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Path]:
        """
        批量处理图像
        
        Args:
            input_paths: 输入图像路径列表
            roi: 水印区域
            algorithm: 修复算法
            radius: 修复半径
            quality: 输出质量
            progress_callback: 进度回调(current, total)
            
        Returns:
            输出文件路径列表
        """
        results = []
        total = len(input_paths)
        
        for i, input_path in enumerate(input_paths):
            try:
                output_path = self.process(
                    input_path, roi, None, algorithm, radius, quality
                )
                results.append(output_path)
                
                if progress_callback:
                    progress_callback(i + 1, total)
                    
            except Exception as e:
                logger.error(f"批量处理失败 [{input_path}]: {e}")
                raise
        
        return results
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的图像格式"""
        from utils.validators import get_supported_image_formats
        return get_supported_image_formats()
    
    def list_images(
        self,
        directory: Union[str, Path],
        recursive: bool = False
    ) -> List[Path]:
        """
        列出目录中的图像文件
        
        Args:
            directory: 目录路径
            recursive: 是否递归子目录
            
        Returns:
            图像文件路径列表
        """
        formats = self.get_supported_formats()
        return list_files(directory, extensions=formats, recursive=recursive)
