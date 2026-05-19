"""
ground truth (fixed) for perf401_manual_list_comp
expected_detection_after_fix: ruff PERF should find NO violations (exit 0)
"""


def double_positives(data: list[int]) -> list[int]:
    return [x * 2 for x in data if x > 0]
