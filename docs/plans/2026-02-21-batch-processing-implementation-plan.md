# 批量处理功能实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 GUI 中添加批量处理功能，支持多文件和文件夹模式批量处理图像/视频去水印

**Architecture:** 
- 在现有 GUI 主窗口添加批量处理面板
- 使用已有的 batch_executor.py 实现批量处理逻辑
- 添加批量处理专用线程处理进度更新

**Tech Stack:** Python, PyQt6, OpenCV, concurrent.futures

---

### Task 1: 创建批量处理面板组件

**Files:**
- Create: `gui/components/batch_panel.py`
- Modify: `gui/components/__init__.py`

**Step 1: 创建 batch_panel.py**

```python
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QProgressBar, QCheckBox, 
                             QSpinBox, QGroupBox, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

class BatchPanel(QWidget):
    """批量处理面板"""
    
    files_selected = pyqtSignal(list)  # 文件列表信号
    batch_start = pyqtSignal(dict)    # 开始批量处理信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.selected_files = []
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 文件选择按钮组
        btn_group = QGroupBox("文件选择模式")
        btn_layout = QHBoxLayout()
        
        self.btn_single = QPushButton("单文件")
        self.btn_batch = QPushButton("批量文件")
        self.btn_folder = QPushButton("文件夹")
        
        self.btn_single.setCheckable(True)
        self.btn_batch.setCheckable(True)
        self.btn_folder.setCheckable(True)
        self.btn_single.setChecked(True)
        
        btn_layout.addWidget(self.btn_single)
        btn_layout.addWidget(self.btn_batch)
        btn_layout.addWidget(self.btn_folder)
        btn_group.setLayout(btn_layout)
        layout.addWidget(btn_group)
        
        # 已选择文件列表
        self.file_list = QListWidget()
        layout.addWidget(QLabel("已选择文件:"))
        layout.addWidget(self.file_list)
        
        # 批量处理设置
        settings_group = QGroupBox("批量处理设置")
        settings_layout = QVBoxLayout()
        
        self.chk_same_roi = QCheckBox("使用同一ROI处理所有文件")
        self.chk_same_roi.setChecked(True)
        settings_layout.addWidget(self.chk_same_roi)
        
        workers_layout = QHBoxLayout()
        workers_layout.addWidget(QLabel("并发数:"))
        self.spin_workers = QSpinBox()
        self.spin_workers.setRange(1, 16)
        self.spin_workers.setValue(4)
        workers_layout.addWidget(self.spin_workers)
        settings_layout.addLayout(workers_layout)
        
        self.chk_adaptive = QCheckBox("自适应调度")
        self.chk_adaptive.setChecked(True)
        settings_layout.addWidget(self.chk_adaptive)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setVisible(False)
        layout.addWidget(self.lbl_status)
        
        # 开始/取消按钮
        btn_layout2 = QHBoxLayout()
        self.btn_start = QPushButton("开始批量处理")
        self.btn_start.setEnabled(False)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setEnabled(False)
        btn_layout2.addWidget(self.btn_start)
        btn_layout2.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout2)
        
        # 信号连接
        self.btn_single.clicked.connect(lambda: self._set_mode("single"))
        self.btn_batch.clicked.connect(lambda: self._set_mode("batch"))
        self.btn_folder.clicked.connect(lambda: self._set_mode("folder"))
        
    def _set_mode(self, mode):
        """设置选择模式"""
        self.btn_single.setChecked(mode == "single")
        self.btn_batch.setChecked(mode == "batch")
        self.btn_folder.setChecked(mode == "folder")
        
        if mode == "single":
            self._select_single_file()
        elif mode == "batch":
            self._select_multiple_files()
        elif mode == "folder":
            self._select_folder()
    
    def _select_single_file(self):
        """选择单个文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图像", "",
            "图像文件 (*.png *.jpg *.jpeg *.webp *.bmp);;视频文件 (*.mp4 *.avi *.mov *.flv *.mkv)"
        )
        if file_path:
            self.selected_files = [file_path]
            self._update_file_list()
    
    def _select_multiple_files(self):
        """选择多个文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择多个图像", "",
            "图像文件 (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if files:
            self.selected_files = files
            self._update_file_list()
    
    def _select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            from pathlib import Path
            from utils import get_supported_image_formats, get_supported_video_formats
            
            img_formats = get_supported_image_formats()
            vid_formats = get_supported_video_formats()
            
            files = []
            for f in Path(folder).rglob("*"):
                if f.suffix.lower() in img_formats + vid_formats:
                    files.append(str(f))
            
            self.selected_files = files
            self._update_file_list()
    
    def _update_file_list(self):
        """更新文件列表显示"""
        self.file_list.clear()
        for f in self.selected_files:
            self.file_list.addItem(f)
        self.btn_start.setEnabled(len(self.selected_files) > 0)
        self.files_selected.emit(self.selected_files)
    
    def get_batch_config(self) -> dict:
        """获取批量处理配置"""
        return {
            "files": self.selected_files,
            "same_roi": self.chk_same_roi.isChecked(),
            "max_workers": self.spin_workers.value(),
            "adaptive": self.chk_adaptive.isChecked()
        }
    
    def set_progress(self, current: int, total: int, message: str = ""):
        """设置进度"""
        if total > 0:
            self.progress.setValue(int(current * 100 / total))
            self.lbl_status.setText(f"{current}/{total} {message}")
    
    def set_running(self, running: bool):
        """设置运行状态"""
        self.btn_start.setEnabled(not running and len(self.selected_files) > 0)
        self.btn_cancel.setEnabled(running)
        self.progress.setVisible(running)
        self.lbl_status.setVisible(running)
```

