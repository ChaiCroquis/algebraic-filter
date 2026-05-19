"""
ground truth (fixed) for sim103_needless_bool
expected_detection_after_fix: ruff SIM should find NO violations (exit 0)
"""


def is_positive(x: int) -> bool:
    return x > 0
