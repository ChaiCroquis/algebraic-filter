"""
violation: Functor compose law violation — fmap(f . g, xs) != fmap(f, fmap(g, xs))
expected_detection: hypothesis @given Functor compose law
expected_fix:
    def my_map(f, xs): return [f(x) for x in xs]
"""


def my_map(f: callable, xs: list[int]) -> list[int]:
    # bug: f を 2 回適用してしまう → Functor compose law 破綻
    return [f(f(x)) for x in xs]
