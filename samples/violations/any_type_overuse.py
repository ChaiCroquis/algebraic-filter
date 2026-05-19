"""
violation: Any type overuse (ruff ANN401)
expected_detection: ruff --select=ANN (ANN401 any-type)
"""
from typing import Any


def process(data: Any) -> Any:
    return data
