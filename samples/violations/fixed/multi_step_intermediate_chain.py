"""
ground truth (fixed) for multi_step_intermediate_chain
single comprehension で 3 操作 (×2, >0 filter, +1) を fusion
"""


def transform_3_steps(data: list[int]) -> list[int]:
    return [(x * 2) + 1 for x in data if (x * 2) > 0]
