"""
violation: UP015 — redundant open modes (open(..., 'r') is default)
expected_detection: ruff --select=UP (UP015)
"""


def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()
