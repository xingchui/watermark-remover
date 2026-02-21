#!/usr/bin/env bash
set -euo pipefail

echo "AGENTS 验证开始..."

# 1) pytest 子集（若有依赖）
if command -v pytest >/dev/null 2>&1; then
  echo "Running pytest subset..."
  pytest tests/test_batch_executor.py::test_run_batch_basic -q || echo "pytest basic test FAILED"
else
  echo "pytest not found, skip"
fi

# 2) mypy 检查
if command -v mypy >/dev/null 2>&1; then
  echo "Running mypy..."
  mypy watermark_remover core services utils gui || true
else
  echo "mypy not found, skip"
fi

# 3) 简单静态分析
if command -v flake8 >/dev/null 2>&1; then
  echo "Running flake8..."
  flake8 watermark_remover tests || true
else
  echo "flake8 not found, skip"
fi

echo "Verification script completed."
