"""
文件操作工具模块
提供文件和目录操作功能
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Union
from .exceptions import FileOperationError
from .logger import get_logger

logger = get_logger()


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在，不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        Path对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_extension(filename: Union[str, Path]) -> str:
    """
    获取文件扩展名（小写）
    
    Args:
        filename: 文件名
        
    Returns:
        扩展名（包含点，如 '.jpg'）
    """
    return Path(filename).suffix.lower()


def get_filename_without_ext(filename: Union[str, Path]) -> str:
    """
    获取不带扩展名的文件名
    
    Args:
        filename: 文件名
        
    Returns:
        文件名（不含扩展名）
    """
    return Path(filename).stem


def generate_output_path(
    input_path: Union[str, Path],
    output_dir: Union[str, Path],
    suffix: str = "_removed",
    output_ext: Optional[str] = None
) -> Path:
    """
    生成输出文件路径
    
    Args:
        input_path: 输入文件路径
        output_dir: 输出目录
        suffix: 文件名后缀
        output_ext: 输出扩展名（None则保持原扩展名）
        
    Returns:
        输出文件路径
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    # 确保输出目录存在
    ensure_dir(output_dir)
    
    # 生成文件名
    name = input_path.stem + suffix
    if output_ext:
        ext = output_ext if output_ext.startswith('.') else '.' + output_ext
    else:
        ext = input_path.suffix
    
    output_path = output_dir / (name + ext)
    
    # 如果文件已存在，添加数字后缀
    counter = 1
    original_output = output_path
    while output_path.exists():
        output_path = output_dir / f"{original_output.stem}_{counter}{ext}"
        counter += 1
    
    return output_path


def list_files(
    directory: Union[str, Path],
    extensions: Optional[List[str]] = None,
    recursive: bool = False
) -> List[Path]:
    """
    列出目录中的文件
    
    Args:
        directory: 目录路径
        extensions: 文件扩展名列表（如 ['.jpg', '.png']）
        recursive: 是否递归子目录
        
    Returns:
        文件路径列表
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise FileOperationError(f"目录不存在: {directory}")
    
    if not directory.is_dir():
        raise FileOperationError(f"不是目录: {directory}")
    
    files = []
    
    if recursive:
        pattern = "**/*"
    else:
        pattern = "*"
    
    for path in directory.glob(pattern):
        if path.is_file():
            if extensions is None or path.suffix.lower() in extensions:
                files.append(path)
    
    return sorted(files)


def copy_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    overwrite: bool = False
) -> Path:
    """
    复制文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在文件
        
    Returns:
        目标文件路径
    """
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        raise FileOperationError(f"源文件不存在: {src}")
    
    if dst.exists() and not overwrite:
        raise FileOperationError(f"目标文件已存在: {dst}")
    
    ensure_dir(dst.parent)
    
    try:
        shutil.copy2(src, dst)
        logger.debug(f"复制文件: {src} -> {dst}")
        return dst
    except Exception as e:
        raise FileOperationError(f"复制文件失败: {e}")


def move_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    overwrite: bool = False
) -> Path:
    """
    移动文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在文件
        
    Returns:
        目标文件路径
    """
    src = Path(src)
    dst = Path(dst)
    
    if not src.exists():
        raise FileOperationError(f"源文件不存在: {src}")
    
    if dst.exists() and not overwrite:
        raise FileOperationError(f"目标文件已存在: {dst}")
    
    ensure_dir(dst.parent)
    
    try:
        shutil.move(str(src), str(dst))
        logger.debug(f"移动文件: {src} -> {dst}")
        return dst
    except Exception as e:
        raise FileOperationError(f"移动文件失败: {e}")


def delete_file(path: Union[str, Path], ignore_errors: bool = True):
    """
    删除文件
    
    Args:
        path: 文件路径
        ignore_errors: 是否忽略错误
    """
    path = Path(path)
    
    if not path.exists():
        if ignore_errors:
            return
        raise FileOperationError(f"文件不存在: {path}")
    
    try:
        if path.is_file():
            path.unlink()
            logger.debug(f"删除文件: {path}")
        elif path.is_dir():
            shutil.rmtree(path)
            logger.debug(f"删除目录: {path}")
    except Exception as e:
        if not ignore_errors:
            raise FileOperationError(f"删除失败: {e}")
        logger.warning(f"删除失败（已忽略）: {path} - {e}")


def clean_directory(
    directory: Union[str, Path],
    keep_files: Optional[List[str]] = None,
    pattern: Optional[str] = None
):
    """
    清理目录
    
    Args:
        directory: 目录路径
        keep_files: 保留的文件列表
        pattern: 删除文件匹配模式（如 '*.tmp'）
    """
    directory = Path(directory)
    
    if not directory.exists():
        return
    
    keep_files = keep_files or []
    keep_paths = [Path(f).name for f in keep_files]
    
    try:
        for item in directory.iterdir():
            # 检查是否在保留列表中
            if item.name in keep_paths:
                continue
            
            # 检查是否匹配模式
            if pattern and not item.match(pattern):
                continue
            
            delete_file(item, ignore_errors=True)
            
    except Exception as e:
        logger.warning(f"清理目录失败: {directory} - {e}")


def get_file_size(path: Union[str, Path]) -> int:
    """
    获取文件大小（字节）
    
    Args:
        path: 文件路径
        
    Returns:
        文件大小（字节）
    """
    path = Path(path)
    
    if not path.exists():
        raise FileOperationError(f"文件不存在: {path}")
    
    return path.stat().st_size


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的字符串（如 '1.5 MB'）
    """
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


# ==================== 上下文管理器 ====================

from contextlib import contextmanager
from typing import Generator


@contextmanager
def video_capture(path: Union[str, Path]) -> Generator:
    """
    OpenCV VideoCapture 上下文管理器

    Args:
        path: 视频文件路径

    Yields:
        cv2.VideoCapture 对象

    Example:
        with video_capture('input.mp4') as cap:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                # 处理帧
    """
    import cv2

    path = Path(path)
    cap = cv2.VideoCapture(str(path))

    if not cap.isOpened():
        raise FileOperationError(f"无法打开视频: {path}")

    try:
        yield cap
    finally:
        cap.release()


@contextmanager
def video_writer(
    path: Union[str, Path],
    fourcc: int,
    fps: float,
    size: tuple
) -> Generator:
    """
    OpenCV VideoWriter 上下文管理器

    Args:
        path: 输出视频路径
        fourcc: 视频编码
        fps: 帧率
        size: 视频尺寸 (width, height)

    Yields:
        cv2.VideoWriter 对象

    Example:
        with video_writer('output.mp4', fourcc, 30.0, (1920, 1080)) as out:
            for frame in frames:
                out.write(frame)
    """
    import cv2

    path = Path(path)
    ensure_dir(path.parent)

    out = cv2.VideoWriter(str(path), fourcc, fps, size)

    if not out.isOpened():
        raise FileOperationError(f"无法创建视频写入器: {path}")

    try:
        yield out
    finally:
        out.release()
