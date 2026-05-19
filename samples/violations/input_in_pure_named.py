"""
violation: input() in pure-named function (user-interactive、 純粋性違反)
expected_detection: custom rule (Phase 1+ AST analysis for builtin input)
"""


def compute_result(x: int) -> int:
    # bug: 'compute_result' は pure を示唆するが input で対話的依存
    factor = int(input("factor: "))
    return x * factor
