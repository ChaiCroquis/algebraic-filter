"""
ground truth (fixed) for foldable_foldr_foldl_divergence
両方を associative op (addition) に置き換え、 foldl == foldr が成立
"""
import functools
import operator


def reduce_left_subtract(xs: list[int]) -> int:
    # name kept for API compatibility, but implementation uses addition (associative)
    return functools.reduce(operator.add, xs, 0)


def reduce_right_subtract(xs: list[int]) -> int:
    if not xs:
        return 0
    return xs[0] + reduce_right_subtract(xs[1:])
