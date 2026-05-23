"""Phase 2 精度 P1: 法則「宣言」 (@law / @no_law) の検証テスト.

名前 heuristic の両側エラーを、 宣言の検証で根治することを固定:
  - FP 根治: 意図的に非可換な merge を @no_law で宣言 → flag されない
  - FN 改善: 非認識名 thingy に @law("commutativity") 宣言 + 違反 → flag される
  - 優先: 宣言は名前推測を上書きする
  - 後方互換: 未宣言は従来の名前 heuristic

実行: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase2_declared_laws.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase2.generator import auto_test  # noqa: E402
from af_phase2.inferrer import infer_laws, law, no_law  # noqa: E402


def _fails(func) -> list:  # noqa: ANN001
    return [r for r in auto_test(func) if r.status in ("FAIL", "ERROR")]


def test_declared_law_takes_priority_over_name() -> None:
    """宣言は名前推測を上書きする (total という名でも宣言した commutativity を採用)."""

    @law("commutativity")
    def total(a: int, b: int) -> int:
        return a + b

    assert infer_laws(total) == ["commutativity"], infer_laws(total)


def test_no_law_suppresses_name_heuristic_false_positive() -> None:
    """FP 根治: 意図的に非可換な merge を @no_law 宣言 → 法則ゼロ → flag されない."""

    @no_law
    def merge(a: int, b: int) -> int:
        return a  # 左優先 = 意図的に非可換

    assert infer_laws(merge) == []
    assert _fails(merge) == [], f"@no_law merge must not be flagged, got {_fails(merge)}"


def test_declared_law_on_unrecognized_name_catches_violation() -> None:
    """FN 改善: 非認識名でも宣言した法則の違反は検出される."""

    @law("commutativity")
    def thingy(a: int, b: int) -> int:
        return a - b  # 非可換

    assert "commutativity" in infer_laws(thingy)
    assert _fails(thingy), "declared-commutativity violation on unrecognized name must be flagged"


def test_declared_correct_function_passes() -> None:
    """正しく宣言通り (可換) の関数は flag されない."""

    @law("commutativity")
    def combine(a: int, b: int) -> int:
        return a + b

    assert _fails(combine) == [], f"correct declared-commutative func must pass, got {_fails(combine)}"


def test_undeclared_falls_back_to_name_heuristic() -> None:
    """後方互換: 未宣言は従来の名前 heuristic (total -> monoid)."""

    def total(xs: list[int]) -> int:
        return sum(xs)

    assert "monoid_identity" in infer_laws(total), infer_laws(total)
