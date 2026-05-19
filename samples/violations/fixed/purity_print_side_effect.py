"""
ground truth (fixed) for purity_print_side_effect
expected_detection_after_fix:
    - (Phase 1+ custom rule / CrossHair @pure) should find NO side effects
    - print statement removed → pure function
"""


def calc(x: int) -> int:
    return x * 2
