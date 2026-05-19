"""hypothesis @given commutativity test for #weighted_average_commutativity_violation."""
import sys
from pathlib import Path

from hypothesis import assume, given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from weighted_average_commutativity_violation import average  # noqa: E402


@given(
    st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
    st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
)
def test_average_commutativity(a: float, b: float) -> None:
    assume(a != b)
    lhs = average(a, b)
    rhs = average(b, a)
    assert lhs == rhs, f"average({a}, {b})={lhs}, average({b}, {a})={rhs}"
