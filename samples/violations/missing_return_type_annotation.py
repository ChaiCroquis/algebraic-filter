"""
violation: missing return type annotation
expected_detection: ruff --select=ANN (ANN201 missing-return-type-undocumented-public-function)
"""


def double_it(x: int):
    return x * 2
