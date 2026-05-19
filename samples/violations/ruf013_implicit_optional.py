"""
violation: RUF013 — implicit Optional (PEP 484 deprecated)
expected_detection: ruff --select=RUF (RUF013)
"""


def greet(name: str = None) -> str:
    return f"hello {name or 'world'}"
