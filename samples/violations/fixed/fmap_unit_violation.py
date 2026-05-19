"""ground truth (fixed) for fmap_unit_violation"""


def pure(a: int) -> tuple:
    return ("Just", a)


def fmap(f: callable, m: tuple) -> tuple:
    if m[0] == "Just":
        return ("Just", f(m[1]))
    return m
