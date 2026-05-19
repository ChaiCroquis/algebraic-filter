"""
violation: PERF401 (manual-list-comprehension)
expected_detection: ruff --select=PERF
expected_skeleton: list comprehension
expected_fix:
    def double_positives(data: list[int]) -> list[int]:
        return [x * 2 for x in data if x > 0]
"""


def double_positives(data: list[int]) -> list[int]:
    result = []
    for x in data:
        if x > 0:
            result.append(x * 2)
    return result
