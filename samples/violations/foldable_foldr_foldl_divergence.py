"""
violation: Foldable property — foldl/foldr divergence for non-associative op
両方 "sum-like" 命名だが、 subtraction reduce は非結合のため foldl と foldr で結果が異なる
expected_detection: hypothesis @given (reduce_left(xs) == reduce_right(xs))
expected_skeleton: associative op を要件として明示、 または sum() / operator.add に置き換え
"""
import functools


def reduce_left_subtract(xs: list[int]) -> int:
    """foldl style: subtraction left-to-right"""
    return functools.reduce(lambda a, b: a - b, xs, 0)


def reduce_right_subtract(xs: list[int]) -> int:
    """foldr style: subtraction right-to-left"""
    if not xs:
        return 0
    return xs[0] - reduce_right_subtract(xs[1:])
