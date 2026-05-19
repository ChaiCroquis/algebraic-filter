"""hypothesis @given Maybe Functor unit law test for #fmap_unit_violation."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fmap_unit_violation import pure, fmap  # noqa: E402


@given(st.integers(min_value=-50, max_value=50))
def test_fmap_unit_law(a: int) -> None:
    def f(x: int) -> int:
        return x + 1

    lhs = fmap(f, pure(a))
    rhs = pure(f(a))
    assert lhs == rhs, f"fmap(f, pure({a}))={lhs}, pure(f({a}))={rhs}"
