"""hypothesis @given Monoid identity for concat test for #concat_identity_violation."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from concat_identity_violation import my_concat  # noqa: E402


@given(st.lists(st.text(min_size=0, max_size=5), min_size=0, max_size=5))
def test_concat_identity(xs: list[str]) -> None:
    # identity: prefix='' で my_concat('', xs) == ''.join(xs)
    expected = "".join(xs)
    actual = my_concat("", xs)
    assert actual == expected, f"my_concat('', {xs})={actual!r}, expected {expected!r}"
