"""AF Phase 3 — tracemalloc-based runtime data movement checker.

関数を tracemalloc で計測、 input size に対する allocation 比率 (= overhead factor) で
data movement 効率を articulate。 閾値超過時に 構造化 violation を返す.
"""
from __future__ import annotations

import tracemalloc
from typing import Any, Callable, NamedTuple


class RuntimeMeasurement(NamedTuple):
    function_name: str
    total_size_bytes: int
    allocation_count: int
    top_allocations: list[str]


class RuntimeViolation(NamedTuple):
    rule_id: str
    function_name: str
    measured_bytes: int
    threshold_bytes: int
    overhead_factor: float
    message: str


def measure(func: Callable, *args: Any, **kwargs: Any) -> RuntimeMeasurement:
    """関数を tracemalloc で計測、 allocation 統計を返す."""
    tracemalloc.start()
    snap_before = tracemalloc.take_snapshot()
    func(*args, **kwargs)
    snap_after = tracemalloc.take_snapshot()
    diff = snap_after.compare_to(snap_before, "lineno")

    positive = [s for s in diff if s.size_diff > 0]
    total_size = sum(s.size_diff for s in positive)
    total_count = sum(s.count_diff for s in positive)
    top = [f"{s}" for s in positive[:3]]

    tracemalloc.stop()
    return RuntimeMeasurement(
        function_name=getattr(func, "__name__", "?"),
        total_size_bytes=total_size,
        allocation_count=total_count,
        top_allocations=top,
    )


def check_threshold(
    func: Callable,
    sample_input: Any,
    *,
    max_bytes: int = 100 * 1024,
    expected_input_bytes: int | None = None,
) -> tuple[RuntimeViolation | None, RuntimeMeasurement]:
    """関数の allocation が閾値を超えるかチェック.

    overhead_factor = measured / expected_input_bytes (= 入力 size に対する allocation 倍率)
    threshold 超過時に RuntimeViolation を返す.
    """
    m = measure(func, sample_input)
    overhead = (
        m.total_size_bytes / expected_input_bytes
        if expected_input_bytes and expected_input_bytes > 0
        else float("nan")
    )

    if m.total_size_bytes > max_bytes:
        violation = RuntimeViolation(
            rule_id="excessive-data-movement",
            function_name=m.function_name,
            measured_bytes=m.total_size_bytes,
            threshold_bytes=max_bytes,
            overhead_factor=overhead,
            message=(
                f"{m.function_name} allocated {m.total_size_bytes:,} bytes "
                f"(> threshold {max_bytes:,}, overhead x{overhead:.2f}). "
                "Stream Fusion / single comprehension 等で削減可能か確認"
            ),
        )
        return violation, m

    return None, m
