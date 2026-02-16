"""
水印选择器组件
用于手动选择水印区域
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Tuple, Optional


class WatermarkSelector(QWidget):
    """
    水印选择器组件
    
    功能：
    - 手动输入ROI坐标
    - 显示当前选择的区域
    """
    
    # 信号
    roi_changed = pyqtSignal(int, int, int, int)  # x, y, w, h
    apply_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._roi: Optional[Tuple[int, int, int, int]] = None
        self._image_width = 0
        self._image_height = 0
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("水印区域")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # ROI输入组
        roi_group = QGroupBox("手动输入坐标")
        roi_layout = QVBoxLayout(roi_group)
        
        # X坐标
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X:"))
        self._spin_x = QSpinBox()
        self._spin_x.setRange(0, 99999)
        self._spin_x.setValue(0)
        self._spin_x.valueChanged.connect(self._on_value_changed)
        x_layout.addWidget(self._spin_x)
        roi_layout.addLayout(x_layout)
        
        # Y坐标
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y:"))
        self._spin_y = QSpinBox()
        self._spin_y.setRange(0, 99999)
        self._spin_y.setValue(0)
        self._spin_y.valueChanged.connect(self._on_value_changed)
        y_layout.addWidget(self._spin_y)
        roi_layout.addLayout(y_layout)
        
        # 宽度
        w_layout = QHBoxLayout()
        w_layout.addWidget(QLabel("宽度:"))
        self._spin_w = QSpinBox()
        self._spin_w.setRange(1, 99999)
        self._spin_w.setValue(100)
        self._spin_w.valueChanged.connect(self._on_value_changed)
        w_layout.addWidget(self._spin_w)
        roi_layout.addLayout(w_layout)
        
        # 高度
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("高度:"))
        self._spin_h = QSpinBox()
        self._spin_h.setRange(1, 99999)
        self._spin_h.setValue(100)
        self._spin_h.valueChanged.connect(self._on_value_changed)
        h_layout.addWidget(self._spin_h)
        roi_layout.addLayout(h_layout)
        
        layout.addWidget(roi_group)
        
        # 当前区域显示
        self._label_roi = QLabel("未选择区域")
        self._label_roi.setStyleSheet("color: #888888; padding: 5px;")
        layout.addWidget(self._label_roi)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        self._btn_apply = QPushButton("应用")
        self._btn_apply.setObjectName("primary_button")
        self._btn_apply.clicked.connect(self.apply_clicked.emit)
        button_layout.addWidget(self._btn_apply)
        
        self._btn_clear = QPushButton("清除")
        self._btn_clear.clicked.connect(self._on_clear)
        button_layout.addWidget(self._btn_clear)
        
        layout.addLayout(button_layout)
        
        # 提示文本
        hint = QLabel("提示：在图像上拖动鼠标可选择水印区域")
        hint.setStyleSheet("color: #666666; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        
        layout.addStretch()
    
    def set_image_size(self, width: int, height: int):
        """
        设置图像尺寸，用于限制ROI范围
        
        Args:
            width: 图像宽度
            height: 图像高度
        """
        self._image_width = width
        self._image_height = height
        
        # 更新spinbox范围
        self._spin_x.setRange(0, width - 1)
        self._spin_y.setRange(0, height - 1)
        self._spin_w.setRange(1, width)
        self._spin_h.setRange(1, height)
    
    def set_roi(self, x: int, y: int, w: int, h: int):
        """
        设置ROI值
        
        Args:
            x: X坐标
            y: Y坐标
            w: 宽度
            h: 高度
        """
        self._roi = (x, y, w, h)
        
        # 更新spinbox（不触发信号）
        self._spin_x.blockSignals(True)
        self._spin_y.blockSignals(True)
        self._spin_w.blockSignals(True)
        self._spin_h.blockSignals(True)
        
        self._spin_x.setValue(x)
        self._spin_y.setValue(y)
        self._spin_w.setValue(w)
        self._spin_h.setValue(h)
        
        self._spin_x.blockSignals(False)
        self._spin_y.blockSignals(False)
        self._spin_w.blockSignals(False)
        self._spin_h.blockSignals(False)
        
        # 更新显示
        self._update_roi_label()
    
    def get_roi(self) -> Optional[Tuple[int, int, int, int]]:
        """
        获取当前ROI
        
        Returns:
            (x, y, w, h) 或 None
        """
        if self._roi:
            return self._roi
        
        # 从spinbox获取
        return (
            self._spin_x.value(),
            self._spin_y.value(),
            self._spin_w.value(),
            self._spin_h.value()
        )
    
    def clear(self):
        """清除选择"""
        self._roi = None
        
        self._spin_x.setValue(0)
        self._spin_y.setValue(0)
        self._spin_w.setValue(100)
        self._spin_h.setValue(100)
        
        self._label_roi.setText("未选择区域")
        self._label_roi.setStyleSheet("color: #888888; padding: 5px;")
        
        self.clear_clicked.emit()
    
    def _on_value_changed(self):
        """值改变处理"""
        x = self._spin_x.value()
        y = self._spin_y.value()
        w = self._spin_w.value()
        h = self._spin_h.value()
        
        self._roi = (x, y, w, h)
        self._update_roi_label()
        self.roi_changed.emit(x, y, w, h)
    
    def _update_roi_label(self):
        """更新ROI标签显示"""
        if self._roi:
            x, y, w, h = self._roi
            self._label_roi.setText(f"区域: ({x}, {y}) {w}×{h}")
            self._label_roi.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
    
    def _on_clear(self):
        """清除按钮处理"""
        self.clear()
