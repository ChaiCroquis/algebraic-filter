"""
violation: 命名 'update' は dict update (= idempotent overwrite) を示唆するが
            実装は increment (= 2 回呼ぶと 2 倍)
expected_detection: hypothesis (update 2 回後 count == update 1 回後 count)
"""


class Counter:
    def __init__(self) -> None:
        self._counts: dict = {}

    def update(self, key: str) -> None:
        # bug: 命名 'update' は冪等を示唆、 実装は increment
        self._counts[key] = self._counts.get(key, 0) + 1

    def count(self, key: str) -> int:
        return self._counts.get(key, 0)
