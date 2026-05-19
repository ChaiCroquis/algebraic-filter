"""hypothesis @given Monad associativity test for #monad_associativity_violation."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monad_associativity_violation import pure, bind  # noqa: E402


@given(st.integers(min_value=-50, max_value=50))
def test_monad_associativity(a: int) -> None:
    def f(x: int) -> tuple:
        return pure(x + 1)

    def g(x: int) -> tuple:
        return pure(x * 2)

    # associativity: bind(bind(m, f), g) == bind(m, lambda x: bind(f(x), g))
    lhs = bind(bind(pure(a), f), g)
    rhs = bind(pure(a), lambda x: bind(f(x), g))
    assert lhs == rhs, f"bind associativity fails for a={a}: lhs={lhs}, rhs={rhs}"
