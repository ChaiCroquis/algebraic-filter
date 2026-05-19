"""hypothesis @given commutativity test for #intersect_commutativity_violation."""
import sys
from pathlib import Path

from hypothesis import assume, given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from intersect_commutativity_violation import intersect  # noqa: E402


@given(
    st.lists(st.integers(min_value=-20, max_value=20), min_size=1, max_size=5),
    st.lists(st.integers(min_value=-20, max_value=20), min_size=1, max_size=5),
)
def test_intersect_commutativity(a: list[int], b: list[int]) -> None:
    assume(a != b)
    lhs = intersect(a, b)
    rhs = intersect(b, a)
    assert lhs == rhs, f"intersect({a}, {b})={lhs}, intersect({b}, {a})={rhs}"
