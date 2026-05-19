"""ground truth (fixed) for idempotence_of_set_remove"""


class FakeSet:
    def __init__(self) -> None:
        self._data: list = []

    def add(self, x: int) -> None:
        if x not in self._data:
            self._data.append(x)

    def remove(self, x: int) -> None:
        if x in self._data:
            self._data.remove(x)

    def __len__(self) -> int:
        return len(self._data)
