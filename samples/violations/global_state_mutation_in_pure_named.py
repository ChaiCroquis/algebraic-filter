"""
violation: pure-named function が global state mutation
expected_detection: custom rule (Phase 1+) AST analysis or CrossHair @pure contract
expected_fix: pure function (no global mutation)
"""


_counter = 0


def compute(x: int) -> int:
    # bug: 関数名 'compute' は pure を示唆するが global 変数を mutation
    global _counter
    _counter += 1
    return x * 2
