"""
处理线程模块
在后台执行处理任务，不阻塞UI
"""

from enum import Enum
from typing import Optional, Callable, Any
from PyQt6.QtCore import QThread, pyqtSignal
import tempfile
from pathlib import Path

from services import TaskScheduler, Task, TaskStatus, TaskType
from services.image_service import ImageService
from services.video_service import VideoService
from utils import get_logger, is_ai_algorithm, get_config, ensure_dir

logger = get_logger()


class ProcessingMode(Enum):
    """处理模式"""
    IMAGE = "image"
    VIDEO = "video"
    BATCH = "batch"


class ProcessingThread(QThread):
    """
    处理工作线程
    
    信号：
        - started: 任务开始 (task_id)
        - progress: 进度更新 (task_id, current, total, message)
        - completed: 任务完成 (task_id, output_path)
        - failed: 任务失败 (task_id, error_message)
    """
    
    # 信号定义
    task_started = pyqtSignal(str)  # task_id
    task_progress = pyqtSignal(str, int, int, str)  # task_id, current, total, message
    task_completed = pyqtSignal(str, str)  # task_id, output_path
    task_failed = pyqtSignal(str, str)  # task_id, error_message
    
    def __init__(
        self,
        scheduler: TaskScheduler,
        parent=None
    ):
        """
        初始化处理线程
        
        Args:
            scheduler: 任务调度器
            parent: 父对象
        """
        super().__init__(parent)
        
        self.scheduler = scheduler
        self._running = False
        
        # 创建服务
        self.image_service = ImageService(scheduler=scheduler)
        self.video_service = VideoService(scheduler=scheduler)
        
        # 设置调度器回调
        self.scheduler.set_callbacks(
            on_started=self._on_task_started,
            on_completed=self._on_task_completed,
            on_failed=self._on_task_failed,
            on_progress=self._on_progress_update
        )
        
        logger.debug("初始化 ProcessingThread")
    
    def _on_task_started(self, task: Task):
        """任务开始回调"""
        self.task_started.emit(task.id)
    
    def _on_task_completed(self, task: Task):
        """任务完成回调"""
        self.task_completed.emit(task.id, task.output_path)
    
    def _on_task_failed(self, task: Task):
        """任务失败回调"""
        self.task_failed.emit(task.id, task.error or "未知错误")
    
    def _on_progress_update(self, task: Task):
        """进度更新回调"""
        # 对于视频，total 设为 100，current 为 progress
        self.task_progress.emit(task.id, task.progress, 100, task.message)
    
    def run(self):
        """线程主循环"""
        self._running = True
        
        logger.info("处理线程已启动")
        
        # 启动调度器
        self.scheduler.start()
        
        # 等待线程停止
        while self._running:
            self.msleep(100)
        
        # 停止调度器
        self.scheduler.stop(wait=True)
        
        logger.info("处理线程已停止")
    
    def stop(self):
        """停止线程"""
        self._running = False
        self.scheduler.stop(wait=False)
        self.wait()
    
    def submit_image_task(
        self,
        input_path: str,
        output_path: str,
        roi: tuple,
        algorithm: Optional[str] = None,
        radius: Optional[int] = None,
        quality: Optional[int] = None,
        ai_device: str = 'cpu'
    ) -> str:
        """
        提交图像处理任务
        
        Args:
            input_path: 输入路径
            output_path: 输出路径
            roi: 水印区域
            algorithm: 算法
            radius: 半径
            quality: 质量
            ai_device: AI 设备 ('cpu' 或 'cuda')
            
        Returns:
            任务ID
        """
        params = {
            'roi': roi,
            'algorithm': algorithm,
            'radius': radius,
            'quality': quality,
            'ai_device': ai_device,
        }
        
        task_id = self.scheduler.add_task(
            TaskType.IMAGE,
            input_path,
            output_path,
            params
        )
        
        # 提交任务到线程池
        self.scheduler.submit_task(task_id, self._process_image_task)
        
        return task_id
    
    def submit_video_task(
        self,
        input_path: str,
        output_path: str,
        roi: tuple,
        algorithm: Optional[str] = None,
        radius: Optional[int] = None,
        ai_device: str = 'cpu'
    ) -> str:
        """
        提交视频处理任务
        
        Args:
            input_path: 输入路径
            output_path: 输出路径
            roi: 水印区域
            algorithm: 算法
            radius: 半径
            ai_device: AI 设备
            
        Returns:
            任务ID
        """
        params = {
            'roi': roi,
            'algorithm': algorithm,
            'radius': radius,
            'ai_device': ai_device,
        }
        
        task_id = self.scheduler.add_task(
            TaskType.VIDEO,
            input_path,
            output_path,
            params
        )
        
        # 提交任务到线程池
        self.scheduler.submit_task(task_id, self._process_video_task)
        
        return task_id
    
    def _process_image_task(self, task: Task):
        """
        处理图像任务
        
        Args:
            task: 任务对象
        """
        try:
            params = task.params
            roi = params.get('roi')
            algorithm = params.get('algorithm')
            radius = params.get('radius')
            quality = params.get('quality')
            ai_device = params.get('ai_device', 'cpu')
            
            # 检查是否使用 AI/高级修复
            use_ai = is_ai_algorithm(algorithm)
            
            # 更新进度
            self.scheduler.update_progress(task.id, 10, "正在处理图像...")
            
            if use_ai:
                # 使用 AI/高级处理
                from core import HybridProcessor
                processor = HybridProcessor(use_ai=True, ai_device=ai_device, radius=radius or 3)
                output_path = processor.process_file(
                    task.input_path,
                    task.output_path,
                    roi,
                    quality=quality
                )
            else:
                # 使用传统算法处理
                output_path = self.image_service.process(
                    task.input_path,
                    roi,
                    task.output_path,
                    algorithm=algorithm,
                    radius=radius,
                    quality=quality
                )
            
            # 更新进度
            self.scheduler.update_progress(task.id, 100, "处理完成")
            
            # 更新任务输出路径
            task.output_path = str(output_path)
            
        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            raise
    
    def _process_video_task(self, task: Task):
        """
        处理视频任务
        
        Args:
            task: 任务对象
        """
        try:
            params = task.params
            roi = params.get('roi')
            algorithm = params.get('algorithm')
            radius = params.get('radius')
            ai_device = params.get('ai_device', 'cpu')
            
            # 检查是否使用 AI/高级修复
            use_ai = is_ai_algorithm(algorithm)

            # 进度回调
            def progress_callback(current: int, total: int):
                progress = int(current * 100 / total) if total > 0 else 0
                self.scheduler.update_progress(
                    task.id, progress, f"处理中... {current}/{total}"
                )
            
            # 更新进度
            self.scheduler.update_progress(task.id, 5, "开始处理视频...")
            
            if use_ai:
                # 使用高级算法处理视频
                output_path = self._process_video_with_ai(
                    task.input_path,
                    roi,
                    task.output_path,
                    ai_device=ai_device,
                    radius=radius,
                    progress_callback=progress_callback
                )
            else:
                # 使用传统算法处理
                output_path = self.video_service.process(
                    task.input_path,
                    roi,
                    task.output_path,
                    algorithm=algorithm,
                    radius=radius,
                    progress_callback=progress_callback
                )
            
            # 更新进度
            self.scheduler.update_progress(task.id, 100, "处理完成")
            
            # 更新任务输出路径
            task.output_path = str(output_path)
            
        except Exception as e:
            logger.error(f"视频处理失败: {e}")
            raise
    
    def _process_video_with_ai(self, input_path: str, roi: tuple, output_path: str, 
                                ai_device: str = 'cpu', radius: int = 3,
                                progress_callback=None) -> Path:
        """使用高级算法处理视频"""
        from pathlib import Path
        from core import HybridProcessor, VideoProcessor
        from utils import ensure_dir, validate_roi
        import cv2
        import tempfile
        
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # 获取视频信息
        temp_processor = VideoProcessor()
        video_info = temp_processor.get_video_info(input_path)
        
        width = video_info['width']
        height = video_info['height']
        fps = video_info['fps']
        total_frames = video_info['frame_count']
        
        # 验证 ROI
        roi = validate_roi(roi, width, height)
        
        # 确保输出目录存在
        ensure_dir(output_path.parent)
        
        # 创建高级处理器
        hybrid_processor = HybridProcessor(use_ai=True, ai_device=ai_device, radius=radius)
        
        # 临时视频文件
        temp_app_name = get_config('paths.temp_app_name', 'watermark_remover')
        temp_dir = Path(tempfile.gettempdir()) / temp_app_name
        ensure_dir(temp_dir)
        temp_video = temp_dir / 'temp_processed.mp4'
        
        try:
            cap = cv2.VideoCapture(str(input_path))
            if not cap.isOpened():
                raise Exception(f"无法打开视频: {input_path}")
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(temp_video), fourcc, fps, (width, height))
            
            if not out.isOpened():
                cap.release()
                raise Exception("无法创建输出视频")
            
            try:
                frame_count = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    processed_frame = hybrid_processor.remove_watermark(frame, roi)
                    out.write(processed_frame)
                    frame_count += 1
                    if progress_callback and frame_count % 10 == 0:
                        progress_callback(frame_count, total_frames)
                
                if progress_callback:
                    progress_callback(total_frames, total_frames)
            finally:
                cap.release()
                out.release()
            
            # 合并音频
            self._merge_audio_video(input_path, temp_video, output_path)
            return output_path
        finally:
            try:
                if temp_video.exists():
                    temp_video.unlink()
            except:
                pass
    
    def _merge_audio_video(self, input_video: Path, processed_video: Path, output_path: Path):
        """合并音频和视频"""
        import subprocess
        from utils import get_config
        
        cmd = [
            'ffmpeg', '-y', '-i', str(processed_video), '-i', str(input_video),
            '-c:v', 'copy', '-c:a', get_config('processing.video.audio_codec', 'aac'),
            '-b:a', get_config('processing.video.audio_bitrate', '128k'),
            '-map', '0:v:0', '-map', '1:a:0?', '-shortest', str(output_path)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg 错误: {e.stderr}")
            raise Exception(f"合并音频失败: {e.stderr}")
        except FileNotFoundError:
            raise Exception("ffmpeg 未安装或未添加到 PATH")
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        return self.scheduler.cancel_task(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态或 None
        """
        task = self.scheduler.get_task(task_id)
        return task.status if task else None
