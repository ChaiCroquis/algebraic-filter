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


# Phase 2: 代数法則 violation (= af_phase2 経由で hypothesis が検出した法則違反)
# law_id は af_phase2.law_templates.LAW_REGISTRY の key と一致する
_PHASE2_SKELETON: dict[str, str] = {
    "monoid_identity": "ensure identity element: f(x, identity) == x AND f(identity, x) == x",
    "monoid_associativity": "ensure (a `op` b) `op` c == a `op` (b `op` c)",
    "semigroup_associativity": "ensure (a `op` b) `op` c == a `op` (b `op` c)",
    "functor_identity": "fmap(id, x) == x (identity preservation)",
    "functor_compose": "fmap(f . g, x) == fmap(f, fmap(g, x))",
    "foldable_foldl_foldr": "foldl and foldr equivalent for commutative monoids",
    "monad_left_identity": "return(a).bind(f) == f(a)",
    "monad_right_identity": "m.bind(return) == m",
    "monad_associativity": "(m.bind(f)).bind(g) == m.bind(lambda x: f(x).bind(g))",
    "eq_reflexivity": "x == x for all x",
    "eq_symmetry": "(a == b) implies (b == a)",
    "commutativity": "f(a, b) == f(b, a)",
    "idempotence_state_int": "f(f(x)) == f(x)",
    "idempotence_class": "obj.method(); obj.method() leaves state equal to single call",
}

_PHASE2_FIX: dict[str, str] = {
    "monoid_identity": "def add(x, y): return x + y  # identity = 0",
    "monoid_associativity": "use a + b + c form (not (a - b) + c which breaks)",
    "semigroup_associativity": "use ''.join(strs) for string concat (associative)",
    "functor_identity": "fmap(lambda x: x, container) must return container",
    "functor_compose": "fmap(compose(f, g), x) == fmap(f, fmap(g, x))",
    "foldable_foldl_foldr": "use sum / functools.reduce with commutative op",
    "monad_left_identity": "Just(a).bind(f) must equal f(a)",
    "monad_right_identity": "m.bind(lambda x: Just(x)) must equal m",
    "monad_associativity": "chain .bind() calls left-to-right preserve equivalence",
    "eq_reflexivity": "obj == obj must be True",
    "eq_symmetry": "(a == b) == (b == a)",
    "commutativity": "def avg(a, b): return (a + b) / 2  (not (a - b) / 2)",
    "idempotence_state_int": "def normalize(x): return abs(x)  # abs(abs(x)) == abs(x)",
    "idempotence_class": "def mark_processed(self): self.processed = True  # repeat-safe",
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
    return [
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
        for v in phase3_violations
    ]


def format_phase2_violations(
    phase2_failures: list[dict[str, Any]], file_path: str
) -> list[dict[str, Any]]:
    """Phase 2 代数法則 failure list → 構造化 violation list (layer='Phase 2 algebraic-law').

    入力 phase2_failures は dict list で、 各 dict は次の field を持つ:
        - law_id: af_phase2.law_templates.LAW_REGISTRY の key (= 法則名)
        - function_name: 違反検出した関数名
        - counter_example: hypothesis が見つけた反例 (= optional、 articulate 用)
        - line: 関数定義行 (= optional、 ない場合 '?' を補う)

    Phase 2 違反を Phase 4 統一 schema に整合させ、 Claude の修正サイクルに
    Layer 1 / Layer 3 と同様の構造で feedback 投入する。
    """
    result: list[dict[str, Any]] = []
    for f in phase2_failures:
        law_id = f.get("law_id", "")
        function_name = f.get("function_name", "?")
        line = f.get("line", "?")
        counter_example = f.get("counter_example", "")
        message = (
            f"function `{function_name}` violates {law_id}"
            + (f" (counter-example: {counter_example})" if counter_example else "")
        )
        result.append(
            {
                "layer": "Phase 2 algebraic-law",
                "violation_location": f"{file_path}:{line}",
                "violation_law": law_id,
                "violation_message": message,
                "alternative_skeleton": _PHASE2_SKELETON.get(
                    law_id, "(see Phase 2 law_templates.py)"
                ),
                "fix_example": _PHASE2_FIX.get(law_id, ""),
            }
        )
    return result


def combine_violations(
    ruff_output: str,
    phase3_violations: list,
    file_path: str,
    phase2_failures: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Phase 1 + Phase 2 + Phase 3 violation を統一 schema の 1 list に集約.

    phase2_failures = None の場合 (= 既定) は Phase 1 + Phase 3 のみ (= v0.1.0 互換)。
    phase2_failures = [...] の場合は Phase 2 結果も統合 (= Phase 4 拡張 schema)。
    """
    parts = (
        format_ruff_violations(ruff_output, file_path)
        + format_phase3_violations(phase3_violations, file_path)
    )
    if phase2_failures:
        parts += format_phase2_violations(phase2_failures, file_path)
    return parts
