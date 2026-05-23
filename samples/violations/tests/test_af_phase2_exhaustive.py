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

from af_phase2.exhaustive import exhaustive_verify  # noqa: E402


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
