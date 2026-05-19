"""hypothesis @given Functor compose law test for #fmap_compose_violation."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fmap_compose_violation import my_map  # noqa: E402


@given(st.lists(st.integers(min_value=-50, max_value=50), min_size=1, max_size=5))
def test_functor_compose_law(xs: list[int]) -> None:
    def f(x: int) -> int:
        return x + 1

    def g(x: int) -> int:
        return x * 2

    lhs = my_map(f, my_map(g, xs))
    rhs = my_map(lambda x: f(g(x)), xs)
    assert lhs == rhs, f"compose law fails for {xs}: lhs={lhs}, rhs={rhs}"
