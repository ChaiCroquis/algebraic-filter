"""
ground truth (fixed) for functor_id_violation
expected after-fix: my_map(lambda x: x, xs) == xs for all xs (Functor identity law)
"""


def my_map(f: callable, xs: list[float]) -> list[float]:
    return [f(x) for x in xs]
