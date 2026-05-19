"""hypothesis @given set remove idempotence test for #idempotence_of_set_remove."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from idempotence_of_set_remove import FakeSet  # noqa: E402


@given(st.integers(min_value=-100, max_value=100))
def test_set_remove_idempotence(x: int) -> None:
    s = FakeSet()
    s.add(x)
    s.remove(x)
    len_after_first = len(s)
    # 2 回目 remove は idempotent であるべき (= state 不変)
    s.remove(x)
    len_after_second = len(s)
    assert len_after_first == len_after_second, (
        f"remove({x}) idempotence: first={len_after_first}, second={len_after_second}"
    )
