"""
violation: SIM118 — use 'in dict' instead of 'in dict.keys()'
expected_detection: ruff --select=SIM (SIM118)
"""


def has_key(d: dict[str, int], k: str) -> bool:
    return k in d.keys()
