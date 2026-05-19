"""
ground truth (fixed) for idempotence_violation_in_named_set_add
dedup check で idempotence 成立: add(x); add(x) と add(x) で同じ状態
"""


class FakeSet:
    def __init__(self) -> None:
        self._data: list = []

    def add(self, x: int) -> None:
        if x not in self._data:
            self._data.append(x)

    def __len__(self) -> int:
        return len(self._data)
