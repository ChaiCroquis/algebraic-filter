"""hypothesis @given Monoid identity test for #monoid_identity_violation."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monoid_identity_violation import my_sum  # noqa: E402


@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=10))
def test_monoid_identity(xs: list[int]) -> None:
    expected = sum(xs)
    actual = my_sum(xs)
    assert actual == expected, f"my_sum({xs})={actual}, expected={expected}"
