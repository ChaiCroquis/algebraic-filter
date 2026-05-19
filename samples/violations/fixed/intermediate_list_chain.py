"""
ground truth (fixed) for intermediate_list_chain
expected_detection_after_fix:
    - ruff PERF: still no detection (ruff 標準ルールは元から検出しない、 baseline)
    - tracemalloc: single comprehension → 中間 list materialization が消失、 allocation 件数大幅減
"""


def transform(data: list[int]) -> list[int]:
    return [x * 2 for x in data if x > 0]
