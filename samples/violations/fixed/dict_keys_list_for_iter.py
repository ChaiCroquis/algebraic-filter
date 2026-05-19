"""ground truth (fixed) for dict_keys_list_for_iter — items() で直接 iter"""


def find_key(d: dict[str, int], target: int) -> str | None:
    for k, v in d.items():
        if v == target:
            return k
    return None
