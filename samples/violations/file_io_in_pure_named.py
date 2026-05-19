"""
violation: pure-named function が file I/O (純粋性違反)
expected_detection: custom rule (Phase 1+ AST analysis for open/write)
"""


def transform(x: int) -> int:
    # bug: 'transform' は pure を示唆するが file write
    with open("/tmp/log.txt", "a", encoding="utf-8") as f:
        f.write(f"transform({x})\n")
    return x * 2
