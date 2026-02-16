"""
视频服务模块
提供视频处理业务逻辑封装
"""

from pathlib import Path
from typing import Optional, Tuple, Union, Callable, List
from core import VideoProcessor
from utils import (
    validate_video_file,
    validate_output_path,
    validate_roi,
    generate_output_path,
    get_config,
    get_logger,
    list_files,
)
from utils.exceptions import VideoProcessingError
from services.task_scheduler import TaskScheduler, TaskType, Task

logger = get_logger()


class VideoService:
    """视频服务"""
    
    def __init__(
        self,
        scheduler: Optional[TaskScheduler] = None,
        output_dir: Optional[str] = None
    ):
        """
        初始化视频服务
        
        Args:
            scheduler: 任务调度器
            output_dir: 默认输出目录
        """
        self.scheduler = scheduler
        self.output_dir = output_dir or get_config('paths.output_dir', './output')
        
        # 创建视频处理器
        self.processor = VideoProcessor()
        
        logger.debug("初始化 VideoService")
    
    def process(
        self,
        input_path: Union[str, Path],
        roi: Tuple[int, int, int, int],
        output_path: Optional[Union[str, Path]] = None,
        algorithm: Optional[str] = None,
        radius: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Path:
        """
        处理单个视频
        
        Args:
            input_path: 输入视频路径
            roi: 水印区域 (x, y, width, height)
            output_path: 输出路径（None则自动生成）
            algorithm: 修复算法 ('telea', 'ns', 或 'advanced')
            radius: 修复半径
            progress_callback: 进度回调(current_frame, total_frames)
            
        Returns:
            输出文件路径
        """
        # 验证输入文件
        input_path = validate_video_file(input_path)
        
        # 生成输出路径
        if output_path is None:
            output_path = generate_output_path(
                input_path, self.output_dir, suffix="_removed"
            )
        else:
            output_path = Path(output_path)
            validate_output_path(output_path.parent)
        
        logger.info(f"处理视频: {input_path} -> {output_path}")
        
        # 检查是否使用高级修复
        use_advanced = algorithm and ('advanced' in str(algorithm).lower() or '高级' in str(algorithm))
        
        # 创建处理器（传递algorithm以支持高级模式）
        processor = VideoProcessor(algorithm=algorithm, radius=radius, use_advanced=use_advanced)
        
        # 处理
        output_path = processor.remove_watermark(
            input_path, output_path, roi, progress_callback
        )
        
        return output_path
    
    def process_async(
        self,
        input_path: Union[str, Path],
        roi: Tuple[int, int, int, int],
        output_path: Optional[Union[str, Path]] = None,
        algorithm: Optional[str] = None,
        radius: Optional[int] = None
    ) -> str:
        """
        异步处理视频（添加到任务队列）
        
        Args:
            input_path: 输入视频路径
            roi: 水印区域
            output_path: 输出路径
            algorithm: 修复算法
            radius: 修复半径
            
        Returns:
            任务ID
        """
        if not self.scheduler:
            raise VideoProcessingError("未提供任务调度器")
        
        # 验证输入
        input_path = validate_video_file(input_path)
        
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
        }
        
        task_id = self.scheduler.add_task(
            TaskType.VIDEO,
            str(input_path),
            str(output_path),
            params
        )
        
        logger.debug(f"添加视频处理任务: {task_id}")
        
        return task_id
    
    def get_video_info(self, input_path: Union[str, Path]) -> dict:
        """
        获取视频信息
        
        Args:
            input_path: 视频文件路径
            
        Returns:
            视频信息字典
        """
        input_path = validate_video_file(input_path)
        return self.processor.get_video_info(input_path)
    
    def extract_frame(
        self,
        input_path: Union[str, Path],
        frame_index: int = 0
    ):
        """
        提取视频帧
        
        Args:
            input_path: 视频文件路径
            frame_index: 帧索引
            
        Returns:
            帧图像
        """
        input_path = validate_video_file(input_path)
        return self.processor.extract_frame(input_path, frame_index)
    
    def preview_mask(
        self,
        input_path: Union[str, Path],
        roi: Tuple[int, int, int, int],
        frame_index: int = 0
    ):
        """
        预览遮罩效果
        
        Args:
            input_path: 视频文件路径
            roi: 水印区域
            frame_index: 帧索引
            
        Returns:
            带遮罩预览的帧
        """
        input_path = validate_video_file(input_path)
        return self.processor.preview_mask_on_frame(input_path, roi, frame_index)
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的视频格式"""
        from utils.validators import get_supported_video_formats
        return get_supported_video_formats()
    
    def list_videos(
        self,
        directory: Union[str, Path],
        recursive: bool = False
    ) -> List[Path]:
        """
        列出目录中的视频文件
        
        Args:
            directory: 目录路径
            recursive: 是否递归子目录
            
        Returns:
            视频文件路径列表
        """
        formats = self.get_supported_formats()
        return list_files(directory, extensions=formats, recursive=recursive)
