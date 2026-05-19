"""
violation: Monoid identity violation — reduce(op, xs, init) で init が true identity ではない
expected_detection: hypothesis @given (my_sum(xs) == sum(xs))
expected_fix: initial を 0 (= addition の identity) に修正
"""
import functools
import operator


def my_sum(xs: list[int]) -> int:
    # bug: addition の identity は 0 だが initial を 5 にしている
    return functools.reduce(operator.add, xs, 5)
