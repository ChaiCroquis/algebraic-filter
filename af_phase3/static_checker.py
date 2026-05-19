"""AF Phase 3 — 静的 AST checker for data movement violations.

ruff の標準 PERF/SIM ルールでは検出されない pattern を AF 独自 contribution として捕捉:
  - intermediate-list-chain: list(filter(..., list(map(..., data))))
  - dict-keys-list: list(d.keys()) / list(d.values())
  - explicit-copy: data.copy() の繰り返し
  - string-concat-in-loop: for body 内の `s += ...` accumulation
"""
from __future__ import annotations

import ast
from typing import NamedTuple


class StaticViolation(NamedTuple):
    rule_id: str
    line: int
    message: str


def check_source(source: str) -> list[StaticViolation]:
    """Python source code を parse → data movement violation を検出."""
    tree = ast.parse(source)
    visitor = _DataMovementVisitor()
    visitor.visit(tree)
    return visitor.violations


def check_file(path: str) -> list[StaticViolation]:
    """指定 path の Python file を check."""
    with open(path, encoding="utf-8") as f:
        source = f.read()
    return check_source(source)


class _DataMovementVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[StaticViolation] = []
        self._in_for_loop = 0
        self._for_loop_target: str | None = None

    def visit_Call(self, node: ast.Call) -> None:
        self._check_intermediate_list_chain(node)
        self._check_dict_keys_list(node)
        self._check_explicit_copy(node)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._in_for_loop += 1
        prev_target = self._for_loop_target
        if isinstance(node.target, ast.Name):
            self._for_loop_target = node.target.id
        for stmt in node.body:
            self._check_string_concat_in_loop(stmt)
        self.generic_visit(node)
        self._for_loop_target = prev_target
        self._in_for_loop -= 1

    def _check_intermediate_list_chain(self, node: ast.Call) -> None:
        if not _is_call_to(node, "list"):
            return
        if not node.args:
            return
        inner = node.args[0]
        # list(map(..., ...)) or list(filter(..., ...)) で 2 番目引数が更に list(...)
        if isinstance(inner, ast.Call) and _is_call_to(inner, ("map", "filter")):
            if len(inner.args) >= 2 and isinstance(inner.args[1], ast.Call):
                inner_inner = inner.args[1]
                if _is_call_to(inner_inner, "list"):
                    self.violations.append(
                        StaticViolation(
                            "intermediate-list-chain",
                            node.lineno,
                            f"line {node.lineno}: list({inner.func.id}(..., list(...))) chain — "
                            "single comprehension or generator expression に置換可能",
                        )
                    )

    def _check_dict_keys_list(self, node: ast.Call) -> None:
        if not _is_call_to(node, "list"):
            return
        if not node.args:
            return
        inner = node.args[0]
        if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute):
            if inner.func.attr in ("keys", "values"):
                self.violations.append(
                    StaticViolation(
                        "dict-keys-list",
                        node.lineno,
                        f"line {node.lineno}: list(d.{inner.func.attr}()) — "
                        "直接 iter or items() で十分、 中間 list は不要",
                    )
                )

    def _check_explicit_copy(self, node: ast.Call) -> None:
        # x.copy() pattern
        if isinstance(node.func, ast.Attribute) and node.func.attr == "copy":
            self.violations.append(
                StaticViolation(
                    "explicit-copy",
                    node.lineno,
                    f"line {node.lineno}: .copy() — 必要性を確認 (Stream Fusion 観点で省略可能な場合)",
                )
            )

    def _check_string_concat_in_loop(self, stmt: ast.stmt) -> None:
        # for-body 内で `result += x` パターン (string concat assumption)
        if not isinstance(stmt, ast.AugAssign):
            return
        if not isinstance(stmt.op, ast.Add):
            return
        if not isinstance(stmt.target, ast.Name):
            return
        self.violations.append(
            StaticViolation(
                "string-concat-in-loop",
                stmt.lineno,
                f"line {stmt.lineno}: for body 内の {stmt.target.id} += ... — "
                "string なら ''.join、 list なら extend or comprehension 推奨",
            )
        )


def _is_call_to(node: ast.Call, name) -> bool:
    if not isinstance(node.func, ast.Name):
        return False
    if isinstance(name, str):
        return node.func.id == name
    return node.func.id in name
