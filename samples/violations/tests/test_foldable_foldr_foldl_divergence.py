"""hypothesis @given foldl/foldr equivalence test for #foldable_foldr_foldl_divergence."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from foldable_foldr_foldl_divergence import reduce_left_subtract, reduce_right_subtract  # noqa: E402


@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=2, max_size=5))
def test_foldl_foldr_equivalence(xs: list[int]) -> None:
    left = reduce_left_subtract(xs)
    right = reduce_right_subtract(xs)
    assert left == right, f"foldl({xs})={left} != foldr({xs})={right}"
