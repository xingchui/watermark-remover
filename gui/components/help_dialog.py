"""
帮助对话框模块
提供应用使用帮助文档
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser,
    QPushButton, QLabel, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class HelpDialog(QDialog):
    """帮助对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用帮助")
        self.setMinimumSize(700, 600)
        self.resize(800, 650)

        # 设置对话框整体样式：浅色背景
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)

        self._init_ui()
        self._load_content()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("水印去除工具 - 使用帮助")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 帮助内容浏览器
        self._content_browser = QTextBrowser()
        self._content_browser.setOpenExternalLinks(True)

        # 设置样式：白色背景，深色文字，大字体
        self._content_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                color: #333333;
                font-size: 14px;
                border: 1px solid #cccccc;
                border-radius: 6px;
                padding: 10px;
            }
            QTextBrowser QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QTextBrowser QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 30px;
            }
            QTextBrowser QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)

        layout.addWidget(self._content_browser)
        
        # 关闭按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_content(self):
        """加载帮助内容"""
        help_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
                    font-size: 15px;
                    line-height: 1.8;
                    color: #333333;
                    background-color: #ffffff;
                    padding: 15px;
                }
                h1 {
                    color: #2c3e50;
                    font-size: 26px;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 12px;
                    margin-top: 30px;
                }
                h2 {
                    color: #34495e;
                    font-size: 20px;
                    margin-top: 25px;
                    margin-bottom: 15px;
                    padding-left: 12px;
                    border-left: 5px solid #3498db;
                }
                h3 {
                    color: #555;
                    font-size: 17px;
                    margin-top: 20px;
                }
                .tip {
                    background-color: #e8f6ff;
                    border-left: 5px solid #3498db;
                    padding: 15px 18px;
                    margin: 18px 0;
                    border-radius: 6px;
                    font-size: 15px;
                }
                .warning {
                    background-color: #fff3cd;
                    border-left: 5px solid #ffc107;
                    padding: 15px 18px;
                    margin: 18px 0;
                    border-radius: 6px;
                    font-size: 15px;
                }
                .step {
                    background-color: #f8f9fa;
                    padding: 18px;
                    margin: 12px 0;
                    border-radius: 10px;
                    border: 1px solid #dee2e6;
                    font-size: 15px;
                }
                .step-number {
                    display: inline-block;
                    width: 32px;
                    height: 32px;
                    background-color: #3498db;
                    color: white;
                    text-align: center;
                    line-height: 32px;
                    border-radius: 50%;
                    font-size: 16px;
                    font-weight: bold;
                    margin-right: 12px;
                }
                ul, ol {
                    padding-left: 30px;
                    font-size: 15px;
                }
                li {
                    margin: 10px 0;
                    line-height: 1.6;
                }
                code {
                    background-color: #f4f4f4;
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-family: Consolas, monospace;
                    font-size: 14px;
                    color: #e83e8c;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 18px 0;
                    font-size: 15px;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                    font-size: 15px;
                }
                td {
                    line-height: 1.6;
                }
                .feature-box {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 25px;
                    border-radius: 12px;
                    margin: 25px 0;
                    font-size: 16px;
                }
                p {
                    font-size: 15px;
                    line-height: 1.8;
                    margin: 12px 0;
                }
                strong {
                    font-weight: bold;
                    color: #2c3e50;
                    font-size: 15px;
                }
            </style>
        </head>
        <body>
            <div class="feature-box">
                <h1 style="color: white; border: none; margin: 0; padding: 0;">📖 欢迎使用水印去除工具</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">本工具基于 OpenCV 和 PyQt6 开发，支持图像和视频的批量水印去除。</p>
            </div>

            <h1>🚀 快速开始</h1>
            
            <h2>图像去水印</h2>
            <div class="step">
                <span class="step-number">1</span><strong>选择图像</strong>
                <p>点击左侧"选择图像"按钮，支持 PNG、JPG、JPEG、WebP、BMP 格式。</p>
            </div>
            <div class="step">
                <span class="step-number">2</span><strong>选择水印区域</strong>
                <p>在右侧预览区按住鼠标左键拖动，框选水印位置。选中的区域会用绿色边框显示。</p>
            </div>
            <div class="step">
                <span class="step-number">3</span><strong>调整参数</strong>
                <ul>
                    <li><strong>修复算法：</strong>TELEA（快速，适合简单背景）、NS（纹理保持，适合复杂背景）、高级修复（质量最佳）</li>
                    <li><strong>修复半径：</strong>建议 3-5 像素，范围越大修复范围越广</li>
                    <li><strong>输出质量：</strong>JPEG 输出质量（1-100），建议 95</li>
                </ul>
            </div>
            <div class="step">
                <span class="step-number">4</span><strong>开始处理</strong>
                <p>点击"开始处理"按钮，处理完成后会自动保存到 output 目录。</p>
            </div>

            <h2>视频去水印</h2>
            <div class="step">
                <span class="step-number">1</span><strong>选择视频</strong>
                <p>点击"选择视频"按钮，支持 MP4、AVI、MOV、FLV、MKV 格式。</p>
            </div>
            <div class="step">
                <span class="step-number">2</span><strong>选择水印区域</strong>
                <p>视频的第一帧会显示在预览区，同样拖动鼠标选择水印位置。</p>
            </div>
            <div class="step">
                <span class="step-number">3</span><strong>开始处理</strong>
                <p>点击"开始处理"，程序会逐帧处理并保留原始音频。处理时间较长，请耐心等待。</p>
            </div>

            <h1>🎛️ 参数说明</h1>
            
            <table>
                <tr>
                    <th>参数</th>
                    <th>说明</th>
                    <th>推荐值</th>
                </tr>
                <tr>
                    <td>修复算法</td>
                    <td>TELEA: 快速修复，适合纯色背景<br>NS: 纹理合成，适合复杂背景<br>高级修复: 多算法融合，质量最佳</td>
                    <td>高级修复</td>
                </tr>
                <tr>
                    <td>修复半径</td>
                    <td>修复区域边缘扩展的像素数</td>
                    <td>3-5</td>
                </tr>
                <tr>
                    <td>输出质量</td>
                    <td>JPEG 压缩质量（仅影响 JPG 输出）</td>
                    <td>95</td>
                </tr>
                <tr>
                    <td>AI 设备</td>
                    <td>使用 CPU 或 CUDA GPU 加速（需要支持）</td>
                    <td>CPU</td>
                </tr>
            </table>

            <h1>💡 使用技巧</h1>
            
            <div class="tip">
                <strong>✨ 选择区域技巧</strong><br>
                选择范围应略大于水印实际区域（多预留 5-10 像素），这样修复效果更自然，边缘过渡更平滑。
            </div>
            
            <div class="tip">
                <strong>🔍 预览功能</strong><br>
                处理前点击"预览效果"可以查看修复后的效果，不满意可以调整参数重新预览。
            </div>
            
            <div class="tip">
                <strong>⚡ 批量处理</strong><br>
                支持选择多个文件进行批量处理，适合处理同一位置有水印的图片序列或视频片段。
            </div>

            <h1>⚠️ 注意事项</h1>
            
            <div class="warning">
                <strong>🎬 视频处理依赖</strong><br>
                视频处理需要系统中安装 ffmpeg 并添加到 PATH 环境变量。如未安装，请访问 https://ffmpeg.org/download.html 下载。
            </div>
            
            <div class="warning">
                <strong>💾 磁盘空间</strong><br>
                处理大视频时会生成临时文件，请确保磁盘有足够空间（建议预留视频大小的 2-3 倍）。
            </div>
            
            <div class="warning">
                <strong>🖼️ 复杂水印</strong><br>
                对于覆盖重要画面内容或半透明的大型水印，自动修复效果可能不理想，建议结合其他图像编辑软件使用。
            </div>

            <h1>🐛 常见问题</h1>
            
            <h3>Q: 处理后的图片质量下降了？</h3>
            <p>A: 如果是 JPEG 格式，提高"输出质量"参数到 95-100。或选择 PNG 格式输出（无损）。</p>
            
            <h3>Q: 去水印后背景有明显痕迹？</h3>
            <p>A: 尝试以下方法：<br>
            1. 增大修复半径（5-10）<br>
            2. 切换修复算法（NS 算法通常纹理保持更好）<br>
            3. 确保选择区域比水印大一圈</p>
            
            <h3>Q: 视频处理报 "ffmpeg not found" 错误？</h3>
            <p>A: 需要安装 ffmpeg：<br>
            1. Windows: 下载 ffmpeg，将 bin 目录添加到系统 PATH<br>
            2. macOS: <code>brew install ffmpeg</code><br>
            3. Linux: <code>sudo apt install ffmpeg</code></p>
            
            <h3>Q: 处理后的视频没有声音？</h3>
            <p>A: 检查 ffmpeg 是否正确安装，或尝试重新安装 ffmpeg。</p>
            
            <h3>Q: 批量处理时程序卡死？</h3>
            <p>A: 减少同时处理的文件数量，或在 config.yaml 中降低 max_workers 线程数。</p>

            <h1>📁 文件说明</h1>
            
            <ul>
                <li><strong>config.yaml</strong> - 配置文件，可调整处理参数和路径</li>
                <li><strong>output/</strong> - 默认输出目录</li>
                <li><strong>temp/</strong> - 临时文件目录（程序退出时可自动清理）</li>
                <li><strong>logs/</strong> - 日志文件目录</li>
            </ul>

            <h1>📞 技术支持</h1>
            
            <p>如有问题或建议，欢迎反馈。</p>
            
            <div class="tip" style="margin-top: 30px;">
                <strong>版本信息</strong><br>
                水印去除工具 v1.0<br>
                基于 OpenCV + PyQt6 构建
            </div>
        </body>
        </html>
        """
        self._content_browser.setHtml(help_html)
