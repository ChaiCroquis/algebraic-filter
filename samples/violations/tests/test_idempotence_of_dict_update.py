"""hypothesis @given dict update idempotence test for #idempotence_of_dict_update."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from idempotence_of_dict_update import Counter  # noqa: E402


@given(st.text(min_size=1, max_size=5))
def test_dict_update_idempotence(key: str) -> None:
    c = Counter()
    c.update(key)
    count_after_first = c.count(key)
    # 2 回目 update は idempotent であるべき (= count 不変)
    c.update(key)
    count_after_second = c.count(key)
    assert count_after_first == count_after_second, (
        f"update({key!r}) idempotence: first={count_after_first}, second={count_after_second}"
    )
