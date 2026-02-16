# 水印去除工具

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)
[![Release](https://img.shields.io/github/v/release/yourusername/watermark-remover.svg)](https://github.com/yourusername/watermark-remover/releases)

基于OpenCV和PyQt6的本地离线水印去除工具，支持图片和视频批量处理。

## 功能特性

### 图像处理
- ✅ 支持PNG/JPG/JPEG/WebP/BMP格式
- ✅ OpenCV Inpainting算法（TELEA/NS）
- ✅ ROI区域选择和预览
- ✅ 批量处理
- ✅ 保持原始格式和质量

### 视频处理
- ✅ 支持MP4/AVI/MOV/FLV/MKV格式
- ✅ 逐帧去水印处理
- ✅ 保留原始音频轨道
- ✅ 进度实时显示
- ✅ 内存+磁盘混合缓存策略

### 界面功能
- ✅ 可视化ROI选择（鼠标拖动）
- ✅ 图像缩放和平移
- ✅ 实时进度反馈
- ✅ 日志显示
- ✅ 深色主题界面

## 技术栈

- **Python**: 3.10+
- **OpenCV-Python**: 图像/视频处理核心
- **PyQt6**: 图形用户界面
- **ffmpeg-python**: 视频编解码
- **Pillow**: 图像格式支持
- **numpy**: 数值计算
- **pyyaml**: 配置文件管理

## 安装依赖

```bash
pip install -r requirements.txt
```

### 依赖清单
- opencv-python>=4.8.0
- PyQt6>=6.4.0
- Pillow>=10.0.0
- numpy>=1.24.0
- pyyaml>=6.0.0
- ffmpeg-python>=0.2.0

## 运行程序

### 开发模式
```bash
python main.py
```

### 打包为EXE
```bash
pyinstaller build.spec
```

打包后的可执行文件位于 `dist/` 目录。

## 项目结构

```
watermark_remover/
├── main.py                    # 程序入口
├── config.yaml                # 配置文件
├── requirements.txt           # 依赖清单
├── build.spec                 # PyInstaller配置
├── README.md                  # 项目说明
│
├── assets/                    # 静态资源
│   ├── icons/                 # 图标
│   └── styles/                # QSS样式
│
├── core/                      # 核心算法层
│   ├── __init__.py
│   ├── image_processor.py     # 图像处理
│   ├── video_processor.py     # 视频处理
│   ├── watermark_detector.py  # 水印检测
│   └── cache_manager.py       # 缓存管理
│
├── services/                  # 业务逻辑层
│   ├── __init__.py
│   ├── task_scheduler.py      # 任务调度
│   ├── image_service.py       # 图像服务
│   └── video_service.py       # 视频服务
│
├── gui/                       # 界面层
│   ├── __init__.py
│   ├── main_window.py         # 主窗口
│   ├── components/            # UI组件
│   │   ├── image_viewer.py    # 图像预览
│   │   ├── watermark_selector.py
│   │   └── progress_dialog.py
│   └── threads/               # 工作线程
│       └── processing_thread.py
│
└── utils/                     # 工具层
    ├── __init__.py
    ├── exceptions.py          # 异常定义
    ├── config_loader.py       # 配置加载
    ├── logger.py              # 日志工具
    ├── file_utils.py          # 文件操作
    ├── image_utils.py         # 图像工具
    └── validators.py          # 验证器
```

## 架构说明

本项目采用四层模块化架构：

1. **工具层 (Utils)**: 基础设施，包括配置、日志、验证等
2. **核心算法层 (Core)**: OpenCV图像/视频处理核心算法
3. **业务逻辑层 (Services)**: 任务调度、服务封装
4. **界面层 (GUI)**: PyQt6用户界面

层间通过接口调用，禁止跨层硬编码，具备良好的可扩展性。

## 配置说明

编辑 `config.yaml` 可调整以下参数：

```yaml
processing:
  image:
    inpainting_radius: 3        # 修复半径
    algorithm: "telea"           # 修复算法
    quality: 95                  # 输出质量
  
  video:
    max_memory_frames: 100       # 最大内存缓存帧数
    codec: "libx264"             # 视频编码器
    crf: 18                      # 视频质量（越小越好）
    
  threading:
    max_workers: "auto"          # 线程数（auto=CPU核心数）

paths:
  temp_dir: "./temp"             # 临时文件目录
  output_dir: "./output"         # 默认输出目录
```

## 使用说明

### 图像去水印
1. 点击"选择图像"加载图片
2. 在图像上拖动鼠标选择水印区域
3. 调整参数（算法、半径、质量）
4. 点击"开始处理"

### 视频去水印
1. 点击"选择视频"加载视频
2. 在第一帧上选择水印区域
3. 点击"开始处理"
4. 等待处理完成（保留音频）

### ROI选择技巧
- 选择范围应略大于水印实际区域
- 对于复杂背景，可尝试调整"修复半径"
- TELEA算法适合大多数场景，NS算法适合纹理复杂的区域

## 性能优化

- **多线程**: 根据CPU核心数自动调整
- **内存缓存**: 小文件使用内存缓存
- **磁盘缓存**: 大文件自动切换到磁盘缓存
- **批量处理**: 支持多文件并行处理

## 注意事项

1. 首次运行前请安装所有依赖
2. 视频处理需要ffmpeg命令行工具
3. 处理大视频时确保磁盘空间充足
4. 建议定期清理 `./temp` 目录

## 常见问题

**Q: 视频处理报错 "ffmpeg not found"？**
A: 需要安装ffmpeg并添加到系统PATH。

**Q: 处理后的视频没有声音？**
A: 检查ffmpeg是否正确安装，音频编码参数是否正确。

**Q: 去水印效果不理想？**
A: 尝试调整修复半径或切换算法（TELEA/NS）。

**Q: 批量处理卡住？**
A: 减少同时处理的文件数量，或降低线程数配置。

## 许可证

MIT License

## 作者

OpenCode Assistant

## 更新日志

### v1.0 (2026-02-16)
- 初始版本发布
- 支持图像水印去除
- 支持视频水印去除
- 支持批量处理
- PyQt6图形界面
