"""
violation: os.environ access in pure-named function (外部状態依存)
expected_detection: custom rule (Phase 1+ AST analysis for os.environ)
"""
import os


def get_config(key: str) -> str:
    # bug: 'get_config' は pure を示唆するが os.environ で external state 依存
    return os.environ.get(key, "default")
