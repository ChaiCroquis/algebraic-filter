"""
violation: Maybe Monad の left identity law violation
left identity: bind(pure(a), f) == f(a)
expected_detection: hypothesis @given (bind(pure(a), f) == f(a))
expected_skeleton: bind が pure constructor の中身を取り出して f に渡す
"""


def pure(a: int) -> tuple:
    return ("Just", a)


def bind(m: tuple, f) -> tuple:
    # bug: Just を Nothing に変換してしまう (f が呼ばれない)
    if m[0] == "Just":
        return ("Nothing",)
    return m
