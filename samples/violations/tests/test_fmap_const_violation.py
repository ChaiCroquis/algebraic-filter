"""hypothesis @given Functor const law test for #fmap_const_violation."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fmap_const_violation import my_map  # noqa: E402


@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=5), st.integers(min_value=-50, max_value=50))
def test_functor_const_law(xs: list[int], k: int) -> None:
    expected = [k] * len(xs)
    actual = my_map(lambda _: k, xs)
    assert actual == expected, f"my_map(const({k}), {xs}) = {actual}, expected {expected}"
