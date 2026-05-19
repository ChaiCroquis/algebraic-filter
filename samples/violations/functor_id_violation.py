"""
violation: Functor identity law violation — fmap(id, xs) != xs
expected_detection: hypothesis @given (Functor identity: my_map(lambda x: x, xs) == xs)
expected_skeleton: standard map without extra transform
expected_fix:
    def my_map(f, xs: list[float]) -> list[float]:
        return [f(x) for x in xs]
"""


def my_map(f, xs: list[float]) -> list[float]:
    # naming suggests Functor structure (fmap), but adds 0.0001 even when f == id
    # Functor identity law violated: my_map(lambda x: x, xs) != xs
    return [f(x) + 0.0001 for x in xs]
