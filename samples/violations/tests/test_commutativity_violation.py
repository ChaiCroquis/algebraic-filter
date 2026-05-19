"""hypothesis @given commutativity test for #commutativity_violation_in_named_commutative."""
import sys
from pathlib import Path

from hypothesis import assume, given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from commutativity_violation_in_named_commutative import merge  # noqa: E402


@given(st.text(min_size=1, max_size=5), st.text(min_size=1, max_size=5))
def test_merge_commutativity(a: str, b: str) -> None:
    assume(a != b)  # 同一 string は trivial に commutative
    lhs = merge(a, b)
    rhs = merge(b, a)
    assert lhs == rhs, f"merge({a!r}, {b!r}) = {lhs!r}, merge({b!r}, {a!r}) = {rhs!r}"
