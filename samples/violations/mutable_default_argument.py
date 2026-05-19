"""
violation: mutable default argument (ruff B006)
expected_detection: ruff --select=B (B006 function-call-in-default-argument)
expected_fix: default を None にして関数内で None check
"""


def add_item(item: int, items: list = []) -> list:
    # bug: 同じ default list を全 caller で共有 → 蓄積バグ
    items.append(item)
    return items
