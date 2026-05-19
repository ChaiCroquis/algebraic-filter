"""hypothesis @given idempotence test for #idempotence_violation_in_named_set_add."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from idempotence_violation_in_named_set_add import FakeSet  # noqa: E402


@given(st.integers(min_value=-100, max_value=100))
def test_idempotence_of_add(x: int) -> None:
    s = FakeSet()
    s.add(x)
    len_once = len(s)
    s.add(x)
    len_twice = len(s)
    assert len_once == len_twice, f"add({x}) twice: len {len_once} -> {len_twice}"
