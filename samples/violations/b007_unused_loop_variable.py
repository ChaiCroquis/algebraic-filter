"""
violation: B007 — unused loop variable
expected_detection: ruff --select=B (B007)
"""


def repeat_action(n: int) -> list[int]:
    result = []
    for i in range(n):
        result.append(42)
    return result
