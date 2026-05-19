"""
violation: FURB118 — reimplemented operator (lambda p: p[0] -> operator.itemgetter)
expected_detection: ruff --select=FURB (FURB118)
"""


def get_firsts(pairs: list[tuple[int, int]]) -> list[int]:
    return list(map(lambda p: p[0], pairs))
