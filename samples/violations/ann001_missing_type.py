"""
violation: ANN001 (missing-type-function-argument)
expected_detection: ruff --select=ANN
expected_skeleton: typed function signature
expected_fix:
    def add(x: int, y: int) -> int:
        return x + y
"""


def add(x, y):
    return x + y
