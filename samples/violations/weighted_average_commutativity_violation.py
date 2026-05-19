"""
violation: 命名 'average' は可換だが、 weighted 実装が引数順序依存
expected_detection: hypothesis @given (average(a, b) == average(b, a))
expected_fix: 等重み平均 ((a + b) / 2)
"""


def average(a: float, b: float) -> float:
    # bug: weighted (1, 2) のため average(a, b) != average(b, a)
    return (1 * a + 2 * b) / 3
