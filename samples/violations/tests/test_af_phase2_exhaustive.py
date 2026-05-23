"""Phase 2 精度 P3-C1: 小有限ドメイン exhaustive 検証のテスト.

サンプリングでなく全数列挙 = その有限域での決定論保証 (取りこぼしなし・再現可能)。

実行: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase2_exhaustive.py -v
"""
from __future__ import annotations

import operator
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase2.exhaustive import complete_domain, exhaustive_verify  # noqa: E402

_BOOL = (False, True)


def test_exhaustive_catches_commutativity_violation() -> None:
    assert exhaustive_verify(operator.sub, "commutativity") is not None


def test_exhaustive_passes_commutative() -> None:
    assert exhaustive_verify(operator.add, "commutativity") is None


def test_exhaustive_catches_associativity_violation() -> None:
    assert exhaustive_verify(operator.sub, "monoid_associativity") is not None


def test_exhaustive_passes_associative() -> None:
    assert exhaustive_verify(operator.add, "monoid_associativity") is None


def test_exhaustive_idempotence() -> None:
    assert exhaustive_verify(operator.add, "idempotence") is not None  # a+a=2a != a
    assert exhaustive_verify(max, "idempotence") is None  # max(a,a)=a


def test_exhaustive_additive_identity() -> None:
    assert exhaustive_verify(operator.add, "monoid_identity") is None  # a+0=a
    assert exhaustive_verify(lambda a, b: a + b + 1, "monoid_identity") is not None


def test_exhaustive_is_deterministic() -> None:
    """全数なので毎回同じ結果 = 決定論 (サンプリングの揺らぎがない)."""
    r1 = exhaustive_verify(operator.sub, "commutativity")
    r2 = exhaustive_verify(operator.sub, "commutativity")
    assert r1 == r2 and r1 is not None


# --- D2: bool/有限型は完全ドメインで *完全証明* (有界でなく打ち切りなし) ---


def test_complete_domain_detects_bool_only() -> None:
    """complete_domain は bool 注釈の関数に (False, True)、 int には None."""

    def boolop(a: bool, b: bool) -> bool:
        return a and b

    def intop(a: int, b: int) -> int:
        return a + b

    assert complete_domain(boolop) == _BOOL
    assert complete_domain(intop) is None


def test_bool_commutativity_complete_proof() -> None:
    """bool 全 4 通り = 型全体を尽くす完全証明 (and は可換、 非対称 op は反証)."""

    def myand(a: bool, b: bool) -> bool:
        return a and b

    def asym(a: bool, b: bool) -> bool:
        return a and not b

    assert exhaustive_verify(myand, "commutativity", domain=_BOOL) is None
    assert exhaustive_verify(asym, "commutativity", domain=_BOOL) is not None


def test_bool_idempotence_complete_proof() -> None:
    """bool 完全証明: or は冪等 (a or a == a)、 xor は非冪等 (True^True=False)."""

    def myor(a: bool, b: bool) -> bool:
        return a or b

    def xor(a: bool, b: bool) -> bool:
        return a != b

    assert exhaustive_verify(myor, "idempotence", domain=_BOOL) is None
    assert exhaustive_verify(xor, "idempotence", domain=_BOOL) is not None


def test_bool_complete_domain_drives_verification() -> None:
    """complete_domain で取得した完全ドメインで検証する統合 (有限型→完全証明の経路)."""

    def myand(a: bool, b: bool) -> bool:
        return a and b

    dom = complete_domain(myand)
    assert dom is not None
    assert exhaustive_verify(myand, "commutativity", domain=dom) is None
