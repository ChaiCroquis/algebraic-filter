"""
violation: 3 段以上の中間 list materialization (Stream Fusion 系違反)
expected_detection: tracemalloc (大きな allocation count for line) + 将来 ruff custom rule
expected_skeleton: single comprehension で 3 操作 fusion
"""


def transform_3_steps(data: list[int]) -> list[int]:
    # 3 つの中間 list を materialization
    return list(
        map(
            lambda x: x + 1,
            list(filter(lambda x: x > 0, list(map(lambda x: x * 2, data)))),
        )
    )
