"""ground truth (fixed) for intersect_commutativity_violation — sorted set で order-independent"""


def intersect(a: list[int], b: list[int]) -> list[int]:
    return sorted(set(a) & set(b))
