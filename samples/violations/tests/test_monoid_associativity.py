"""
Phase 0 Day 4 hypothesis 検出能力評価 test.

#5 monoid_associativity_violation.py の my_sum() に対し、
hypothesis @given で「標準 sum() と等価か」 を property test する。

期待結果: AssertionError (= violation 検出 PASS)
理由: my_sum は subtraction reduce で、 標準 sum (addition reduce) とは結果が異なる
"""
import functools

from hypothesis import given, strategies as st


def my_sum(xs: list[int]) -> int:
    """copy of samples/violations/monoid_associativity_violation.py:my_sum"""
    return functools.reduce(lambda a, b: a - b, xs, 0)


@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=10))
def test_my_sum_matches_standard_sum(xs: list[int]) -> None:
    expected = sum(xs)
    actual = my_sum(xs)
    assert actual == expected, f"my_sum({xs})={actual} but sum={expected}"
