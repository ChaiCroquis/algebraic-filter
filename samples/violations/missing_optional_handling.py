"""
violation: function は Optional[int] を返すが signature は `-> int` (None handling 欠落)
expected_detection: mypy --strict (Phase 1 で install) or ruff RUF series
expected_skeleton: 戻り値型に None 含める (`int | None`)
"""


def find_first_positive(xs: list[int]) -> int:
    for x in xs:
        if x > 0:
            return x
    return None  # bug: signature 通りなら int だが None を return
