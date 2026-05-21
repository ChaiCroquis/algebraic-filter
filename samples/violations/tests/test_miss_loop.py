"""Regression tests for the miss-loop separation classifier (scripts/miss_loop.py).

Pins the deterministic 切り分け judgment: which misses are clustered
(bulk-fixable) vs non-clustered (hard tail).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from miss_loop import classify_miss  # noqa: E402


def test_type_error_is_clustered_pyright() -> None:
    cl, path = classify_miss("type-error", "coerce")
    assert cl is True
    assert "pyright" in path


def test_perf_is_clustered_ruff() -> None:
    cl, path = classify_miss("perf", "double_it")
    assert cl is True
    assert "ruff" in path


def test_boundary_is_clustered_strategy() -> None:
    cl, _ = classify_miss("boundary", "my_sum")
    assert cl is True


def test_algebra_intent_name_is_clustered() -> None:
    """intent を持つ名前の代数違反 = keyword 拡張で一括 = clustered."""
    for name in ("tally", "accumulate_total", "blend", "total_score"):
        cl, path = classify_miss("algebra-assoc", name)
        assert cl is True, name
        assert "keyword" in path


def test_algebra_no_intent_name_is_non_clustered() -> None:
    """intent 信号なし名の代数違反 = hard tail = non-clustered."""
    for name in ("thingy", "process_items", "do_op", "handle_x"):
        cl, path = classify_miss("algebra-commut", name)
        assert cl is False, name
        assert "hard tail" in path
