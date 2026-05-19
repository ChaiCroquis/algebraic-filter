"""ground truth (fixed) for monad_associativity_violation"""


def pure(a: int) -> tuple:
    return ("Just", a)


def bind(m: tuple, f: callable) -> tuple:
    if m[0] == "Just":
        return f(m[1])
    return m
