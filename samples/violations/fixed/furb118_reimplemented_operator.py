"""ground truth (fixed) for furb118_reimplemented_operator"""
from operator import itemgetter


def get_firsts(pairs: list[tuple[int, int]]) -> list[int]:
    return list(map(itemgetter(0), pairs))
