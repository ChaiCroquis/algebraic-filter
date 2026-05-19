"""ground truth (fixed) for idempotence_of_dict_update — 命名を increment に統一"""


class Counter:
    def __init__(self) -> None:
        self._counts: dict = {}

    def increment(self, key: str) -> None:
        self._counts[key] = self._counts.get(key, 0) + 1

    def count(self, key: str) -> int:
        return self._counts.get(key, 0)
