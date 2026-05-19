"""ground truth (fixed) for fmap_const_violation"""


def my_map(f: callable, xs: list[int]) -> list[int]:
    return [f(x) for x in xs]
