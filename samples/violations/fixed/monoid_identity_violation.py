"""ground truth (fixed) for monoid_identity_violation"""
import functools
import operator


def my_sum(xs: list[int]) -> int:
    return functools.reduce(operator.add, xs, 0)
