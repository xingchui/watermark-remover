"""
主窗口模块
应用程序主界面
"""

import sys
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QComboBox,
    QSpinBox, QGroupBox, QSplitter, QMessageBox,
    QTabWidget, QProgressBar, QTextEdit, QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QImage

from services import TaskScheduler, ImageService, VideoService
from services.task_scheduler import TaskStatus
from utils import (
    get_config, get_logger, ensure_dir,
    is_supported_image_format, is_supported_video_format,
    get_file_extension, load_image
)
from gui.components import ImageViewer, WatermarkSelector, ProgressDialog, HelpDialog, BatchPanel
from gui.threads import ProcessingThread

logger = get_logger()


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化服务
        self.scheduler = TaskScheduler()
        self.image_service = ImageService(scheduler=self.scheduler)
        self.video_service = VideoService(scheduler=self.scheduler)
        
        # 当前文件
        self._current_file: Optional[Path] = None
        self._current_file_type: Optional[str] = None  # 'image' 或 'video'
        self._current_frame: Optional[np.ndarray] = None
        
        # 切换文件标志（避免切换时错误保存ROI）
        self._switching_file = False
        
        # 处理线程
        self._processing_thread: Optional[ProcessingThread] = None
        
        # 初始化UI
        self._init_ui()
        
        # 启动处理线程
        self._start_processing_thread()
        
        # 加载配置
        self._load_settings()
        
        logger.info("主窗口初始化完成")
    
    def _init_ui(self):
        """初始化UI"""
        # 窗口设置
        self.setWindowTitle(get_config('ui.window_title', '水印去除工具'))
        self.setMinimumSize(1000, 700)
        self.resize(
            get_config('ui.window_width', 1200),
            get_config('ui.window_height', 800)
        )
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # === 左侧面板 ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # 文件选择组
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        self._label_file_path = QLabel("未选择文件")
        self._label_file_path.setObjectName("file_path_label")
        self._label_file_path.setWordWrap(True)
        file_layout.addWidget(self._label_file_path)
        
        btn_layout = QHBoxLayout()
        
        self._btn_select_image = QPushButton("选择图像")
        self._btn_select_image.setObjectName("primary_button")
        self._btn_select_image.clicked.connect(self._on_select_image)
        btn_layout.addWidget(self._btn_select_image)
        
        self._btn_select_video = QPushButton("选择视频")
        self._btn_select_video.setObjectName("primary_button")
        self._btn_select_video.clicked.connect(self._on_select_video)
        btn_layout.addWidget(self._btn_select_video)
        
        file_layout.addLayout(btn_layout)
        left_layout.addWidget(file_group)
        
        # 参数设置组
        params_group = QGroupBox("处理参数")
        params_layout = QVBoxLayout(params_group)
        params_layout.setSpacing(5)
        
        # 算法选择 (紧凑)
        algo_layout = QHBoxLayout()
        algo_layout.setSpacing(5)
        algo_layout.addWidget(QLabel("算法:"))
        self._combo_algorithm = QComboBox()
        self._combo_algorithm.addItems(["TELEA", "NS", "高级"])
        self._combo_algorithm.setCurrentText(get_config('processing.image.algorithm', 'telea').upper())
        self._combo_algorithm.setFixedWidth(100)
        algo_layout.addWidget(self._combo_algorithm)
        algo_layout.addStretch()
        params_layout.addLayout(algo_layout)
        
        # AI 设备选择（使用新的layout，避免重复添加）
        self._ai_device_layout = QHBoxLayout()
        self._ai_device_layout.addWidget(QLabel("AI 设备:"))
        self._combo_ai_device = QComboBox()
        self._combo_ai_device.addItems(["CPU", "CUDA (GPU)"])
        ai_device = get_config('processing.ai.device', 'cpu')
        self._combo_ai_device.setCurrentText("CUDA (GPU)" if ai_device == 'cuda' else "CPU")
        self._ai_device_layout.addWidget(self._combo_ai_device)
        
        # AI 状态标签
        from core import AIImageProcessor
        self._label_ai_status = QLabel()
        if AIImageProcessor.is_available():
            self._label_ai_status.setText("高级修复: 已启用")
            self._label_ai_status.setStyleSheet("color: #4CAF50;")
        else:
            self._label_ai_status.setText("高级修复: 不可用")
            self._label_ai_status.setStyleSheet("color: #f44336;")
        
        # 创建一个容器来隐藏AI设备选择
        ai_container = QWidget()
        ai_container.setLayout(self._ai_device_layout)
        ai_container.setVisible(False)
        
        params_layout.addWidget(self._label_ai_status)
        params_layout.addWidget(ai_container)
        
        # 修复半径 + 输出质量 (同一行，紧凑布局)
        radius_quality_layout = QHBoxLayout()
        radius_quality_layout.setSpacing(8)
        
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(QLabel("半径:"))
        self._spin_radius = QSpinBox()
        self._spin_radius.setRange(1, 50)
        self._spin_radius.setValue(get_config('processing.image.inpainting_radius', 3))
        self._spin_radius.setFixedWidth(60)
        radius_layout.addWidget(self._spin_radius)
        radius_quality_layout.addLayout(radius_layout)
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("质量:"))
        self._spin_quality = QSpinBox()
        self._spin_quality.setRange(1, 100)
        self._spin_quality.setValue(get_config('processing.image.quality', 95))
        self._spin_quality.setFixedWidth(60)
        quality_layout.addWidget(self._spin_quality)
        radius_quality_layout.addLayout(quality_layout)
        
        params_layout.addLayout(radius_quality_layout)
        
        left_layout.addWidget(params_group)
        
        # 水印选择器
        self._watermark_selector = WatermarkSelector()
        self._watermark_selector.roi_changed.connect(self._on_roi_changed)
        self._watermark_selector.apply_clicked.connect(self._on_apply_roi)
        self._watermark_selector.clear_clicked.connect(self._on_clear_roi)
        left_layout.addWidget(self._watermark_selector)
        
        # 操作按钮
        action_group = QGroupBox("操作")
        action_layout = QVBoxLayout(action_group)
        
        self._btn_process = QPushButton("开始处理")
        self._btn_process.setObjectName("success_button")
        self._btn_process.setEnabled(False)
        self._btn_process.clicked.connect(self._on_process)
        action_layout.addWidget(self._btn_process)
        
        self._btn_preview = QPushButton("预览效果")
        self._btn_preview.setEnabled(False)
        self._btn_preview.clicked.connect(self._on_preview)
        action_layout.addWidget(self._btn_preview)

        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #cccccc;")
        line.setFixedHeight(1)
        action_layout.addSpacing(10)
        action_layout.addWidget(line)
        action_layout.addSpacing(10)

        # 帮助按钮
        self._btn_help = QPushButton("❓ 使用帮助")
        self._btn_help.setObjectName("help_button")
        self._btn_help.clicked.connect(self._on_show_help)
        action_layout.addWidget(self._btn_help)

        left_layout.addWidget(action_group)
        
        # 批量处理面板
        self._batch_panel = BatchPanel()
        self._batch_panel.files_selected.connect(self._on_batch_files_selected)
        self._batch_panel.batch_start.connect(self._on_batch_start)
        self._batch_panel.file_preview.connect(self._on_batch_file_preview)
        self._batch_panel.file_selection_changed.connect(self._on_batch_file_selected)
        left_layout.addWidget(self._batch_panel)
        
        # 进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        left_layout.addWidget(self._progress_bar)
        
        left_layout.addStretch()
        
        # 添加到分割器
        splitter.addWidget(left_panel)
        
        # === 右侧面板 ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 图像预览
        preview_group = QGroupBox("图像预览")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(5, 5, 5, 5)
        
        self._image_viewer = ImageViewer()
        self._image_viewer.roi_selected.connect(self._on_viewer_roi_selected)
        preview_layout.addWidget(self._image_viewer)
        
        right_layout.addWidget(preview_group)
        
        # 日志显示
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(5, 5, 5, 5)
        
        self._text_log = QTextEdit()
        self._text_log.setObjectName("log_text")
        self._text_log.setReadOnly(True)
        log_layout.addWidget(self._text_log)
        
        right_layout.addWidget(log_group)
        
        # 添加到分割器
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([350, 850])
        
        # 状态栏
        self._status_bar = self.statusBar()
        self._status_bar.showMessage("就绪")
    
    def _start_processing_thread(self):
        """启动处理线程"""
        self._processing_thread = ProcessingThread(self.scheduler, self)
        self._processing_thread.task_started.connect(self._on_task_started)
        self._processing_thread.task_progress.connect(self._on_task_progress)
        self._processing_thread.task_completed.connect(self._on_task_completed)
        self._processing_thread.task_failed.connect(self._on_task_failed)
        self._processing_thread.start()
    
    def _load_settings(self):
        """加载设置"""
        # 可以在这里恢复用户偏好设置
        pass
    
    def _on_select_image(self):
        """选择图像"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图像",
            "",
            "图像文件 (*.png *.jpg *.jpeg *.webp *.bmp);;所有文件 (*.*)"
        )
        
        if file_path:
            self._load_file(file_path, 'image')
    
    def _on_select_video(self):
        """选择视频"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.flv *.mkv);;所有文件 (*.*)"
        )
        
        if file_path:
            self._load_file(file_path, 'video')
    
    def _load_file(self, file_path: str, file_type: str):
        """
        加载文件
        
        Args:
            file_path: 文件路径
            file_type: 文件类型 ('image' 或 'video')
        """
        try:
            self._current_file = Path(file_path)
            self._current_file_type = file_type
            
            self._label_file_path.setText(str(self._current_file))
            
            if file_type == 'image':
                # 加载图像（使用 load_image 以支持中文路径）
                image = load_image(str(self._current_file))
                
                self._current_frame = image
                self._image_viewer.set_image(image)
                
                # 更新水印选择器的图像尺寸
                height, width = image.shape[:2]
                self._watermark_selector.set_image_size(width, height)
                
                self._log(f"加载图像: {self._current_file.name} ({width}x{height})")
                
            elif file_type == 'video':
                # 加载视频第一帧
                frame = self.video_service.extract_frame(self._current_file, 0)
                self._current_frame = frame
                self._image_viewer.set_image(frame)
                
                # 获取视频信息
                info = self.video_service.get_video_info(self._current_file)
                
                # 更新水印选择器的图像尺寸
                self._watermark_selector.set_image_size(info['width'], info['height'])
                
                self._log(f"加载视频: {self._current_file.name}")
                self._log(f"  分辨率: {info['width']}x{info['height']}")
                self._log(f"  帧率: {info['fps']:.2f}")
                self._log(f"  总帧数: {info['frame_count']}")
                self._log(f"  时长: {info['duration']:.2f}秒")
            
            # 启用按钮
            self._btn_process.setEnabled(True)
            self._btn_preview.setEnabled(True)
            
            # 启用选择模式
            self._image_viewer.enable_selection(True)
            
            self._status_bar.showMessage(f"已加载: {self._current_file.name}")
            
        except Exception as e:
            logger.error(f"加载文件失败: {e}")
            QMessageBox.critical(self, "错误", f"加载文件失败:\n{e}")
    
    def _on_viewer_roi_selected(self, x: int, y: int, w: int, h: int):
        """图像查看器ROI选择处理"""
        self._watermark_selector.set_roi(x, y, w, h)
        # 获取原始图像尺寸用于调试
        orig_w, orig_h = self._image_viewer.get_original_size()
        display_scale = self._image_viewer.get_display_scale()
        self._log(f"选择区域: ({x}, {y}) {w}x{h} [原始尺寸: {orig_w}x{orig_h}, 显示比例: {display_scale:.2f}]")
    
    def _on_roi_changed(self, x: int, y: int, w: int, h: int):
        """ROI改变处理"""
        # 更新图像查看器的ROI显示
        self._image_viewer.set_roi(x, y, w, h)
        
        # 切换文件时不保存ROI
        if self._switching_file:
            return
        
        # 保存当前选中文件的ROI
        self._save_current_file_roi()
    
    def _save_current_file_roi(self):
        """保存当前选中文件的ROI"""
        # 获取当前批量面板选中的文件
        selected_items = self._batch_panel.file_list.selectedItems()
        if selected_items:
            file_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
            if file_path:
                roi = self._watermark_selector.get_roi()
                # 获取图像原始尺寸用于验证
                if self._current_frame is not None:
                    orig_h, orig_w = self._current_frame.shape[:2]
                    self._log(f"保存ROI: {Path(file_path).name} -> {roi} [图像: {orig_w}x{orig_h}]")
                else:
                    self._log(f"保存ROI: {Path(file_path).name} -> {roi}")
                self._batch_panel.set_file_roi(file_path, roi)
    
    def _on_apply_roi(self):
        """应用ROI"""
        roi = self._watermark_selector.get_roi()
        if roi:
            self._image_viewer.set_roi(*roi)
            self._log(f"应用区域: {roi}")
            # 保存ROI到当前文件
            self._save_current_file_roi()
    
    def _on_clear_roi(self):
        """清除ROI"""
        self._image_viewer.clear_roi()
        self._log("清除选择区域")
    
    def _on_preview(self):
        """预览效果"""
        if self._current_frame is None:
            return
        
        roi = self._watermark_selector.get_roi()
        if not roi:
            QMessageBox.warning(self, "警告", "请先选择水印区域")
            return
        
        try:
            # 创建预览图像
            from core import ImageProcessor, AIImageProcessor
            
            algorithm_text = self._combo_algorithm.currentText()
            
            # 检查是否使用高级修复
            if '高级' in algorithm_text:
                processor = AIImageProcessor(model_name='advanced')
            else:
                processor = ImageProcessor(
                    algorithm=algorithm_text.lower(),
                    radius=self._spin_radius.value()
                )
            
            preview = processor.remove_watermark(self._current_frame, roi)
            
            # 显示预览
            self._image_viewer.set_image(preview)
            self._log("显示处理预览（按ESC恢复原始图像）")
            
            # 3秒后恢复
            QTimer.singleShot(3000, lambda: self._image_viewer.set_image(self._current_frame))
            
        except Exception as e:
            logger.error(f"预览失败: {e}")
            QMessageBox.critical(self, "错误", f"预览失败:\n{e}")

    def _on_show_help(self):
        """显示帮助文档"""
        help_dialog = HelpDialog(self)
        help_dialog.exec()

    def _on_process(self):
        """开始处理"""
        if self._current_file is None:
            return
        
        roi = self._watermark_selector.get_roi()
        if not roi:
            QMessageBox.warning(self, "警告", "请先选择水印区域")
            return
        
        # 禁用处理按钮
        self._btn_process.setEnabled(False)
        self._btn_preview.setEnabled(False)
        
        # 显示进度条
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        
        # 获取参数
        algorithm_text = self._combo_algorithm.currentText()
        # 转换为小写用于处理（高级除外）
        if '高级' in algorithm_text:
            algorithm = algorithm_text  # 高级修复保持原样
        else:
            algorithm = algorithm_text.lower()  # TELEA -> telea, NS -> ns
        radius = self._spin_radius.value()
        quality = self._spin_quality.value()
        
        # 检查是否使用高级修复
        use_ai = '高级' in algorithm_text or 'advanced' in algorithm
        ai_device = 'cuda' if self._combo_ai_device.currentText() == 'CUDA (GPU)' else 'cpu'
        
        # 生成输出路径
        output_dir = get_config('paths.output_dir', './output')
        ensure_dir(output_dir)
        
        from utils.file_utils import generate_output_path
        output_path = generate_output_path(
            self._current_file, output_dir, suffix="_removed"
        )
        
        self._log(f"开始处理: {self._current_file.name}")
        if use_ai:
            self._log(f"  算法: 高级修复 (多尺度融合), 质量: {quality}")
        else:
            self._log(f"  算法: {algorithm_text.upper()}, 半径: {radius}, 质量: {quality}")
        self._log(f"  区域: {roi}")
        
        try:
            if self._current_file_type == 'image':
                # 提交图像处理任务
                # 传递原始algorithm_text以识别高级修复
                task_id = self._processing_thread.submit_image_task(
                    str(self._current_file),
                    str(output_path),
                    roi,
                    algorithm=algorithm_text,  # 传递原始文本以识别"高级"
                    radius=radius,
                    quality=quality,
                    ai_device=ai_device
                )
                self._current_task_id = task_id
                
            elif self._current_file_type == 'video':
                # 提交视频处理任务
                task_id = self._processing_thread.submit_video_task(
                    str(self._current_file),
                    str(output_path),
                    roi,
                    algorithm=algorithm_text,  # 传递原始文本以识别"高级"
                    radius=radius,
                    ai_device=ai_device
                )
                self._current_task_id = task_id
                
        except Exception as e:
            logger.error(f"提交任务失败: {e}")
            QMessageBox.critical(self, "错误", f"提交任务失败:\n{e}")
            self._btn_process.setEnabled(True)
            self._btn_preview.setEnabled(True)
            self._progress_bar.setVisible(False)
    
    def _on_task_started(self, task_id: str):
        """任务开始处理"""
        self._log(f"任务开始: {task_id[:8]}...")
        self._status_bar.showMessage("处理中...")
    
    def _on_task_progress(self, task_id: str, current: int, total: int, message: str):
        """任务进度处理"""
        # 检查是否是批量任务
        if hasattr(self, '_batch_task_ids') and task_id in self._batch_task_ids:
            # 批量任务进度 - 可以在这里更新
            if message:
                self._status_bar.showMessage(f"批量处理: {message}")
            return
        
        # 单文件任务进度
        if hasattr(self, '_current_task_id') and task_id == self._current_task_id:
            progress = int(current * 100 / total) if total > 0 else current
            self._progress_bar.setValue(progress)
            if message:
                self._status_bar.showMessage(message)
    
    def _on_task_completed(self, task_id: str, output_path: str):
        """任务完成处理"""
        # 检查是否是批量任务
        if hasattr(self, '_batch_task_ids') and task_id in self._batch_task_ids:
            self._batch_task_ids.remove(task_id)
            self._log(f"[OK] 任务完成: {output_path}")
            
            # 更新进度
            total = len(self._batch_task_ids) + 1  # 包含已完成的任务
            completed = total - len(self._batch_task_ids)
            self._batch_panel.set_progress(completed, total, f"已完成 {completed}/{total}")
            
            # 检查是否所有批量任务都完成
            if not self._batch_task_ids:
                self._log("所有批量任务已完成")
                self._batch_panel.set_running(False)
                self._btn_process.setEnabled(True)
                self._btn_preview.setEnabled(True)
            return
        
        # 单文件任务处理
        if hasattr(self, '_current_task_id') and task_id == self._current_task_id:
            self._progress_bar.setValue(100)
            self._log(f"[OK] 处理完成: {output_path}")
            self._status_bar.showMessage("处理完成")
            
            QMessageBox.information(self, "完成", f"处理完成!\n输出文件:\n{output_path}")
            
            # 恢复按钮
            self._btn_process.setEnabled(True)
            self._btn_preview.setEnabled(True)
            self._progress_bar.setVisible(False)
    
    def _on_task_failed(self, task_id: str, error_message: str):
        """任务失败处理"""
        # 检查是否是批量任务
        if hasattr(self, '_batch_task_ids') and task_id in self._batch_task_ids:
            self._batch_task_ids.remove(task_id)
            logger.error(f"批量任务失败: {error_message}")
            self._log(f"[FAILED] 任务失败: {error_message}")
            
            # 检查是否所有批量任务都完成（失败也算完成）
            if not self._batch_task_ids:
                self._log("所有批量任务已完成（部分失败）")
                self._batch_panel.set_running(False)
                self._btn_process.setEnabled(True)
                self._btn_preview.setEnabled(True)
            return
        
        # 单文件任务处理
        if hasattr(self, '_current_task_id') and task_id == self._current_task_id:
            logger.error(f"任务失败: {error_message}")
            self._log(f"[FAILED] 处理失败: {error_message}")
            self._status_bar.showMessage("处理失败")
            
            QMessageBox.critical(self, "错误", f"处理失败:\n{error_message}")
            
            # 恢复按钮
            self._btn_process.setEnabled(True)
            self._btn_preview.setEnabled(True)
            self._progress_bar.setVisible(False)
    
    def _log(self, message: str):
        """
        添加日志
        
        Args:
            message: 日志消息
        """
        logger.info(message)
        self._text_log.append(message)
        # 滚动到底部
        scrollbar = self._text_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _on_batch_files_selected(self, files: list):
        """批处理文件选择回调"""
        self._log(f"已选择 {len(files)} 个文件用于批量处理")
    
    def _on_batch_file_preview(self, file_path: str):
        """批处理文件预览回调"""
        from pathlib import Path
        from utils import load_image, is_supported_image_format, is_supported_video_format
        
        file_path = Path(file_path)
        
        try:
            if is_supported_image_format(file_path):
                # 加载图像预览
                image = load_image(str(file_path))
                self._current_frame = image
                self._image_viewer.set_image(image)
                
                # 更新水印选择器
                height, width = image.shape[:2]
                self._watermark_selector.set_image_size(width, height)
                
                self._log(f"预览图像: {file_path.name} ({width}x{height})")
                
            elif is_supported_video_format(file_path):
                # 加载视频第一帧预览
                frame = self.video_service.extract_frame(file_path, 0)
                self._current_frame = frame
                self._image_viewer.set_image(frame)
                
                # 获取视频信息
                info = self.video_service.get_video_info(file_path)
                
                # 更新水印选择器
                self._watermark_selector.set_image_size(info['width'], info['height'])
                
                self._log(f"预览视频: {file_path.name}")
                self._log(f"  分辨率: {info['width']}x{info['height']}")
            
            # 启用选择模式
            self._image_viewer.enable_selection(True)
            self._status_bar.showMessage(f"预览: {file_path.name}")
            
        except Exception as e:
            logger.error(f"预览失败: {e}")
            self._log(f"[ERROR] 预览失败: {e}")
    
    def _on_batch_file_selected(self, file_path: str):
        """批量文件列表中选中某个文件"""
        from pathlib import Path
        from utils import load_image, is_supported_image_format, is_supported_video_format
        
        # 设置切换文件标志，避免触发ROI保存
        self._switching_file = True
        
        file_path = Path(file_path)
        
        try:
            width, height = 0, 0
            
            if is_supported_image_format(file_path):
                # 加载图像
                image = load_image(str(file_path))
                self._current_frame = image
                self._image_viewer.set_image(image)
                
                # 获取尺寸
                height, width = image.shape[:2]
                self._watermark_selector.set_image_size(width, height)
                
                self._log(f"选中图像: {file_path.name} ({width}x{height})")
                
            elif is_supported_video_format(file_path):
                # 加载视频第一帧
                frame = self.video_service.extract_frame(file_path, 0)
                self._current_frame = frame
                self._image_viewer.set_image(frame)
                
                # 获取视频信息
                info = self.video_service.get_video_info(file_path)
                width, height = info['width'], info['height']
                self._watermark_selector.set_image_size(width, height)
                
                self._log(f"选中视频: {file_path.name}")
            
            # 加载或清除ROI
            self._load_roi_for_file(str(file_path))
            
            # 启用选择模式
            self._image_viewer.enable_selection(True)
            self._status_bar.showMessage(f"选中: {file_path.name}")
            
        except Exception as e:
            logger.error(f"加载文件失败: {e}")
            self._log(f"[ERROR] 加载失败: {e}")
        finally:
            # 重置切换文件标志
            self._switching_file = False
    
    def _load_roi_for_file(self, file_path: str):
        """加载文件对应的ROI"""
        saved_roi = self._batch_panel.get_file_roi(file_path)
        if saved_roi:
            self._watermark_selector.set_roi(*saved_roi)
            self._image_viewer.set_roi(*saved_roi)
            self._log(f"加载文件ROI: {saved_roi}")
        else:
            # 使用无信号清除方法
            self._watermark_selector.clear_roi()
            self._image_viewer.clear_roi()
    
    def _on_batch_start(self, config: dict):
        """开始批量处理"""
        files = config.get("files", [])
        if not files:
            QMessageBox.warning(self, "警告", "请先选择要处理的文件")
            return
        
        # 获取参数
        algorithm_text = self._combo_algorithm.currentText()
        if '高级' in algorithm_text:
            algorithm = algorithm_text
        else:
            algorithm = algorithm_text.lower()
        radius = self._spin_radius.value()
        quality = self._spin_quality.value()
        max_workers = config.get("max_workers", 4)
        
        # 获取配置
        same_roi = config.get("same_roi", True)
        file_rois = config.get("file_rois", {})
        
        # 检查是否有文件设置了ROI
        files_with_roi = [f for f in files if file_rois.get(f)]
        
        roi = None  # 默认值
        if same_roi:
            # 使用同一 ROI
            roi = self._watermark_selector.get_roi()
            if not roi and not files_with_roi:
                QMessageBox.warning(self, "警告", "请先选择水印区域或为文件设置ROI")
                return
            self._log(f"开始批量处理 {len(files)} 个文件")
            self._log(f"  模式: 同一ROI, 并发数: {max_workers}")
        else:
            # 每个文件独立ROI
            if files_with_roi:
                self._log(f"开始批量处理 {len(files)} 个文件")
                self._log(f"  模式: 独立ROI (已设置: {len(files_with_roi)}个), 并发数: {max_workers}")
            else:
                QMessageBox.warning(self, "警告", "未勾选同一ROI时，请先为各文件设置水印区域")
                return
        
        # 禁用单文件处理按钮
        self._btn_process.setEnabled(False)
        self._btn_preview.setEnabled(False)
        
        # 设置批量面板状态
        self._batch_panel.set_running(True)
        
        # 处理批量文件
        self._process_batch_files(files, same_roi, roi, file_rois, algorithm, radius, quality)
    
    def _process_batch_files(self, files: list, same_roi: bool, common_roi: tuple, 
                             file_rois: dict, algorithm: str, radius: int, quality: int):
        """逐个处理批量文件"""
        output_dir = get_config('paths.output_dir', './output')
        ensure_dir(output_dir)
        
        from utils.file_utils import generate_output_path
        from pathlib import Path
        
        total = len(files)
        self._batch_panel.set_progress(0, total, "准备处理...")
        
        # 记录已提交的任务ID
        self._batch_task_ids = []
        
        for idx, file_path in enumerate(files):
            try:
                input_path = Path(file_path)
                output_path = generate_output_path(input_path, output_dir, suffix="_removed")
                
                # 获取该文件对应的ROI
                if same_roi:
                    # 使用同一ROI
                    file_roi = common_roi
                else:
                    # 使用文件独立ROI
                    file_roi = file_rois.get(file_path)
                
                # 跳过没有ROI的文件
                if not file_roi:
                    self._log(f"跳过 (无ROI): {input_path.name}")
                    continue
                
                # 判断文件类型
                if is_supported_image_format(input_path):
                    task_id = self._processing_thread.submit_image_task(
                        str(input_path),
                        str(output_path),
                        file_roi,
                        algorithm=algorithm,
                        radius=radius,
                        quality=quality
                    )
                    self._batch_task_ids.append(task_id)
                elif is_supported_video_format(input_path):
                    task_id = self._processing_thread.submit_video_task(
                        str(input_path),
                        str(output_path),
                        file_roi,
                        algorithm=algorithm,
                        radius=radius
                    )
                    self._batch_task_ids.append(task_id)
                
                self._log(f"已提交: {input_path.name} (ROI: {file_roi})")
                
            except Exception as e:
                self._log(f"提交失败 {file_path}: {e}")
                
            except Exception as e:
                self._log(f"提交失败 {file_path}: {e}")
            
            # 更新进度 - 只是提交进度，不是完成进度
            self._batch_panel.set_progress(idx + 1, total, f"已提交 {idx + 1}/{total}")
        
        self._log(f"批量处理任务已全部提交，共 {len(self._batch_task_ids)} 个任务")
        
        # 不再立即设置 running=False，而是等待任务完成
        # 通过 task_completed 和 task_failed 信号来跟踪
    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止处理线程
        if self._processing_thread:
            self._processing_thread.stop()
        
        # 停止调度器
        self.scheduler.stop()
        
        logger.info("应用程序关闭")
        event.accept()
