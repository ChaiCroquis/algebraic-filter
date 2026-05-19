"""
violation: 命名 intersect は可換だが、 order が a 依存 (intersect(a,b) != intersect(b,a) for ordering)
expected_detection: hypothesis @given (intersect(a,b) == intersect(b,a) for set equality)
"""


def intersect(a: list[int], b: list[int]) -> list[int]:
    # bug: order が a に依存 → intersect(a, b) と intersect(b, a) で list order が異なる
    return [x for x in a if x in b]
