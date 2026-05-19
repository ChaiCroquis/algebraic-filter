"""
violation: C416 — unnecessary comprehension (list(x) で十分な場面に [x for x in xs])
expected_detection: ruff --select=C (C416)
"""


def to_list(iterable: list[int]) -> list[int]:
    return [item for item in iterable]
