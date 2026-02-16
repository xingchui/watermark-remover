"""
进度对话框组件
显示处理进度
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal


class ProgressDialog(QDialog):
    """
    进度对话框
    
    功能：
    - 显示进度条
    - 显示日志信息
    - 支持取消操作
    """
    
    # 信号
    cancelled = pyqtSignal()
    
    def __init__(self, title: str = "处理中", parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        self._cancelled = False
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 标题
        self._label_title = QLabel("正在处理...")
        self._label_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self._label_title)
        
        # 状态标签
        self._label_status = QLabel("准备中...")
        self._label_status.setObjectName("status_label")
        layout.addWidget(self._label_status)
        
        # 进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)
        
        # 日志显示
        log_label = QLabel("处理日志:")
        layout.addWidget(log_label)
        
        self._text_log = QTextEdit()
        self._text_log.setObjectName("log_text")
        self._text_log.setReadOnly(True)
        self._text_log.setMaximumBlockCount(100)  # 限制最大行数
        layout.addWidget(self._text_log)
        
        # 按钮组
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self._btn_cancel = QPushButton("取消")
        self._btn_cancel.setObjectName("danger_button")
        self._btn_cancel.clicked.connect(self._on_cancel)
        button_layout.addWidget(self._btn_cancel)
        
        self._btn_close = QPushButton("关闭")
        self._btn_close.clicked.connect(self.close)
        self._btn_close.setVisible(False)
        button_layout.addWidget(self._btn_close)
        
        layout.addLayout(button_layout)
    
    def set_title(self, title: str):
        """
        设置标题
        
        Args:
            title: 标题文本
        """
        self._label_title.setText(title)
        self.setWindowTitle(title)
    
    def set_status(self, status: str):
        """
        设置状态文本
        
        Args:
            status: 状态文本
        """
        self._label_status.setText(status)
    
    def set_progress(self, value: int):
        """
        设置进度
        
        Args:
            value: 进度值 (0-100)
        """
        self._progress_bar.setValue(min(100, max(0, value)))
    
    def log(self, message: str):
        """
        添加日志
        
        Args:
            message: 日志消息
        """
        self._text_log.append(message)
        # 滚动到底部
        scrollbar = self._text_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def set_complete(self, success: bool = True):
        """
        设置完成状态
        
        Args:
            success: 是否成功
        """
        self._progress_bar.setValue(100)
        
        if success:
            self._label_status.setText("处理完成")
            self._label_status.setProperty("status", "success")
            self.log("✓ 处理完成")
        else:
            self._label_status.setText("处理失败")
            self._label_status.setProperty("status", "error")
        
        # 更新按钮
        self._btn_cancel.setVisible(False)
        self._btn_close.setVisible(True)
    
    def is_cancelled(self) -> bool:
        """
        检查是否已取消
        
        Returns:
            是否已取消
        """
        return self._cancelled
    
    def _on_cancel(self):
        """取消按钮处理"""
        self._cancelled = True
        self._label_status.setText("正在取消...")
        self.log("用户取消操作")
        self._btn_cancel.setEnabled(False)
        self.cancelled.emit()
    
    def closeEvent(self, event):
        """关闭事件处理"""
        if not self._cancelled and self._progress_bar.value() < 100:
            # 如果还在处理中，先取消
            self._on_cancel()
            event.ignore()
        else:
            event.accept()
