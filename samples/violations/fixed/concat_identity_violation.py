"""ground truth (fixed) for concat_identity_violation"""


def my_concat(prefix: str, xs: list[str]) -> str:
    return prefix + "".join(xs)
