"""ground truth (fixed) for mutable_default_argument"""


def add_item(item: int, items: list | None = None) -> list:
    if items is None:
        items = []
    items.append(item)
    return items
