from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QProgressBar, QCheckBox, 
                             QSpinBox, QGroupBox, QFileDialog, QMessageBox,
                             QListWidgetItem, QAbstractItemView)
from PyQt6.QtCore import pyqtSignal, Qt
from pathlib import Path
from typing import Optional, Tuple, Dict


class BatchPanel(QWidget):
    """批量处理面板"""
    
    files_selected = pyqtSignal(list)  # 文件列表信号
    batch_start = pyqtSignal(dict)    # 开始批量处理信号
    file_preview = pyqtSignal(str)     # 文件预览信号 (发射文件路径)
    file_selection_changed = pyqtSignal(str)  # 文件选中变化信号 (发射文件路径)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.selected_files = []
        self.file_rois: Dict[str, Optional[Tuple[int, int, int, int]]] = {}  # 文件路径 -> ROI
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # === 已选择文件列表 ===
        list_label_layout = QHBoxLayout()
        list_label_layout.addWidget(QLabel("已选择文件:"))
        list_label_layout.addStretch()
        
        self.lbl_file_count = QLabel("0 个文件")
        self.lbl_file_count.setStyleSheet("color: #4CAF50; font-weight: bold;")
        list_label_layout.addWidget(self.lbl_file_count)
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setMinimumHeight(120)
        self.file_list.setMaximumHeight(200)
        
        # === 文件操作按钮 ===
        file_btn_layout = QHBoxLayout()
        file_btn_layout.setSpacing(5)
        
        self.btn_add = QPushButton("➕ 添加文件")
        self.btn_add.setToolTip("添加图像或视频文件")
        
        self.btn_remove = QPushButton("🗑️ 移除选中")
        self.btn_remove.setToolTip("从列表中移除选中的文件")
        self.btn_remove.setEnabled(False)
        
        self.btn_preview = QPushButton("👁️ 预览选中")
        self.btn_preview.setToolTip("在右侧预览区显示选中的文件")
        self.btn_preview.setEnabled(False)
        
        self.btn_clear = QPushButton("清空列表")
        self.btn_clear.setToolTip("清空所有已选择的文件")
        
        file_btn_layout.addWidget(self.btn_add)
        file_btn_layout.addWidget(self.btn_remove)
        file_btn_layout.addWidget(self.btn_preview)
        file_btn_layout.addWidget(self.btn_clear)
        
        # === 批量处理设置 ===
        settings_group = QGroupBox("处理设置")
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(6)
        
        # 同一ROI选项
        self.chk_same_roi = QCheckBox("✓ 使用同一ROI处理所有文件")
        self.chk_same_roi.setChecked(True)
        self.chk_same_roi.setToolTip("勾选后，所有文件将使用相同的水印区域进行批量处理")
        settings_layout.addWidget(self.chk_same_roi)
        
        # 并发数设置
        workers_layout = QHBoxLayout()
        workers_layout.setSpacing(10)
        workers_layout.addWidget(QLabel("并发数:"))
        self.spin_workers = QSpinBox()
        self.spin_workers.setRange(1, 16)
        self.spin_workers.setValue(4)
        self.spin_workers.setToolTip("同时处理的文件数量")
        workers_layout.addWidget(self.spin_workers)
        workers_layout.addStretch()
        
        self.chk_adaptive = QCheckBox("自适应调度")
        self.chk_adaptive.setChecked(True)
        self.chk_adaptive.setToolTip("根据文件大小自动调整处理优先级")
        workers_layout.addWidget(self.chk_adaptive)
        
        settings_layout.addLayout(workers_layout)
        settings_group.setLayout(settings_layout)
        
        # === 进度显示 ===
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(True)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setVisible(False)
        self.lbl_status.setStyleSheet("color: #2196F3;")
        
        # === 开始/取消按钮 ===
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        self.btn_start = QPushButton("🚀 开始批量处理")
        self.btn_start.setObjectName("success_button")
        self.btn_start.setEnabled(False)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setEnabled(False)
        
        action_layout.addWidget(self.btn_start, 1)
        action_layout.addWidget(self.btn_cancel)
        
        # === 组装布局 ===
        layout.addLayout(list_label_layout)
        layout.addWidget(self.file_list)
        layout.addLayout(file_btn_layout)
        layout.addWidget(settings_group)
        layout.addWidget(self.progress)
        layout.addWidget(self.lbl_status)
        layout.addLayout(action_layout)
        
        # 信号连接
        self.btn_add.clicked.connect(self._on_add_files)
        self.btn_remove.clicked.connect(self._on_remove_selected)
        self.btn_preview.clicked.connect(self._on_preview_selected)
        self.btn_clear.clicked.connect(self._on_clear_files)
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.file_list.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _on_add_files(self):
        """添加文件 - 弹出选择对话框"""
        # 弹出文件选择对话框，支持多选
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择媒体文件", "",
            "媒体文件 (*.png *.jpg *.jpeg *.webp *.bmp *.mp4 *.avi *.mov *.flv *.mkv);;图像 (*.png *.jpg *.jpeg *.webp *.bmp);;视频 (*.mp4 *.avi *.mov *.flv *.mkv);;所有文件 (*.*)"
        )
        if files:
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
            self._update_file_list()
    
    def _select_single_file(self):
        """选择单个文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择媒体文件", "",
            "媒体文件 (*.png *.jpg *.jpeg *.webp *.bmp *.mp4 *.avi *.mov *.flv *.mkv);;图像 (*.png *.jpg *.jpeg *.webp *.bmp);;视频 (*.mp4 *.avi *.mov *.flv *.mkv)"
        )
        if file_path:
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
                self._update_file_list()
    
    def _select_multiple_files(self):
        """选择多个文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择多个图像文件", "",
            "图像文件 (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if files:
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
            self._update_file_list()
    
    def _select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            try:
                from utils import get_supported_image_formats, get_supported_video_formats
                img_formats = get_supported_image_formats()
                vid_formats = get_supported_video_formats()
            except ImportError:
                img_formats = ['.png', '.jpg', '.jpeg', '.webp', '.bmp']
                vid_formats = ['.mp4', '.avi', '.mov', '.flv', '.mkv']
            
            files = []
            for f in Path(folder).rglob("*"):
                if f.suffix.lower() in img_formats + vid_formats:
                    files.append(str(f))
            
            for file_path in files:
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
            
            self._update_file_list()
    
    def _on_remove_selected(self):
        """移除选中的文件"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        
        # 获取选中的完整路径
        selected_paths = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        
        # 从列表中移除
        for path in selected_paths:
            if path in self.selected_files:
                self.selected_files.remove(path)
            # 移除对应的ROI记录
            if path in self.file_rois:
                del self.file_rois[path]
        
        self._update_file_list()
    
    def _on_clear_files(self):
        """清空文件列表"""
        if self.selected_files:
            reply = QMessageBox.question(
                self, "确认清空", 
                "确定要清空所有已选择的文件吗?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.selected_files = []
                self._update_file_list()
    
    def _on_file_double_clicked(self, item):
        """双击文件预览"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.file_preview.emit(file_path)
    
    def _on_preview_selected(self):
        """预览选中的文件"""
        selected_items = self.file_list.selectedItems()
        if selected_items:
            file_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.file_preview.emit(file_path)
    
    def _update_file_list(self):
        """更新文件列表显示"""
        self.file_list.clear()
        
        for f in self.selected_files:
            item = QListWidgetItem(Path(f).name)  # 显示文件名
            item.setData(Qt.ItemDataRole.UserRole, f)  # 存储完整路径
            item.setToolTip(f)  # 完整路径作为提示
            self.file_list.addItem(item)
        
        # 更新计数
        count = len(self.selected_files)
        self.lbl_file_count.setText(f"{count} 个文件")
        
        # 启用/禁用按钮
        has_files = count > 0
        self.btn_start.setEnabled(has_files)
        
        # 发送信号
        self.files_selected.emit(self.selected_files)
    
    def _on_selection_changed(self):
        """文件选择变化"""
        has_selection = len(self.file_list.selectedItems()) > 0
        self.btn_remove.setEnabled(has_selection)
        self.btn_preview.setEnabled(has_selection)
        
        # 发送选中的文件路径
        if has_selection:
            selected_item = self.file_list.selectedItems()[0]
            file_path = selected_item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.file_selection_changed.emit(file_path)
    
    def _on_start_clicked(self):
        """开始批量处理按钮点击"""
        if not self.selected_files:
            QMessageBox.warning(self, "警告", "请先选择要处理的文件")
            return
        
        config = self.get_batch_config()
        self.batch_start.emit(config)
    
    def get_batch_config(self) -> dict:
        """获取批量处理配置"""
        return {
            "files": self.selected_files,
            "same_roi": self.chk_same_roi.isChecked(),
            "max_workers": self.spin_workers.value(),
            "adaptive": self.chk_adaptive.isChecked(),
            "file_rois": self.file_rois  # 每个文件的ROI
        }
    
    def set_file_roi(self, file_path: str, roi: Optional[Tuple[int, int, int, int]]):
        """设置指定文件的ROI"""
        self.file_rois[file_path] = roi
    
    def get_file_roi(self, file_path: str) -> Optional[Tuple[int, int, int, int]]:
        """获取指定文件的ROI"""
        return self.file_rois.get(file_path)
    
    def clear_file_rois(self):
        """清空所有文件的ROI"""
        self.file_rois.clear()
    
    def set_progress(self, current: int, total: int, message: str = ""):
        """设置进度"""
        if total > 0:
            percent = int(current * 100 / total)
            self.progress.setValue(percent)
            self.lbl_status.setText(f"{current}/{total} {message}")
    
    def set_running(self, running: bool):
        """设置运行状态"""
        self.btn_start.setEnabled(not running and len(self.selected_files) > 0)
        self.btn_cancel.setEnabled(running)
        self.btn_add.setEnabled(not running)
        self.btn_remove.setEnabled(not running)
        self.btn_preview.setEnabled(not running)
        self.btn_clear.setEnabled(not running)
        self.progress.setVisible(running)
        self.lbl_status.setVisible(running)
        
        if running:
            self.lbl_status.setText("处理中...")
        else:
            self.lbl_status.setText("处理完成")
