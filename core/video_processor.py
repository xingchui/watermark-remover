"""
视频处理模块
提供视频去水印核心功能
"""

import cv2
import numpy as np
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Tuple, Optional, Union, Callable, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import (
    ensure_dir,
    get_file_extension,
    generate_output_path,
    validate_roi,
    get_config,
    get_logger,
)
from utils.exceptions import VideoProcessingError
from core.image_processor import ImageProcessor
from core.ai_processor import HybridProcessor
from core.cache_manager import CacheManager

logger = get_logger()


def _copy_to_temp(video_path: Path) -> Path:
    """
    将视频文件复制到临时位置（处理中文路径问题）

    Args:
        video_path: 原始视频路径

    Returns:
        临时文件路径
    """
    temp_app_name = get_config('paths.temp_app_name', 'watermark_remover')
    temp_dir = Path(tempfile.gettempdir()) / temp_app_name
    ensure_dir(temp_dir)
    
    # 使用安全的临时文件名
    import uuid
    safe_name = f"video_{video_path.stem[:20]}_{uuid.uuid4().hex[:8]}{video_path.suffix}"
    temp_path = temp_dir / safe_name
    
    try:
        shutil.copy2(str(video_path), str(temp_path))
        return temp_path
    except Exception as e:
        raise VideoProcessingError(f"复制视频到临时位置失败: {e}")


