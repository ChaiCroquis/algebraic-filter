"""
violation: Functor const law violation — fmap(const(k), xs) != [k] * len(xs)
expected_detection: hypothesis @given (my_map(lambda _: k, xs) == [k]*len(xs))
"""


def my_map(f: callable, xs: list[int]) -> list[int]:
    # bug: const function を渡しても結果が input と混ざる
    return [f(x) + x for x in xs]
