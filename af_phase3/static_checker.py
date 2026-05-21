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
        # names with AST-local evidence of being str (for string-concat-in-loop
        # precision — avoids flagging int/float accumulators as concat). Scoped
        # per function via visit_FunctionDef.
        self._string_names: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        self._check_intermediate_list_chain(node)
        self._check_dict_keys_list(node)
        self._check_explicit_copy(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_scoped(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_scoped(node)

    def _visit_scoped(self, node: ast.AST) -> None:
        prev = self._string_names
        self._string_names = _collect_string_names(node)
        self.generic_visit(node)
        self._string_names = prev

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
        if not (isinstance(inner, ast.Call) and _is_call_to(inner, ("map", "filter"))):
            return
        if not (len(inner.args) >= 2 and isinstance(inner.args[1], ast.Call)):
            return
        if not _is_call_to(inner.args[1], "list"):
            return
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
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr in ("keys", "values")
        ):
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
        # for-body 内で `result += x` パターン (string concat)
        if not isinstance(stmt, ast.AugAssign):
            return
        if not isinstance(stmt.op, ast.Add):
            return
        if not isinstance(stmt.target, ast.Name):
            return
        # precision gate: int/float accumulator (`total += i`) を string concat と
        # 誤検出しないよう、 target が str 証跡を持つ or RHS が str 式の時のみ flag。
        # (2026-05-21 perflint 中立 corpus で float accumulator FP を検出 → 追加)
        if not (
            stmt.target.id in self._string_names
            or _is_string_expr(stmt.value, self._string_names)
        ):
            return
        self.violations.append(
            StaticViolation(
                "string-concat-in-loop",
                stmt.lineno,
                f"line {stmt.lineno}: for body 内の {stmt.target.id} += ... — "
                "string なら ''.join、 list なら extend or comprehension 推奨",
            )
        )


def _is_call_to(node: ast.Call, name: str | tuple[str, ...]) -> bool:
    if not isinstance(node.func, ast.Name):
        return False
    if isinstance(name, str):
        return node.func.id == name
    return node.func.id in name


def _is_string_literalish(node: ast.expr) -> bool:
    """str 型を AST だけで強く示唆する式か (literal / f-string / str() / 連結)。"""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    if isinstance(node, ast.JoinedStr):  # f-string
        return True
    if isinstance(node, ast.Call) and _is_call_to(node, "str"):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _is_string_literalish(node.left) or _is_string_literalish(node.right)
    return False


def _is_string_expr(node: ast.expr, string_names: set[str]) -> bool:
    """check 時点で node が str 式か (literalish か、 str 既知の名前か、 その連結)。"""
    if isinstance(node, ast.Name):
        return node.id in string_names
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _is_string_expr(node.left, string_names) or _is_string_expr(
            node.right, string_names
        )
    return _is_string_literalish(node)


def _collect_string_names(scope: ast.AST) -> set[str]:
    """関数 scope 内で str 証跡を持つ変数名を集める (string-concat 精度用)。"""
    names: set[str] = set()
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign) and _is_string_literalish(node.value):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    names.add(tgt.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            ann = node.annotation
            if (isinstance(ann, ast.Name) and ann.id == "str") or (
                node.value is not None and _is_string_literalish(node.value)
            ):
                names.add(node.target.id)
    return names
