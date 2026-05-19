"""ground truth (fixed) for b007_unused_loop_variable — list comprehension で _ 不要化"""


def repeat_action(n: int) -> list[int]:
    return [42 for _ in range(n)]
