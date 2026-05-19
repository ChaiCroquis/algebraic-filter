"""
violation: set remove idempotence (2 回目で ValueError = idempotent でない)
expected_detection: hypothesis (remove 2 回後 == remove 1 回後の state)
"""


class FakeSet:
    def __init__(self) -> None:
        self._data: list = []

    def add(self, x: int) -> None:
        if x not in self._data:
            self._data.append(x)

    def remove(self, x: int) -> None:
        # bug: x が無い場合に ValueError = idempotent でない
        self._data.remove(x)

    def __len__(self) -> int:
        return len(self._data)
