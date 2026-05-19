"""
ground truth (fixed) for monad_left_identity_violation
left identity satisfied: bind(pure(a), f) == f(a)
"""


def pure(a: int) -> tuple:
    return ("Just", a)


def bind(m: tuple, f: callable) -> tuple:
    if m[0] == "Just":
        return f(m[1])
    return m
