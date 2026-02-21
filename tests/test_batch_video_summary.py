import json
from pathlib import Path

def test_video_batch_summary_file_written(tmp_path, monkeypatch):
    from watermark_remover.services.video_service import VideoService
    # fake process to avoid real file IO
    def fake_process(self, input_path, roi, output_path=None, algorithm=None, radius=None):
        return Path(str(input_path) + ".out.mp4")
    monkeypatch.setattr(VideoService, "process", fake_process, raising=True)

    svc = VideoService()
    inputs = [Path("vid1.mp4"), Path("vid2.mp4")]
    roi = (0, 0, 100, 100)
    summary_path = tmp_path / "summary.json"

    outs = svc.batch_process_videos(inputs, roi, adaptive=True, max_workers=2, use_processes=False, summary_path=str(summary_path))

    # Outputs should be a list of Path objects
    assert isinstance(outs, list)
    # Summary file should exist
    assert summary_path.exists(), f"Summary file not created: {summary_path}"
    with open(summary_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Basic checks on summary structure
    assert "total" in data and "success" in data and "failures" in data
