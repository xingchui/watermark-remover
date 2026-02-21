from pathlib import Path

import pytest
from watermark_remover.services.image_service import ImageService
from watermark_remover.services.video_service import VideoService


def test_image_batch_integration(monkeypatch):
    # Patch ImageService.process to a fake implementation that returns a deterministic output path
    def fake_image_process(self, input_path, roi, output_path=None, algorithm=None, radius=None, quality=None):
        # simulate output path
        return Path(str(input_path) + ".out.png")

    monkeypatch.setattr(ImageService, "process", fake_image_process, raising=True)

    svc = ImageService()
    inputs = ["img1.png", "img2.png"]
    roi = (0, 0, 10, 10)
    outs = svc.batch_process_images(inputs, roi, max_workers=2, use_processes=False)

    assert isinstance(outs, list)
    assert [str(p) for p in outs] == ["img1.png.out.png", "img2.png.out.png"]


def test_video_batch_integration(monkeypatch):
    def fake_video_process(self, input_path, roi, output_path=None, algorithm=None, radius=None):
        return Path(str(input_path) + ".out.mp4")

    monkeypatch.setattr(VideoService, "process", fake_video_process, raising=True)

    svc = VideoService()
    inputs = ["vid1.mp4", "vid2.mp4"]
    roi = (0, 0, 20, 20)
    outs = svc.batch_process_videos(inputs, roi, max_workers=2, use_processes=False)

    assert isinstance(outs, list)
    assert [str(p) for p in outs] == ["vid1.mp4.out.mp4", "vid2.mp4.out.mp4"]
