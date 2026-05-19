"""
ground truth (fixed) for commutativity_violation_in_named_commutative
sorted concat にすれば merge(a, b) == merge(b, a) を満たす
"""


def merge(a: str, b: str) -> str:
    return "_".join(sorted([a, b]))
