"""
violation: SIM103 (needless-bool)
expected_detection: ruff --select=SIM
expected_skeleton: direct return of boolean expression
expected_fix:
    def is_positive(x: int) -> bool:
        return x > 0
"""


def is_positive(x: int) -> bool:
    if x > 0:
        return True
    else:
        return False
