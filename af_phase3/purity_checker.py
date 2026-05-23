"""決定論拡張 D4: 純粋性 / 決定性の静的検証 (AST のみ、 実行なし).

純粋性は代数法則推論の前提 (副作用や非決定要素があると法則の検証は不健全になりうる)。
本 checker は **実行せず** AST だけで一次的な不純シグナルを検出する:
  - global / nonlocal 文 (外部状態の書込)
  - I/O 呼び出し (print / input / open)
  - 非決定モジュール呼び出し (random / secrets 全般、 time.time/sleep、
    datetime.now/today/utcnow、 uuid.uuid1/uuid4、 os.urandom)

検出ゼロ = 「一次的な不純シグナルなし」 = その範囲では決定論的・参照透過と *保証* できる
(= 決定論領域の拡張、 opt-in 不要のデフォルト static 解析)。

保守的・健全 (sound) だが完全 (complete) ではない: 別の不純関数の呼び出しや引数の
in-place 変更までは追えない (= 一次シグナルのみ。 limitations に明記)。
"""
from __future__ import annotations

import ast
from typing import NamedTuple


class PurityFinding(NamedTuple):
    kind: str  # "global" / "nonlocal" / "io" / "nondeterminism"
    name: str
    line: int


_IO_FUNCS = {"print", "input", "open"}
_NONDET_MODULES_ALL = {"random", "secrets"}  # モジュール全体が非決定
_NONDET_CALLS = {
    ("time", "time"),
    ("time", "sleep"),
    ("time", "monotonic"),
    ("time", "perf_counter"),
    ("datetime", "now"),
    ("datetime", "today"),
    ("datetime", "utcnow"),
    ("uuid", "uuid1"),
    ("uuid", "uuid4"),
    ("os", "urandom"),
}


def _root_name(node: ast.expr) -> str | None:
    """属性チェーンの根の Name を返す (`datetime.datetime.now` -> "datetime")."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _call_finding(node: ast.Call) -> PurityFinding | None:
    func = node.func
    if isinstance(func, ast.Name) and func.id in _IO_FUNCS:
        return PurityFinding("io", func.id, node.lineno)
    if isinstance(func, ast.Attribute):
        root = _root_name(func)
        if root is not None and (root in _NONDET_MODULES_ALL or (root, func.attr) in _NONDET_CALLS):
            return PurityFinding("nondeterminism", f"{root}.{func.attr}", node.lineno)
    return None


def check_purity(source: str) -> list[PurityFinding]:
    """source の一次的な不純/非決定シグナルを返す. 空 = 一次シグナルなし (= 純粋と保証)."""
    tree = ast.parse(source)
    findings: list[PurityFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Global):
            findings.extend(PurityFinding("global", n, node.lineno) for n in node.names)
        elif isinstance(node, ast.Nonlocal):
            findings.extend(PurityFinding("nonlocal", n, node.lineno) for n in node.names)
        elif isinstance(node, ast.Call):
            found = _call_finding(node)
            if found is not None:
                findings.append(found)
    return findings


def check_purity_file(path: str) -> list[PurityFinding]:
    with open(path, encoding="utf-8") as f:
        return check_purity(f.read())


def is_pure(source: str) -> bool:
    """一次的な不純シグナルが無ければ True (保守的・健全な決定論保証)."""
    return not check_purity(source)
