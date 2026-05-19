"""
violation: time.time() in pure-named function (時間依存 = 非決定的)
expected_detection: custom rule (Phase 1+ AST analysis for time module)
"""
import time


def compute_value(x: int) -> float:
    # bug: 'compute_value' は pure を示唆するが time に依存
    return x + time.time()
