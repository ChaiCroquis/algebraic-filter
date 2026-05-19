"""hypothesis @given Monad left identity test for #monad_left_identity_violation."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monad_left_identity_violation import pure, bind  # noqa: E402


@given(st.integers(min_value=-100, max_value=100))
def test_monad_left_identity(a: int) -> None:
    def f(x: int) -> tuple:
        return pure(x * 2)

    lhs = bind(pure(a), f)
    rhs = f(a)
    assert lhs == rhs, f"bind(pure({a}), f) = {lhs}, expected {rhs}"
