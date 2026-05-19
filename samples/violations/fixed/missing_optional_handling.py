"""
ground truth (fixed) for missing_optional_handling
戻り値型を `int | None` にして None 可能性を articulate
"""


def find_first_positive(xs: list[int]) -> int | None:
    for x in xs:
        if x > 0:
            return x
    return None