class VideoProcessor:
    """视频处理器"""
    
    # 支持的算法列表
    SUPPORTED_ALGORITHMS = ['telea', 'ns', 'advanced']
    
    def __init__(
        self,
        algorithm: Optional[str] = None,
        radius: Optional[int] = None,
        max_memory_frames: Optional[int] = None,
        codec: Optional[str] = None,
        crf: Optional[int] = None,
        preset: Optional[str] = None,
        use_advanced: bool = False
    ):
        """
        初始化视频处理器
        
        Args:
            algorithm: 修复算法 ('telea', 'ns', 或 'advanced')
            radius: 修复半径
            max_memory_frames: 最大内存缓存帧数
            codec: 视频编码器
            crf: 视频质量参数
            preset: 编码速度预设
            use_advanced: 是否使用高级修复（多尺度融合）
        """
        # 判断是否使用高级修复
        if algorithm and ('advanced' in algorithm.lower() or '高级' in str(algorithm)):
            self.use_advanced = True
            self.algorithm = 'telea'  # 基础算法
        else:
            self.use_advanced = use_advanced
            self.algorithm = algorithm or get_config('processing.image.algorithm', 'telea')
        
        self.radius = radius or get_config('processing.image.inpainting_radius', 3)
        self.max_memory_frames = max_memory_frames or get_config('processing.video.max_memory_frames', 100)
        self.codec = codec or get_config('processing.video.codec', 'libx264')
        self.crf = crf or get_config('processing.video.crf', 18)
        self.preset = preset or get_config('processing.video.preset', 'medium')
        
        # 初始化图像处理器（传统算法）
        self.image_processor = ImageProcessor(
            algorithm=self.algorithm,
            radius=self.radius
        )
        
        # 初始化高级处理器（如果启用）
        if self.use_advanced:
            self.hybrid_processor = HybridProcessor(use_ai=True, ai_device='cpu', radius=self.radius)
            logger.debug(f"初始化 VideoProcessor: 使用高级修复 (多尺度融合)")
        else:
            self.hybrid_processor = None
            logger.debug(
                f"初始化 VideoProcessor: algorithm={self.algorithm}, "
                f"max_memory_frames={self.max_memory_frames}"
            )
        
        # 初始化缓存管理器
        self.cache_manager = CacheManager()
    
    def get_video_info(self, video_path: Union[str, Path]) -> dict:
        """
        获取视频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频信息字典
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise VideoProcessingError(f"视频文件不存在: {video_path}")
        
        # 复制到临时文件以处理中文路径
        temp_path = _copy_to_temp(video_path)
        
        try:
            cap = cv2.VideoCapture(str(temp_path))
            
            if not cap.isOpened():
                raise VideoProcessingError(f"无法打开视频: {video_path}")
            
            info = {
                'path': str(video_path),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0,
                'fourcc': int(cap.get(cv2.CAP_PROP_FOURCC)),
            }
            
            cap.release()
            
            logger.debug(f"视频信息: {info}")
            return info
        finally:
            # 清理临时文件
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except:
                pass
    
    def remove_watermark(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        roi: Tuple[int, int, int, int],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Path:
        """
        去除视频水印
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            roi: 水印区域 (x, y, width, height)
            progress_callback: 进度回调函数(current, total)
            
        Returns:
            输出视频路径
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        logger.info(f"处理视频: {input_path}")
        
        # 获取视频信息
        video_info = self.get_video_info(input_path)
        width = video_info['width']
        height = video_info['height']
        fps = video_info['fps']
        total_frames = video_info['frame_count']
        
        # 验证 ROI
        roi = validate_roi(roi, width, height)
        logger.debug(f"水印区域: {roi}")
        
        # 确保输出目录存在
        ensure_dir(output_path.parent)
        
        # 使用 ffmpeg 处理（保留音频）
        return self._process_with_ffmpeg(
            input_path, output_path, roi, fps, total_frames,
            video_info, progress_callback
        )
    
    def _process_with_ffmpeg(
        self,
        input_path: Path,
        output_path: Path,
        roi: Tuple[int, int, int, int],
        fps: float,
        total_frames: int,
        video_info: dict,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> Path:
        """
        使用 ffmpeg 处理视频（保留音频）
        
        处理流程：
        1. 提取音频
        2. 处理视频帧
        3. 合并音频和视频
        """
        temp_dir = self.cache_manager.create_temp_dir()
        
        try:
            # 处理视频帧
            processed_video = temp_dir / "processed_video.mp4"
            self._process_video_frames(
                input_path, processed_video, roi, fps,
                total_frames, progress_callback
            )
            
            # 提取并合并音频
            self._merge_audio(input_path, processed_video, output_path)
            
            logger.info(f"视频处理完成: {output_path}")
            return output_path
            
        finally:
            # 清理临时文件
            self.cache_manager.cleanup_temp_dir(temp_dir)
    
    def _process_video_frames(
        self,
        input_path: Path,
        output_path: Path,
        roi: Tuple[int, int, int, int],
        fps: float,
        total_frames: int,
        progress_callback: Optional[Callable[[int, int], None]]
    ):
        """处理视频帧"""
        # 复制到临时文件以处理中文路径
        temp_input = _copy_to_temp(input_path)
        
        try:
            # 打开输入视频
            cap = cv2.VideoCapture(str(temp_input))
            
            # 获取视频编码器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
            # 创建视频写入器
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            out = cv2.VideoWriter(
                str(output_path), fourcc, fps, (width, height)
            )
            
            if not out.isOpened():
                cap.release()
                raise VideoProcessingError(f"无法创建输出视频: {output_path}")
            
            try:
                frame_count = 0
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 根据设置选择处理器
                    if self.use_advanced and self.hybrid_processor:
                        processed_frame = self.hybrid_processor.remove_watermark(frame, roi)
                    else:
                        processed_frame = self.image_processor.remove_watermark(frame, roi)
                    
                    # 写入
                    out.write(processed_frame)
                    
                    frame_count += 1
                    
                    # 回调进度
                    if progress_callback and frame_count % 10 == 0:
                        progress_callback(frame_count, total_frames)
                
                # 最终进度回调
                if progress_callback:
                    progress_callback(total_frames, total_frames)
                    
            finally:
                cap.release()
                out.release()
        finally:
            # 清理临时输入文件
            try:
                if temp_input.exists():
                    temp_input.unlink()
            except:
                pass
    
    def _merge_audio(
        self,
        input_path: Path,
        video_path: Path,
        output_path: Path
    ):
        """
        合并音频和视频
        
        使用 ffmpeg 合并处理后的视频和原始音频
        """
        # 构建 ffmpeg 命令
        cmd = [
            'ffmpeg',
            '-y',  # 覆盖输出文件
            '-i', str(video_path),  # 处理后的视频
            '-i', str(input_path),  # 原始视频（提取音频）
            '-c:v', 'copy',  # 复制视频流
            '-c:a', get_config('processing.video.audio_codec', 'aac'),
            '-b:a', get_config('processing.video.audio_bitrate', '128k'),
            '-map', '0:v:0',  # 使用第一个输入的视频
            '-map', '1:a:0?',  # 使用第二个输入的音频（如果存在）
            '-shortest',  # 以最短的输入为准
            str(output_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug("音频合并完成")
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg 错误: {e.stderr}")
            raise VideoProcessingError(f"合并音频失败: {e.stderr}")
        except FileNotFoundError:
            logger.error("ffmpeg 未找到")
            raise VideoProcessingError(
                "ffmpeg 未安装或未添加到 PATH。请安装 ffmpeg: https://ffmpeg.org/download.html"
            )
    
    def extract_frame(
        self,
        video_path: Union[str, Path],
        frame_index: int = 0
    ) -> np.ndarray:
        """
        提取视频帧
        
        Args:
            video_path: 视频文件路径
            frame_index: 帧索引
            
        Returns:
            帧图像
        """
        video_path = Path(video_path)
        
        # 复制到临时文件以处理中文路径
        temp_path = _copy_to_temp(video_path)
        
        try:
            cap = cv2.VideoCapture(str(temp_path))
            
            if not cap.isOpened():
                raise VideoProcessingError(f"无法打开视频: {video_path}")
            
            try:
                # 设置帧位置
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                
                ret, frame = cap.read()
                if not ret:
                    raise VideoProcessingError(f"无法读取帧 {frame_index}")
                
                return frame
                
            finally:
                cap.release()
        finally:
            # 清理临时文件
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except:
                pass
    
    def preview_mask_on_frame(
        self,
        video_path: Union[str, Path],
        roi: Tuple[int, int, int, int],
        frame_index: int = 0
    ) -> np.ndarray:
        """
        在视频帧上预览遮罩
        
        Args:
            video_path: 视频文件路径
            roi: 水印区域
            frame_index: 帧索引
            
        Returns:
            带遮罩预览的帧
        """
        # 提取帧
        frame = self.extract_frame(video_path, frame_index)
        
        # 验证 ROI
        height, width = frame.shape[:2]
        roi = validate_roi(roi, width, height)
        
        # 创建遮罩预览
        mask = self.image_processor.preview_mask(frame.shape, roi)
        
        # 叠加遮罩到图像（红色半透明）
        overlay = frame.copy()
        overlay[mask > 0] = [0, 0, 255]  # 红色 BGR
        
        # 混合
        alpha = 0.3
        preview = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)
        
        # 绘制边框
        x, y, w, h = roi
        cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        return preview
