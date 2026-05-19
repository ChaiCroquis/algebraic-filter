"""hypothesis @given Functor identity test for #functor_id_violation."""
import sys
from pathlib import Path

from hypothesis import given, strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from functor_id_violation import my_map  # noqa: E402


@given(
    st.lists(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
        min_size=1,
        max_size=5,
    )
)
def test_functor_id_law(xs: list[float]) -> None:
    expected = list(xs)
    actual = my_map(lambda x: x, xs)
    assert actual == expected, f"my_map(id, {xs}) = {actual}, expected {expected}"
