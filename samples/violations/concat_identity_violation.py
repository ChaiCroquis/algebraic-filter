"""
violation: Monoid identity for string concat — '' is identity, but PREFIX always added
expected_detection: hypothesis @given (my_concat('', xs) == ''.join(xs))
"""


def my_concat(prefix: str, xs: list[str]) -> str:
    # bug: 常に "PREFIX_" を付加 → identity (prefix='') で成立せず
    return "PREFIX_" + prefix + "".join(xs)
