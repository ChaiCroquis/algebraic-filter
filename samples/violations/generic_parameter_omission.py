"""
violation: typing.List 古い style (ruff UP006: use builtin lowercase list)
expected_detection: ruff --select=UP (UP006)
"""
from typing import List


def add_one(xs: List[int]) -> List[int]:
    return [x + 1 for x in xs]
