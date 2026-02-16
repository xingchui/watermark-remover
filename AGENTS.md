# AGENTS.md - AI Coding Assistant Guidelines

## Project Overview

**Watermark Remover Tool** - Python 3.10+ PyQt6 desktop GUI application with 4-layer modular architecture.

## Build / Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Build executable
pyinstaller build.spec  # Output: dist/watermark_remover.exe
```

## Testing

No formal test framework configured. If adding tests:

```bash
pip install pytest pytest-qt
pytest                              # Run all tests
pytest tests/test_image_processor.py::test_remove_watermark -v  # Single test
```

## Code Style

### Import Order
```python
# 1. Standard library
import sys, os
from pathlib import Path
from typing import Tuple, Optional, Union

# 2. Third-party (alphabetical)
import cv2
import numpy as np
from PyQt6.QtWidgets import QMainWindow

# 3. Local imports
from utils import get_config, get_logger
```

### Naming
- Classes: `PascalCase` (ImageProcessor)
- Functions: `snake_case` (remove_watermark)
- Variables: `snake_case` (input_path)
- Constants: `UPPER_SNAKE_CASE` (ALGORITHMS)
- Private: `_leading_underscore` (self._current_file)

### Type Hints
Always use: `def process_file(self, input_path: Union[str, Path], roi: Tuple[int, int, int, int]) -> Path: ...`

### Docstrings
Google-style in Chinese:
```python
def remove_watermark(self, image: np.ndarray, roi: Tuple[int, int, int, int]) -> np.ndarray:
    """
    去除图像水印
    
    Args:
        image: 输入图像 (OpenCV BGR格式)
        roi: 水印区域 (x, y, width, height)
        
    Returns:
        处理后的图像
        
    Raises:
        ImageProcessingError: 处理失败
    """
```

### Error Handling
- Custom exceptions extend `WatermarkRemoverError`
- Always log before raising
- Never use bare `except:`

### Code Formatting
- 4 spaces (no tabs)
- ~100 char line limit
- Single quotes `'`

### Patterns
- Singleton for Logger, ConfigLoader
- `__all__` in every `__init__.py`
- `logger = get_logger()` at module level
- `get_config('key.path', default)` for config

### PyQt6
- Use `pyqtSignal` for thread communication
- Keep UI in main thread
- Use `ProcessingThread` for background tasks

### Architecture
- **Utils**: Infrastructure only
- **Core**: Uses Utils
- **Services**: Uses Utils + Core
- **GUI**: Uses all layers

## File Structure

```
watermark_remover/
├── main.py              # Entry point
├── config.yaml          # Configuration
├── requirements.txt     # Dependencies
├── core/                # OpenCV algorithms
├── services/            # Business logic
├── gui/                 # PyQt6 interface
├── utils/               # Infrastructure
└── assets/              # Icons, styles
```

## Key Implementation Notes

1. **OpenCV**: BGR format (not RGB)
2. **ROI**: `(x, y, width, height)` - NOT `(x1, y1, x2, y2)`
3. **Video**: Requires ffmpeg in PATH
4. **Threading**: GUI in main thread, processing in workers

## Dependencies

- opencv-python>=4.8.0 - Image/video processing
- PyQt6>=6.4.0 - GUI framework
- numpy>=1.24.0 - Numerical operations
- Pillow>=10.0.0 - Image formats
- pyyaml>=6.0.0 - Configuration
- ffmpeg-python>=0.2.0 - Video encoding

## Configuration

- Config file: `config.yaml`
- Access: `get_config('section.key', default_value)`

---

*For AI coding assistants operating in this repository.*
