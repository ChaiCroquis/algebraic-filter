"""
violation: file read in pure-named function (純粋性違反、 外部状態依存)
expected_detection: custom rule (Phase 1+ AST analysis for open/read)
"""


def calculate_value(x: int) -> float:
    # bug: 'calculate' は pure を示唆するが file read で外部依存
    with open("/tmp/factor.txt", encoding="utf-8") as f:
        factor = float(f.read().strip())
    return x * factor
