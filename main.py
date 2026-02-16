#!/usr/bin/env python3
"""
水印去除工具 - 主入口

基于OpenCV和PyQt6的本地离线水印去除工具
"""

import sys
import os
import io
from pathlib import Path

# Windows 控制台编码设置
if sys.platform == 'win32':
    # 设置默认编码为 UTF-8
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 确保可以导入本地模块
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.main_window import MainWindow
from utils.logger import get_logger
from utils.config_loader import get_config

logger = get_logger()


def load_stylesheet(app: QApplication) -> str:
    """
    加载样式表
    
    Args:
        app: QApplication实例
        
    Returns:
        样式表内容
    """
    # 获取样式文件路径
    style_file = Path(__file__).parent / 'assets' / 'styles' / 'modern_style.qss'
    
    if style_file.exists():
        try:
            with open(style_file, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                app.setStyleSheet(stylesheet)
                logger.debug(f"加载样式表: {style_file}")
                return stylesheet
        except Exception as e:
            logger.warning(f"加载样式表失败: {e}")
    
    return ""


def setup_font(app: QApplication):
    """
    设置全局字体
    
    Args:
        app: QApplication实例
    """
    # 根据系统选择字体
    if sys.platform == 'win32':
        font_family = "Microsoft YaHei"
    elif sys.platform == 'darwin':
        font_family = "PingFang SC"
    else:
        font_family = "Noto Sans CJK SC"
    
    font = QFont(font_family, 10)
    app.setFont(font)


def main():
    """主函数"""
    # 启用高DPI支持
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName(get_config('ui.window_title', '水印去除工具'))
    app.setApplicationVersion("1.0")
    
    # 设置字体
    setup_font(app)
    
    # 加载样式表
    load_stylesheet(app)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    logger.info("应用程序启动")
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
