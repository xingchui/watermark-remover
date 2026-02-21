import json
from pathlib import Path
from typing import List
from watermark_remover.core.batch_executor import BatchResult


def write_batch_summary(results: List[BatchResult], path: str) -> Path:
    """Write batch results summary to a JSON file.

    Returns the Path to the written file.
    """
    from watermark_remover.core.batch_executor import summarize_batch_results
    summary = summarize_batch_results(results)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return p
