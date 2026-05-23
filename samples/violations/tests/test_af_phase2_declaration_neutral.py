"""Phase 2 精度 P1 の *非チェリーピック* 検証 (#39-42).

問題: declared-laws の単体テストは「手書きの宣言済み関数」 = favorable で、 mechanism が
動く証明にはなるが「デフォルト挙動が改善した」証明にはならない (= +80% と同型の罠)。

本テストはそれを正す:
  1. ground truth は **独立 oracle** (全数 commutativity 検査) で確立 — fiat で決めない。
  2. **デフォルトの失敗 (FP/FN) と opt-in 宣言の修正を *対で*** 検証 — デフォルトを隠さない。
  3. 演算は canonical (左/右優先 merge・減算・加算) — hand-tune した exotic でない。

結論として固定する honest な事実:
  - デフォルト (宣言なし): 名前推測ゆえ FP (非可換 merge) と FN (非認識名の違反) が残る。
  - opt-in (@law / @no_law): 宣言した関数でのみ両者が閉じる。

実行: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase2_declaration_neutral.py -v
"""
from __future__ import annotations

import itertools
import operator
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase2.generator import auto_test  # noqa: E402
from af_phase2.inferrer import infer_laws, law, no_law  # noqa: E402

_DOMAIN = range(-4, 5)


def _is_commutative(func: Callable[[int, int], int]) -> bool:
    """独立 oracle: 全数での commutativity (AF とは別経路の ground truth)."""
    return all(func(a, b) == func(b, a) for a, b in itertools.product(_DOMAIN, repeat=2))


def _af_flags_commutativity(func: Callable[[int, int], int]) -> bool:
    return any(
        r.law_id == "commutativity" and r.status in ("FAIL", "ERROR")
        for r in auto_test(func)
    )


def test_oracle_self_consistency() -> None:
    """oracle 自身が canonical 演算で正しい (fiat でなく検査で commutativity を決める)."""
    assert _is_commutative(operator.add) is True
    assert _is_commutative(operator.mul) is True
    assert _is_commutative(operator.sub) is False


def test_default_merge_false_positive_is_real() -> None:
    """デフォルト (宣言なし): 真に非可換な merge を FP として flag する (= 既定の問題)."""

    def merge(a: int, b: int) -> int:
        return a  # 左優先 = 真に非可換 (oracle で確認)

    assert _is_commutative(merge) is False  # 独立 oracle: 非可換
    assert _af_flags_commutativity(merge) is True  # 既定: 名前推測で FP が出る


def test_no_law_fixes_merge_false_positive() -> None:
    """opt-in: @no_law で同種の非可換 merge の FP が消える (デフォルトでなく宣言で)."""

    @no_law
    def merge(a: int, b: int) -> int:
        return a

    assert _af_flags_commutativity(merge) is False


def test_default_unrecognized_name_false_negative_is_real() -> None:
    """デフォルト (宣言なし・非認識名): 真の違反を見逃す (= 既定の問題)."""

    def doit(a: int, b: int) -> int:
        return a - b  # 非可換 (oracle で確認)

    assert _is_commutative(doit) is False  # 独立 oracle: 非可換
    assert infer_laws(doit) == []  # 名前推論ゼロ
    assert _af_flags_commutativity(doit) is False  # 既定: 見逃す (FN)


def test_law_declaration_fixes_false_negative() -> None:
    """opt-in: @law で非認識名の違反を捕捉 (デフォルトでなく宣言で)."""

    @law("commutativity")
    def doit(a: int, b: int) -> int:
        return a - b

    assert _af_flags_commutativity(doit) is True


def test_declared_correct_function_not_flagged() -> None:
    """opt-in が過剰検出しない: 宣言通り可換なら flag しない (oracle で可換を確認)."""

    @law("commutativity")
    def combine(a: int, b: int) -> int:
        return a + b

    assert _is_commutative(combine) is True
    assert _af_flags_commutativity(combine) is False
