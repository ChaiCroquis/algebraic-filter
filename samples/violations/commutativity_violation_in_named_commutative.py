"""
violation: commutative-named function ('merge') が non-commutative
expected_detection: hypothesis @given (merge(a, b) == merge(b, a))
expected_skeleton: order-independent operation (例: sorted concat)
"""


def merge(a: str, b: str) -> str:
    # naming suggests commutative (merge は通常 set merge 等で commutative)
    # しかし実装は単純 concat = non-commutative ("x_y" != "y_x")
    return a + "_" + b
