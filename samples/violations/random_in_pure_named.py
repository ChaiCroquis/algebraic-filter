"""
violation: pure-named function が random.random() (時間/外部状態依存)
expected_detection: custom rule (Phase 1+ AST analysis for random module usage)
"""
import random


def calculate(x: int) -> float:
    # bug: 'calculate' は pure (referential transparency) を示唆するが random
    return x * random.random()
