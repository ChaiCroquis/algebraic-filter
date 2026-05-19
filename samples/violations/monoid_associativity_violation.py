"""
violation: monoid associativity (subtraction is not associative, but function is named "sum")
expected_detection: CrossHair with @icontract or PEP316 contract / hypothesis @given test
expected_skeleton: use addition (Monoid: int+0 is associative) instead of subtraction
expected_fix:
    import functools, operator
    def my_sum(xs: list[int]) -> int:
        return functools.reduce(operator.add, xs, 0)

For CrossHair detection, the contract would be:
    pre: True
    post: __return__ == sum(xs)  # standard sum semantics

CrossHair should find a counterexample like xs=[1, 2] where:
    expected sum([1, 2]) = 3
    actual my_sum([1, 2]) = 0 - 1 - 2 = -3
"""

import functools


def my_sum(xs: list[int]) -> int:
    # naming claims "sum" semantics (associative monoid with 0 identity)
    # but implementation uses subtraction (non-associative, identity broken)
    return functools.reduce(lambda a, b: a - b, xs, 0)
