"""
violation: monoid_associativity_violation の icontract 付き variant
expected_detection: CrossHair check on @icontract.ensure (post-condition)
expected_skeleton: addition reduce (Monoid 整合)

icontract で post-condition 「my_sum(xs) == sum(xs)」 を articulate、
CrossHair が counter-example を探索 → subtraction reduce で違反 surface。

実走:
    python -m crosshair check samples/violations/monoid_associativity_with_icontract.py
    期待: counter-example found (exit code 1) for xs=[1] や [1, 2] 等
"""
from __future__ import annotations

import functools

import icontract


@icontract.require(lambda xs: isinstance(xs, list))
@icontract.ensure(lambda xs, result: result == sum(xs))
def my_sum(xs: list[int]) -> int:
    # bug: subtraction reduce (non-associative, identity broken)
    return functools.reduce(lambda a, b: a - b, xs, 0)
