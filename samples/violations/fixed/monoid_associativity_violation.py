"""
ground truth (fixed) for monoid_associativity_violation
expected_detection_after_fix: hypothesis @given test (Monoid law: standard sum equivalence) should PASS

verification:
    pytest samples/violations/tests/test_monoid_fixed.py -v
    -> 1 passed (no Falsifying example)
"""
import functools
import operator


def my_sum(xs: list[int]) -> int:
    return functools.reduce(operator.add, xs, 0)
