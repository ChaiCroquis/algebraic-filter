"""hypothesis @given Monad right identity test for #monad_right_identity_violation."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monad_right_identity_violation import pure, bind  # noqa: E402


@given(st.integers(min_value=-50, max_value=50))
def test_monad_right_identity(a: int) -> None:
    m = pure(a)
    result = bind(m, pure)
    assert result == m, f"bind(pure({a}), pure)={result}, expected {m}"
