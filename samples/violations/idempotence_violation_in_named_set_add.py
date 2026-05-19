"""
violation: set-like add の冪等性破綻 (重複許容)
expected_detection: hypothesis (add(x) 2 回後の len == add(x) 1 回後の len)
expected_skeleton: 標準 set または duplicate check 付き list
"""


class FakeSet:
    def __init__(self) -> None:
        self._data: list = []

    def add(self, x) -> None:
        # bug: set 命名だが dedup なし、 idempotence が崩れる
        self._data.append(x)

    def __len__(self) -> int:
        return len(self._data)
