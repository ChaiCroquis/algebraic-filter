"""
violation: SIM300 (yoda-conditions)
expected_detection: ruff --select=SIM
expected_skeleton: variable on left of comparison
expected_fix:
    def check_status(status: int) -> str:
        if status == 0:
            return "ok"
        return "error"
"""


def check_status(status: int) -> str:
    if 0 == status:
        return "ok"
    return "error"
