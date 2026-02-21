import time
from typing import List


from watermark_remover.core.batch_executor import BatchSpec, BatchItem, BatchResult, run_batch, run_batch_adaptive


def _worker_sleep(item: BatchItem) -> BatchResult:
    # simulate some work with a short sleep
    time.sleep(0.01)
    return BatchResult(True, item.input_path, item.output_path, 0, None)


def _worker_fail(item: BatchItem) -> BatchResult:
    raise ValueError("simulated failure")


def test_run_batch_basic():
    items: List[BatchItem] = [
        BatchItem(f"input_{i}.txt", f"output_{i}.txt", {}) for i in range(5)
    ]
    spec = BatchSpec(items=items, max_workers=3, use_processes=False)
    results = run_batch(spec, _worker_sleep)
    assert len(results) == 5
    assert all(r.success for r in results)
    assert all(r.input_path.startswith("input_" ) for r in results)


def test_run_batch_with_error():
    item = BatchItem("in.txt", "out.txt", {})
    spec = BatchSpec(items=[item], max_workers=1, use_processes=False)
    results = run_batch(spec, _worker_fail)
    assert len(results) == 1
    assert results[0].success is False
    assert results[0].error is not None


def test_run_batch_partial_success_and_failure():
    items = [
        BatchItem("in1.txt", "out1.txt", {}),
        BatchItem("in2.txt", "out2.txt", {}),
        BatchItem("in3.txt", "out3.txt", {}),
    ]
    spec = BatchSpec(items=items, max_workers=2, use_processes=False)

    def worker(item: BatchItem) -> BatchResult:
        if item.input_path == "in2.txt":
            raise RuntimeError("boom")
        time.sleep(0.005)
        return BatchResult(True, item.input_path, item.output_path, 0, None)

    results = run_batch(spec, worker)
    assert len(results) == 3
    # We expect one failure and two successes
    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]
    assert len(successes) == 2
    assert len(failures) == 1


def test_run_batch_adaptive_default_workers():
    items = [
        BatchItem(f"in_{i}.txt", f"out_{i}.txt", {}) for i in range(4)
    ]
    spec = BatchSpec(items=items, max_workers=0, use_processes=False)
    def worker(item: BatchItem) -> BatchResult:
        time.sleep(0.005)
        return BatchResult(True, item.input_path, item.output_path, 0, None)
    results = run_batch_adaptive(spec, worker, adaptive=True)
    assert len(results) == 4
    assert all(r.success for r in results)


def test_run_batch_adaptive_respects_config():
    items = [BatchItem(f"in_{i}.txt", f"out_{i}.txt", {}) for i in range(2)]
    spec = BatchSpec(items=items, max_workers=2, use_processes=False)
    def worker(item: BatchItem) -> BatchResult:
        time.sleep(0.001)
        return BatchResult(True, item.input_path, item.output_path, 0, None)
    results = run_batch_adaptive(spec, worker, adaptive=True)
    assert len(results) == 2
    assert all(r.success for r in results)


def test_run_batch_adaptive_weights_preserved():
    items = [
        BatchItem("in1.txt", "out1.txt", {"weight": 0.5}),
        BatchItem("in2.txt", "out2.txt", {"weight": 2.0}),
        BatchItem("in3.txt", "out3.txt", {"weight": 1.0}),
    ]
    spec = BatchSpec(items=items, max_workers=4, use_processes=False)

    def worker(item: BatchItem) -> BatchResult:
        w = item.payload.get("weight", 1.0)
        time.sleep(0.005 * w)
        return BatchResult(True, item.input_path, item.output_path, int(10 * w), None, weight=w)

    results = run_batch_adaptive(spec, worker, adaptive=True)
    assert len(results) == 3
    for r, it in zip(results, items):
        assert r.weight == it.payload.get("weight", 1.0)
