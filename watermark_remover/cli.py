#!/usr/bin/env python3
"""命令行界面：批量图像/视频处理(mixture)"""
import sys
import os
import json
from __future__ import annotations
# 兼容不同项目结构的导入路径
_root_candidates = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
]
for _p in _root_candidates:
    if _p not in sys.path:
        sys.path.insert(0, _p)
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

try:
    from watermark_remover.services.image_service import ImageService
except Exception:
    try:
        from services.image_service import ImageService
    except Exception:
        ImageService = None  # type: ignore

try:
    from watermark_remover.services.video_service import VideoService
except Exception:
    try:
        from services.video_service import VideoService
    except Exception:
        VideoService = None  # type: ignore

# Basic guard: ensure essential services are importable
if ImageService is None or VideoService is None:
    print("Error: 无法导入 ImageService/VideoService。请检查 PYTHONPATH 或项目结构。", file=sys.stderr)
    sys.exit(1)


def parse_roi(roi_str: str) -> Tuple[int, int, int, int]:
    """解析 ROI 字符串为 (x, y, w, h)。支持用逗号或空格分隔。
    例："10,20,100,50" 或 "10 20 100 50"。
    """
    parts = [p.strip() for p in roi_str.replace(',', ' ').split() if p.strip()]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("ROI 需要 4 个整数组成：x, y, width, height")
    try:
        vals = tuple(int(p) for p in parts)
    except ValueError:
        raise argparse.ArgumentTypeError("ROI 必须是整数")
    return vals


def main() -> int:
    parser = argparse.ArgumentParser(description="批量处理图像/视频以去水印（并行/并发）")
    sub = parser.add_subparsers(dest="command", required=True)

    # batch-image
    p_img = sub.add_parser("batch-image", help="批量处理图像")
    p_img.add_argument("paths", nargs="+", help="输入图像路径列表")
    p_img.add_argument("--roi", required=True, type=parse_roi, help="ROI: x,y,w,h 或 x w h 在同一行，整数值")
    p_img.add_argument("--algorithm", default=None, help="修复算法，例如 telea/ns/advanced")
    p_img.add_argument("--radius", type=int, default=None, help="修复半径")
    p_img.add_argument("--quality", type=int, default=None, help="输出质量(0-100)")
    p_img.add_argument("--max-workers", type=int, default=4, help="最大并发工作数")
    p_img.add_argument("--use-processes", action="store_true", help="使用进程池进行并行")
    p_img.add_argument("--adaptive", action="store_true", help="启用自适应并发调度")
    p_img.add_argument("--summary-path", dest="summary_path", default=None, help="汇总输出 JSON 文件路径")
    p_img.add_argument("--output-dir", dest="output_dir", default=None, help="输出目录")

    # batch-video
    p_vid = sub.add_parser("batch-video", help="批量处理视频")
    p_vid.add_argument("paths", nargs="+", help="输入视频路径列表")
    p_vid.add_argument("--roi", required=True, type=parse_roi, help="ROI: x,y,w,h 或 x w h 在同一行，整数值")
    p_vid.add_argument("--algorithm", default=None, help="修复算法，例如 telea/ns/advanced")
    p_vid.add_argument("--radius", type=int, default=None, help="修复半径")
    p_vid.add_argument("--max-workers", type=int, default=4, help="最大并发工作数")
    p_vid.add_argument("--use-processes", action="store_true", help="使用进程池进行并行")
    p_vid.add_argument("--adaptive", action="store_true", help="启用自适应并发调度")
    p_vid.add_argument("--output-dir", dest="output_dir", default=None, help="输出目录")

    args = parser.parse_args()

    if args.command == "batch-image":
        svc = ImageService(output_dir=args.output_dir)
        input_paths = [Path(p) for p in args.paths]
        out = svc.batch_process_images(
            input_paths,
            roi=args.roi,
            algorithm=args.algorithm,
            radius=args.radius,
            quality=args.quality,
            max_workers=args.max_workers,
            use_processes=args.use_processes,
            adaptive=args.adaptive,
            summary_path=args.summary_path,
        )
        print("输出文件：", [str(p) for p in out])
        return 0

    if args.command == "batch-video":
        svc = VideoService(output_dir=args.output_dir)
        input_paths = [Path(p) for p in args.paths]
        out = svc.batch_process_videos(
            input_paths,
            roi=args.roi,
            algorithm=args.algorithm,
            radius=args.radius,
            max_workers=args.max_workers,
            use_processes=args.use_processes,
            adaptive=args.adaptive,
        )
        print("输出文件：", [str(p) for p in out])
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
