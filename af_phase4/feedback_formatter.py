"""Phase 4: 構造化 LLM フィードバック整形.

input: ruff raw output (Phase 1) + Phase 3 StaticViolation list
output: 統一 schema の構造化 dict list
  {violation_location, violation_law, alternative_skeleton, fix_example, layer}

Phase 1 (ruff) と Phase 3 (AST) の異なる layer の violation を同 schema に揃え、
hook の additionalContext で Claude に投げる payload を一元化する.
"""
from __future__ import annotations

import re
from typing import Any


_RUFF_SKELETON: dict[str, str] = {
    "PERF401": "list comprehension",
    "SIM103": "direct boolean return",
    "SIM108": "ternary expression",
    "SIM115": "with-open context manager",
    "SIM118": "in dict (not in dict.keys())",
    "SIM300": "variable on left of comparison",
    "ANN001": "explicit type annotation for argument",
    "ANN201": "explicit return type annotation",
    "ANN401": "specific type (not Any)",
    "F401": "remove unused import",
    "UP006": "builtin generic (list / dict / tuple)",
    "UP015": "default open mode (omit 'r')",
    "B006": "None default + conditional init",
    "B007": "underscore for unused loop variable",
    "C416": "list(iterable) (not [x for x in iterable])",
    "RUF013": "explicit Optional (str | None)",
    "PERF203": "try/except outside loop",
}

_RUFF_FIX: dict[str, str] = {
    "PERF401": "[x * 2 for x in data if x > 0]",
    "SIM103": "return x > 0",
    "SIM108": "return 'ok' if condition else 'error'",
    "SIM115": "with open(path) as f: ...",
    "SIM118": "k in d",
    "SIM300": "if status == 0:",
    "ANN001": "def add(x: int, y: int) -> int: ...",
    "ANN201": "def double_it(x: int) -> int: ...",
    "ANN401": "specific type instead of Any",
    "F401": "remove unused import line",
    "UP006": "xs: list[int]",
    "UP015": "open(path)",
    "B006": "items: list | None = None; items = items or []",
    "B007": "for _ in range(n):",
    "C416": "list(iterable)",
    "RUF013": "name: str | None = None",
    "PERF203": "(restructure try/except)",
}

_PHASE3_SKELETON: dict[str, str] = {
    "intermediate-list-chain": "single comprehension or generator chain",
    "dict-keys-list": "direct iter or .items()",
    "explicit-copy": "drop unnecessary .copy() / [:] / list() chain",
    "string-concat-in-loop": "''.join(parts)",
}

_PHASE3_FIX: dict[str, str] = {
    "intermediate-list-chain": "[(x * 2) + 1 for x in data if (x * 2) > 0]",
    "dict-keys-list": "for k, v in d.items(): ...",
    "explicit-copy": "(omit redundant copies)",
    "string-concat-in-loop": "return ''.join(parts)",
}


def format_ruff_violations(ruff_output: str, file_path: str) -> list[dict[str, Any]]:
    """ruff raw output → 構造化 violation list (layer='Phase 1 ruff')."""
    violations: list[dict[str, Any]] = []
    lines = ruff_output.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Z]+\d+)\s+(.+)$", lines[i])
        if m:
            rule_id = m.group(1)
            message = m.group(2)
            location = f"{file_path}:?"
            # 次行に "--> path:line:col" あれば location 抽出
            if i + 1 < len(lines):
                loc_m = re.match(r"^\s+-->\s+(.+?):(\d+):(\d+)", lines[i + 1])
                if loc_m:
                    location = f"{loc_m.group(1)}:{loc_m.group(2)}"
            violations.append(
                {
                    "layer": "Phase 1 ruff",
                    "violation_location": location,
                    "violation_law": rule_id,
                    "violation_message": message,
                    "alternative_skeleton": _RUFF_SKELETON.get(rule_id, "(see ruff suggestion)"),
                    "fix_example": _RUFF_FIX.get(rule_id, "(consult ruff help)"),
                }
            )
        i += 1
    return violations


def format_phase3_violations(
    phase3_violations: list, file_path: str
) -> list[dict[str, Any]]:
    """Phase 3 StaticViolation list → 構造化 violation list (layer='Phase 3 AST')."""
    result: list[dict[str, Any]] = []
    for v in phase3_violations:
        result.append(
            {
                "layer": "Phase 3 AST",
                "violation_location": f"{file_path}:{v.line}",
                "violation_law": v.rule_id,
                "violation_message": v.message,
                "alternative_skeleton": _PHASE3_SKELETON.get(
                    v.rule_id, "(see Phase 3 advice)"
                ),
                "fix_example": _PHASE3_FIX.get(v.rule_id, ""),
            }
        )
    return result


def combine_violations(
    ruff_output: str,
    phase3_violations: list,
    file_path: str,
) -> list[dict[str, Any]]:
    """Phase 1 + Phase 3 violation を統一 schema の 1 list に集約."""
    return format_ruff_violations(ruff_output, file_path) + format_phase3_violations(
        phase3_violations, file_path
    )
