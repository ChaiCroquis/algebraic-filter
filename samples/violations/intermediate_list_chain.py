"""
violation: intermediate list materialization (data movement waste)
expected_detection: ruff (PERF) for the explicit list() wraps / memray for object count (Phase 3)
expected_skeleton: single comprehension or generator chain
expected_fix:
    def transform(data: list[int]) -> list[int]:
        return [x * 2 for x in data if x > 0]
"""


def transform(data: list[int]) -> list[int]:
    # two intermediate lists materialized: list(map(...)) and list(filter(...))
    return list(filter(lambda x: x > 0, list(map(lambda x: x * 2, data))))
