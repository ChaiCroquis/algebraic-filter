"""
violation: Maybe Functor unit law — fmap(f, pure(a)) != pure(f(a))
expected_detection: hypothesis @given Functor unit law
"""


def pure(a: int) -> tuple:
    return ("Just", a)


def fmap(f: callable, m: tuple) -> tuple:
    if m[0] == "Just":
        # bug: f 適用結果を ignore して 0 で上書き
        return ("Just", 0)
    return m
