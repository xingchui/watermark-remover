from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional, Callable
import json
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import os


@dataclass
class BatchItem:
    input_path: str
    output_path: Optional[str]
    payload: dict


@dataclass
class BatchResult:
    success: bool
    input_path: str
    output_path: Optional[str]
    duration_ms: int
    error: Optional[str] = None
    weight: float = 1.0


@dataclass
class BatchSpec:
    items: List[BatchItem]
    max_workers: int
    use_processes: bool = False


def _wrap_worker(worker_fn: Callable[[BatchItem], BatchResult], item: BatchItem) -> BatchResult:
    t0 = time.time()
    try:
        res = worker_fn(item)
        duration = int((time.time() - t0) * 1000)
        if isinstance(res, BatchResult):
            res.duration_ms = duration
            if res.input_path is None:
                res.input_path = item.input_path
            if res.output_path is None:
                res.output_path = item.output_path
            # 保证 weight 存在且来自 payload
            if getattr(res, 'weight', None) in (None, 0):
                res.weight = item.payload.get('weight', 1.0)
            return res
        # If worker_fn returns something else, normalize to a success result
        return BatchResult(True, item.input_path, item.output_path, duration, None, item.payload.get('weight', 1.0))
    except Exception as e:
        duration = int((time.time() - t0) * 1000)
        return BatchResult(False, item.input_path, item.output_path, duration, str(e), item.payload.get('weight', 1.0))


def run_batch(spec: BatchSpec, worker_fn: Callable[[BatchItem], BatchResult]) -> List[BatchResult]:
    if not spec.items:
        return []
    max_workers = max(1, int(spec.max_workers))
    executor_cls = ProcessPoolExecutor if spec.use_processes else ThreadPoolExecutor
    results: List[BatchResult] = []
    with executor_cls(max_workers=max_workers) as executor:
        futures = [executor.submit(_wrap_worker, worker_fn, item) for item in spec.items]
        for fut in as_completed(futures):
            try:
                res = fut.result()
            except Exception as e:
                # In case worker_fn raises inside the executor unexpectedly
                # We cannot determine input_path here reliably; provide a generic failure
                results.append(BatchResult(False, "", None, 0, str(e), 1.0))
            else:
                if isinstance(res, BatchResult):
                    results.append(res)
                else:
                    results.append(BatchResult(True, "", None, 0, None))
    return results


def run_batch_adaptive(spec: BatchSpec, worker_fn: Callable[[BatchItem], BatchResult], adaptive: bool = True) -> List[BatchResult]:
    """Adaptive version of run_batch with chunked, dynamic concurrency.
    This implementation processes items in chunks, re-subscribing with potentially adjusted
    concurrency after each chunk to better adapt to observed per-item durations.
    """
    if not adaptive:
        return run_batch(spec, worker_fn)

    # Determine cap for maximum workers
    if spec.max_workers and spec.max_workers > 0:
        cap = int(spec.max_workers)
    else:
        cpu = os.cpu_count() or 1
        cap = min(32, max(1, cpu * 2))  # sensible default for adaptation

    results: List[BatchResult] = []
    items = spec.items
    n = len(items)
    if n == 0:
        return results

    # Choose executor type based on specification
    executor_cls = ProcessPoolExecutor if spec.use_processes else ThreadPoolExecutor

    idx = 0
    # Process in chunks; adapt cap after each chunk based on observed durations
    while idx < n:
        chunk_size = min(cap, n - idx)
        chunk = items[idx: idx + chunk_size]

        with executor_cls(max_workers=max(1, chunk_size)) as executor:
            futures = [executor.submit(_wrap_worker, worker_fn, it) for it in chunk]
            for fut in as_completed(futures):
                res = fut.result()
                results.append(res)

        # Compute average duration for this chunk to adjust concurrency
        durations = [r.duration_ms for r in results[-chunk_size:]]
        if durations:
            avg = sum(durations) / len(durations)
            # simple heuristic: if too slow, decrease cap; if fast, increase cap
            if avg > 200 and cap > 1:
                cap = max(1, cap - 1)
            elif avg < 50 and cap < 32:
                cap = min(32, cap + 1)
        idx += chunk_size

    return results


def summarize_batch_results(results: List[BatchResult]) -> dict:
    """Generate a concise summary for a batch execution.

    Returns a dict with:
      - total: total number of items
      - success: number of successful items
      - failures: number of failed items
      - total_duration_ms: total time spent on all items
      - avg_duration_ms: average time per item
      - total_weight: sum of per-item weights
      - avg_weight: average weight per item
      - min_weight: minimum weight among items
      - max_weight: maximum weight among items
    """
    total = len(results)
    if total == 0:
        return {
            "total": 0,
            "success": 0,
            "failures": 0,
            "total_duration_ms": 0,
            "avg_duration_ms": 0.0,
            "total_weight": 0.0,
            "avg_weight": 0.0,
            "min_weight": 0.0,
            "max_weight": 0.0,
        }
    success = sum(1 for r in results if r.success)
    failures = total - success
    total_duration = sum(r.duration_ms for r in results)
    avg_duration = total_duration / total if total > 0 else 0.0
    total_weight = sum((getattr(r, 'weight', 1.0) or 1.0) for r in results)
    avg_weight = total_weight / total if total > 0 else 0.0
    weights = [getattr(r, 'weight', 1.0) or 1.0 for r in results]
    return {
        "total": total,
        "success": success,
        "failures": failures,
        "total_duration_ms": total_duration,
        "avg_duration_ms": avg_duration,
        "total_weight": total_weight,
        "avg_weight": avg_weight,
        "min_weight": min(weights),
        "max_weight": max(weights),
    }