**Step 2: 更新 components/__init__.py**

```python
from .batch_panel import BatchPanel
from .image_viewer import ImageViewer
from .watermark_selector import WatermarkSelector
from .progress_dialog import ProgressDialog
from .help_dialog import HelpDialog

__all__ = [
    'BatchPanel',
    'ImageViewer',
    'WatermarkSelector',
    'ProgressDialog',
    'HelpDialog',
]
```

**Step 3: 提交**

```bash
git add gui/components/batch_panel.py gui/components/__init__.py
git commit -m "feat(gui): add BatchPanel component for batch processing"
```

---

### Task 2: 修改主窗口集成批量面板

**Files:**
- Modify: `gui/main_window.py:1-50`

**Step 1: 添加导入**

```python
from gui.components import BatchPanel
```

**Step 2: 在 MainWindow.__init__ 中添加批量面板**

在初始化UI后添加（大约在第60行左右）:

```python
# 批量处理面板
self._batch_panel = BatchPanel()
self._batch_panel.files_selected.connect(self._on_batch_files_selected)
self._batch_panel.batch_start.connect(self._on_batch_start)
left_layout.addWidget(self._batch_panel)
```

**Step 3: 添加信号处理方法**

```python
def _on_batch_files_selected(self, files: list):
    """批量文件选择处理"""
    if files:
        self._log(f"已选择 {len(files)} 个文件")

def _on_batch_start(self, config: dict):
    """开始批量处理"""
    # TODO: 实现批量处理逻辑
    pass
```

**Step 4: 提交**

```bash
git add gui/main_window.py
git commit -m "feat(gui): integrate BatchPanel into MainWindow"
```

---

### Task 3: 实现批量处理逻辑

**Files:**
- Modify: `gui/main_window.py`

**Step 1: 实现批量处理方法**

在 MainWindow 类中添加:

```python
def _on_batch_start(self, config: dict):
    """开始批量处理"""
    files = config.get("files", [])
    if not files:
        return
    
    roi = self._watermark_selector.get_roi()
    if not roi:
        QMessageBox.warning(self, "警告", "请先选择水印区域")
        return
    
    # 获取处理参数
    algorithm = self._combo_algorithm.currentText()
    radius = self._spin_radius.value()
    quality = self._spin_quality.value()
    max_workers = config.get("max_workers", 4)
    adaptive = config.get("adaptive", True)
    
    # 设置进度
    self._batch_panel.set_running(True)
    self._batch_panel.set_progress(0, len(files), "准备中...")
    
    # 使用线程处理
    from gui.threads import BatchProcessingThread
    self._batch_thread = BatchProcessingThread(
        files, roi, algorithm, radius, quality, max_workers, adaptive,
        self._current_file_type
    )
    self._batch_thread.progress.connect(self._on_batch_progress)
    self._batch_thread.finished.connect(self._on_batch_finished)
    self._batch_thread.error.connect(self._on_batch_error)
    self._batch_thread.start()
    
    self._log(f"开始批量处理: {len(files)} 个文件")

def _on_batch_progress(self, current: int, total: int, filename: str):
    """批量处理进度"""
    self._batch_panel.set_progress(current, total, filename)
    self._status_bar.showMessage(f"处理中: {filename}")

def _on_batch_finished(self, success: int, failed: int, output_dir: str):
    """批量处理完成"""
    self._batch_panel.set_running(False)
    self._log(f"批量处理完成: 成功 {success}, 失败 {failed}")
    QMessageBox.information(
        self, "完成", 
        f"批量处理完成!\n成功: {success}\n失败: {failed}\n输出目录: {output_dir}"
    )

def _on_batch_error(self, error: str):
    """批量处理错误"""
    self._batch_panel.set_running(False)
    self._log(f"批量处理错误: {error}")
    QMessageBox.critical(self, "错误", f"批量处理出错:\n{error}")
```

