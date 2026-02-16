"""
图像预览组件
提供图像显示、缩放、拖拽和ROI选择功能
"""

from typing import Optional

import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QMouseEvent, QWheelEvent


class ImageViewer(QWidget):
    """
    图像预览组件
    
    功能：
    - 图像显示
    - 鼠标滚轮缩放
    - 拖拽平移
    - ROI矩形选择（信号通知）
    """
    
    # 信号定义
    roi_selected = pyqtSignal(int, int, int, int)  # x, y, width, height
    roi_changed = pyqtSignal(int, int, int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 图像数据
        self._original_image: Optional[np.ndarray] = None
        self._display_image: Optional[np.ndarray] = None
        self._qimage: Optional[QImage] = None
        self._pixmap: Optional[QPixmap] = None
        
        # 显示参数
        self._scale = 1.0
        self._offset = QPoint(0, 0)
        self._min_scale = 0.1
        self._max_scale = 10.0
        self._display_ratio = 1.0  # 自动适应Label的比例
        self._display_offset_x = 0  # 图像在Label中的X偏移
        self._display_offset_y = 0  # 图像在Label中的Y偏移
        
        # ROI选择
        self._roi_start: Optional[QPoint] = None
        self._roi_end: Optional[QPoint] = None
        self._is_selecting = False
        self._selection_enabled = True
        self._roi_rect: Optional[QRect] = None

        # 拖拽
        self._is_dragging = False
        self._drag_start: Optional[QPoint] = None
        
        # UI
        self._init_ui()
        
        # 设置鼠标跟踪
        self.setMouseTracking(True)
    
    def _init_ui(self):
        """初始化UI"""
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 创建标签用于显示图像
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("background-color: #2b2b2b;")
        # 让QLabel将鼠标事件传递给父组件
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # 布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
    
    def set_image(self, image: np.ndarray):
        """
        设置显示的图像
        
        Args:
            image: OpenCV格式图像(BGR)或numpy数组
        """
        if image is None:
            return
        
        self._original_image = image.copy()
        self._display_image = image.copy()
        self._scale = 1.0
        self._offset = QPoint(0, 0)
        
        self._update_display()
    
    def set_roi(self, x: int, y: int, w: int, h: int):
        """设置ROI区域"""
        self._roi_rect = QRect(x, y, w, h)
        self._update_display()
    
    def clear_roi(self):
        """清除ROI区域"""
        self._roi_rect = None
        self._update_display()
    
    def get_roi(self) -> tuple:
        """获取ROI区域坐标"""
        if self._roi_rect:
            return (self._roi_rect.x(), self._roi_rect.y(),
                   self._roi_rect.width(), self._roi_rect.height())
        return None
    
    def enable_selection(self, enabled: bool = True):
        """启用/禁用选择模式"""
        self._selection_enabled = enabled
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def _update_display(self):
        """更新显示"""
        if self._original_image is None:
            return
        
        # 绘制ROI框
        display_img = self._display_image.copy()
        if self._roi_rect:
            cv2.rectangle(
                display_img,
                (self._roi_rect.x(), self._roi_rect.y()),
                (self._roi_rect.x() + self._roi_rect.width(),
                 self._roi_rect.y() + self._roi_rect.height()),
                (0, 255, 0), 2
            )
        
        # 转换为QImage - 使用安全的方法避免内存问题
        height, width = display_img.shape[:2]
        try:
            if len(display_img.shape) == 3:
                # BGR转RGB
                rgb_image = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
                # 创建连续内存的副本
                rgb_image = np.ascontiguousarray(rgb_image)
                # 使用copy方法创建QImage，避免引用原始numpy数组
                self._qimage = QImage(
                    rgb_image.data, width, height, 
                    3 * width, QImage.Format.Format_RGB888
                ).copy()
                # 显式保存numpy数组的引用，防止垃圾回收
                self._qimage._numpy_ref = rgb_image
            else:
                # 灰度图
                display_img = np.ascontiguousarray(display_img)
                self._qimage = QImage(
                    display_img.data, width, height, 
                    width, QImage.Format.Format_Grayscale8
                ).copy()
                self._qimage._numpy_ref = display_img
        except Exception as e:
            import logging
            logging.error(f"创建QImage失败: {e}")
            return
        
        if self._qimage.isNull():
            import logging
            logging.error("QImage创建失败，图像数据无效")
            return
        
        # 缩放
        scaled_width = int(width * self._scale)
        scaled_height = int(height * self._scale)
        scaled_pixmap = QPixmap.fromImage(self._qimage).scaled(
            scaled_width, scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # 计算实际显示比例 = 最终pixmap宽度 / 原始图像宽度
        self._display_ratio = scaled_pixmap.width() / width if width > 0 else 1.0
        
        # 计算偏移量（图像在Label中的位置）
        label_size = self._label.size()
        self._display_offset_x = (label_size.width() - scaled_pixmap.width()) // 2
        self._display_offset_y = (label_size.height() - scaled_pixmap.height()) // 2
        
        self._label.setPixmap(scaled_pixmap)
    
    def wheelEvent(self, event: QWheelEvent):
        """鼠标滚轮事件 - 缩放"""
        if self._original_image is None:
            return
        
        # 计算缩放因子
        delta = event.angleDelta().y()
        scale_factor = 1.1 if delta > 0 else 0.9
        
        new_scale = self._scale * scale_factor
        if self._min_scale <= new_scale <= self._max_scale:
            self._scale = new_scale
            self._update_display()

    def _get_display_transform(self):
        """获取显示变换参数"""
        if self._original_image is None:
            return {'scale': 1.0, 'offset_x': 0, 'offset_y': 0, 'pixmap_ratio': 1.0}
        
        height, width = self._original_image.shape[:2]
        
        # 初始缩放
        scaled_w = int(width * self._scale)
        scaled_h = int(height * self._scale)
        
        # 计算适配label的比例
        label_w = max(1, self._label.width())
        label_h = max(1, self._label.height())
        pixmap_ratio = min(label_w / scaled_w, label_h / scaled_h) if scaled_w > 0 and scaled_h > 0 else 1.0
        
        # 最终显示尺寸
        final_w = int(scaled_w * pixmap_ratio)
        final_h = int(scaled_h * pixmap_ratio)
        
        # 在label中的偏移
        offset_x = (label_w - final_w) // 2
        offset_y = (label_h - final_h) // 2
        
        # 总缩放比例
        total_scale = self._scale * pixmap_ratio
        
        return {
            'scale': total_scale,
            'offset_x': offset_x,
            'offset_y': offset_y,
            'pixmap_ratio': pixmap_ratio
        }    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._selection_enabled and self._original_image is not None:
                # 开始ROI选择
                self._roi_start = event.pos()
                self._roi_end = event.pos()
                self._is_selecting = True
                self.setCursor(Qt.CursorShape.CrossCursor)
            elif self._original_image is not None:
                # 开始拖拽
                self._is_dragging = True
                self._drag_start = event.pos()
                self.setCursor(Qt.CursorShape.OpenHandCursor)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        if self._is_selecting and self._roi_start:
            self._roi_end = event.pos()
            # 实时更新显示
            self._draw_selection_box()
        elif self._is_dragging:
            # 处理拖拽
            delta = event.pos() - self._drag_start
            self._offset += delta
            self._drag_start = event.pos()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_selecting:
                self._is_selecting = False
                self._roi_end = event.pos()
                self.setCursor(Qt.CursorShape.ArrowCursor)
                
                # 使用统一的变换计算
                transform = self._get_display_transform()
                
                # 减去偏移量得到在pixmap中的坐标
                x1 = min(self._roi_start.x(), self._roi_end.x()) - transform['offset_x']
                y1 = min(self._roi_start.y(), self._roi_end.y()) - transform['offset_y']
                x2 = max(self._roi_start.x(), self._roi_end.x()) - transform['offset_x']
                y2 = max(self._roi_start.y(), self._roi_end.y()) - transform['offset_y']
                
                # 确保最小选择区域（10像素）
                if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
                    self._roi_start = None
                    self._roi_end = None
                    self._update_display()
                    return
                
                # 转换为图像坐标
                total_scale = transform['scale']
                if total_scale > 0:
                    img_x = int(x1 / total_scale)
                    img_y = int(y1 / total_scale)
                    img_w = int((x2 - x1) / total_scale)
                    img_h = int((y2 - y1) / total_scale)
                else:
                    img_x = img_y = img_w = img_h = 0
                
                # 确保在图像范围内
                img_h_full, img_w_full = self._original_image.shape[:2]
                img_x = max(0, min(img_x, img_w_full))
                img_y = max(0, min(img_y, img_h_full))
                img_w = min(img_w, img_w_full - img_x)
                img_h = min(img_h, img_h_full - img_y)
                
                if img_w > 0 and img_h > 0:
                    self._roi_rect = QRect(img_x, img_y, img_w, img_h)
                    self.roi_selected.emit(img_x, img_y, img_w, img_h)
                
                self._roi_start = None
                self._roi_end = None
                self._update_display()
                
            elif self._is_dragging:
                self._is_dragging = False
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def _draw_selection_box(self):
        """绘制选择框"""
        if self._original_image is None or not self._is_selecting:
            return
        
        if self._roi_start is None or self._roi_end is None:
            return
        
        # 使用统一的变换计算
        transform = self._get_display_transform()
        
        # 减去偏移量得到在pixmap中的坐标
        x1 = min(self._roi_start.x(), self._roi_end.x()) - transform['offset_x']
        y1 = min(self._roi_start.y(), self._roi_end.y()) - transform['offset_y']
        x2 = max(self._roi_start.x(), self._roi_end.x()) - transform['offset_x']
        y2 = max(self._roi_start.y(), self._roi_end.y()) - transform['offset_y']
        
        # 转换到图像坐标
        total_scale = transform['scale']
        if total_scale > 0:
            img_x1 = int(x1 / total_scale)
            img_y1 = int(y1 / total_scale)
            img_x2 = int(x2 / total_scale)
            img_y2 = int(y2 / total_scale)
        else:
            img_x1 = img_y1 = img_x2 = img_y2 = 0
        
        # 复制显示图像
        temp_img = self._display_image.copy()
        height, width = temp_img.shape[:2]
        
        # 限制范围
        img_x1 = max(0, min(img_x1, width - 1))
        img_y1 = max(0, min(img_y1, height - 1))
        img_x2 = max(0, min(img_x2, width))
        img_y2 = max(0, min(img_y2, height))
        
        if img_x2 > img_x1 and img_y2 > img_y1:
            cv2.rectangle(temp_img, (img_x1, img_y1), (img_x2, img_y2), (255, 0, 0), 2)
        
        # 转换为 QImage - 使用安全方法
        rgb = cv2.cvtColor(temp_img, cv2.COLOR_BGR2RGB)
        rgb = np.ascontiguousarray(rgb)
        qimage = QImage(rgb.data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
        qimage._numpy_ref = rgb
        
        # 使用与_update_display相同的计算方式
        scaled_w = int(width * self._scale)
        scaled_h = int(height * self._scale)
        
        # 计算适配label的比例
        label_w = max(1, self._label.width())
        label_h = max(1, self._label.height())
        ratio = min(label_w / scaled_w, label_h / scaled_h) if scaled_w > 0 and scaled_h > 0 else 1.0
        scaled_w = int(scaled_w * ratio)
        scaled_h = int(scaled_h * ratio)
        
        pixmap = QPixmap.fromImage(qimage).scaled(
            scaled_w, scaled_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self._label.setPixmap(pixmap)

    def reset_view(self):
        """重置视图"""
        self._scale = 1.0
        self._offset = QPoint(0, 0)
        self._update_display()

    def clear(self):
        """清除显示"""
        self._original_image = None
        self._display_image = None
        self._pixmap = None
        self._label.clear()
        self._roi_rect = None
