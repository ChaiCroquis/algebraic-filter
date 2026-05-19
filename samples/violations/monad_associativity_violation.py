"""
violation: Monad associativity — bind(bind(m, f), g) != bind(m, lambda x: bind(f(x), g))
expected_detection: hypothesis @given associativity
"""


def pure(a: int) -> tuple:
    return ("Just", a)


def bind(m: tuple, f: callable) -> tuple:
    if m[0] == "Just":
        result = f(m[1])
        # bug: bind の都度 +1 = associativity 破綻
        if result[0] == "Just":
            return ("Just", result[1] + 1)
        return result
    return m
