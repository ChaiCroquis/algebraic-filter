"""
violation: Monad right identity — bind(m, pure) != m
expected_detection: hypothesis @given (bind(pure(a), pure) == pure(a))
expected_fix: bind が pure に対し m を変えない
"""


def pure(a: int) -> tuple:
    return ("Just", a)


def bind(m: tuple, f: callable) -> tuple:
    if m[0] == "Just":
        result = f(m[1])
        # bug: pure 適用後の Just を Different に変換 → right identity 破綻
        if result[0] == "Just":
            return ("Different", result[1])
        return result
    return m