**Step 2: 提交**

```bash
git add gui/main_window.py
git commit -m "feat(gui): implement batch processing logic in MainWindow"
```

---

### Task 4: 创建批量处理线程

**Files:**
- Create: `gui/threads/batch_processing_thread.py`
- Modify: `gui/threads/__init__.py`

**Step 1: 创建线程类**

```python
from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
from services import ImageService, VideoService

class BatchProcessingThread(QThread):
    """批量处理线程"""
    
    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(int, int, str)   # success, failed, output_dir
    error = pyqtSignal(str)                # error message
    
    def __init__(self, files, roi, algorithm, radius, quality, max_workers, adaptive, file_type):
        super().__init__()
        self.files = files
        self.roi = roi
        self.algorithm = algorithm
        self.radius = radius
        self.quality = quality
        self.max_workers = max_workers
        self.adaptive = adaptive
        self.file_type = file_type  # 'image' or 'video'
    
    def run(self):
        try:
            if self.file_type == 'image':
                self._process_images()
            else:
                self._process_videos()
        except Exception as e:
            self.error.emit(str(e))
    
    def _process_images(self):
        """批量处理图像"""
        from utils import get_config
        output_dir = get_config('paths.output_dir', './output')
        
        svc = ImageService(output_dir=output_dir)
        
        success = 0
        failed = 0
        
        for i, file_path in enumerate(self.files):
            filename = Path(file_path).name
            self.progress.emit(i + 1, len(self.files), filename)
            
            try:
                svc.process(
                    file_path, self.roi, None,
                    self.algorithm, self.radius, self.quality
                )
                success += 1
            except Exception:
                failed += 1
        
        self.finished.emit(success, failed, output_dir)
    
    def _process_videos(self):
        """批量处理视频"""
        from utils import get_config
        output_dir = get_config('paths.output_dir', './output')
        
        svc = VideoService(output_dir=output_dir)
        
        success = 0
        failed = 0
        
        for i, file_path in enumerate(self.files):
            filename = Path(file_path).name
            self.progress.emit(i + 1, len(self.files), filename)
            
            try:
                svc.process(
                    file_path, self.roi, None,
                    self.algorithm, self.radius
                )
                success += 1
            except Exception:
                failed += 1
        
        self.finished.emit(success, failed, output_dir)
```

**Step 2: 更新 __init__.py**

```python
from .processing_thread import ProcessingThread
from .batch_processing_thread import BatchProcessingThread

__all__ = ['ProcessingThread', 'BatchProcessingThread']
```

**Step 3: 提交**

```bash
git add gui/threads/batch_processing_thread.py gui/threads/__init__.py
git commit -m "feat(gui): add BatchProcessingThread for batch processing"
```

---

### Task 5: 测试批量处理功能

**Step 1: 运行程序测试**

```bash
python main.py
```

**Step 2: 测试场景**

1. 点击"批量文件"按钮，选择多个图片
2. 选择 ROI 区域
3. 设置并发数和自适应选项
4. 点击"开始批量处理"
5. 观察进度条和日志

**Step 3: 提交**

```bash
git add .
git commit -m "test: verify batch processing functionality"
```

---

## 执行选项

**计划完成并保存到 `docs/plans/2026-02-21-batch-processing-design.md`。两种执行方式：**

1. **Subagent-Driven (本会话)** - 每个任务派发新的子代理，任务间审核，快速迭代

2. **Parallel Session (单独会话)** - 在新会话中使用 executing-plans，批量执行并设置检查点

**选择哪种方式？**
