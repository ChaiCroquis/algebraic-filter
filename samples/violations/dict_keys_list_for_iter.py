"""
violation: dict.keys() を list 化してから iter (不要 list materialization)
expected_detection: tracemalloc (intermediate list allocation 観測) + ruff PERF (potentially)
"""


def find_key(d: dict[str, int], target: int) -> str | None:
    # bug: 2 つの中間 list を materialize (keys + values)
    keys_list = list(d.keys())
    values_list = list(d.values())
    for i in range(len(keys_list)):
        if values_list[i] == target:
            return keys_list[i]
    return None
