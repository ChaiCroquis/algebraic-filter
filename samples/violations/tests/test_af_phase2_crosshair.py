"""CrossHair opt-in proof-layer tests (af_phase2/crosshair_bridge.py).

Skipped if crosshair-tool is not installed (it is an optional extra).
Verifies: default OFF = no-op; ON catches a real associativity/commutativity
violation by SMT proof; ON does not false-flag a correct (associative +
commutative) function.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

pytest.importorskip("crosshair", reason="crosshair-tool not installed (optional extra)")

from af_phase2.crosshair_bridge import is_enabled, verify  # noqa: E402


def _sub(a: int, b: int) -> int:
    return a - b


def _add(a: int, b: int) -> int:
    return a + b


def test_crosshair_default_off_is_noop() -> None:
    # isolate from any ambient .algebraic-filter.json (point config at a non-existent file)
    saved_env = os.environ.pop("AF_CROSSHAIR", None)
    saved_cfg = os.environ.get("AF_CONFIG_PATH")
    os.environ["AF_CONFIG_PATH"] = str(REPO_ROOT / "_no_such_config.json")
    try:
        assert is_enabled() is False
        assert verify(_sub) == []
    finally:
        if saved_env is not None:
            os.environ["AF_CROSSHAIR"] = saved_env
        if saved_cfg is None:
            os.environ.pop("AF_CONFIG_PATH", None)
        else:
            os.environ["AF_CONFIG_PATH"] = saved_cfg


def test_crosshair_on_catches_violation() -> None:
    """減算は名前 'sub' では law 推論されないので、 monoid 名でラップして検証."""
    os.environ["AF_CROSSHAIR"] = "1"
    try:
        def my_sum(a: int, b: int) -> int:  # 'sum' -> monoid_associativity 推論
            return a - b

        violations = verify(my_sum)
        assert violations, "CrossHair should prove associativity violation of subtraction"
        assert any("associativity" in v["law_id"] for v in violations)
    finally:
        os.environ.pop("AF_CROSSHAIR", None)


def test_crosshair_on_fp_zero_on_correct() -> None:
    os.environ["AF_CROSSHAIR"] = "1"
    try:
        def my_sum(a: int, b: int) -> int:  # 加算 = 結合的 -> 反例なし
            return a + b

        assert verify(my_sum) == [], "correct addition must not be flagged (FP-zero)"
    finally:
        os.environ.pop("AF_CROSSHAIR", None)


def test_crosshair_proves_identity_violation() -> None:
    """精度 P2-B1: identity を SMT 証明。 結合的だが単位元を破る op を捕捉.

    a+b+1 は結合的 (= assoc は通る) が op(a,0)=a+1 != a で additive identity を破る。
    identity を sampling でなく証明で捕捉できることを固定。
    """
    os.environ["AF_CROSSHAIR"] = "1"
    try:
        def my_sum(a: int, b: int) -> int:  # 'sum' -> monoid_identity 推論、 +1 で単位元違反
            return a + b + 1

        violations = verify(my_sum)
        assert any(v["law_id"] == "monoid_identity" for v in violations), violations
    finally:
        os.environ.pop("AF_CROSSHAIR", None)


def test_crosshair_identity_fp_zero_on_correct_add() -> None:
    """正しい加算は additive identity を満たす -> identity 違反は報告されない (FP-zero)."""
    os.environ["AF_CROSSHAIR"] = "1"
    try:
        def my_sum(a: int, b: int) -> int:
            return a + b

        assert all(v["law_id"] != "monoid_identity" for v in verify(my_sum)), "correct add: no identity FP"
    finally:
        os.environ.pop("AF_CROSSHAIR", None)


def test_crosshair_proves_binary_idempotence_violation() -> None:
    """精度 P2-B2: binary idempotence (op(a,a)==a) を SMT 証明。 宣言経由で検証."""
    from af_phase2.inferrer import law

    os.environ["AF_CROSSHAIR"] = "1"
    try:
        @law("idempotence")
        def combine(a: int, b: int) -> int:
            return a + b  # op(a,a)=2a != a (a!=0) -> 非冪等

        violations = verify(combine)
        assert any(v["law_id"] == "idempotence" for v in violations), violations
    finally:
        os.environ.pop("AF_CROSSHAIR", None)


def test_crosshair_binary_idempotence_fp_zero() -> None:
    """冪等な binary op (max) は flag されない (FP-zero)."""
    from af_phase2.inferrer import law

    os.environ["AF_CROSSHAIR"] = "1"
    try:
        @law("idempotence")
        def mymax(a: int, b: int) -> int:
            return max(a, b)  # op(a,a)=a -> 冪等

        assert all(v["law_id"] != "idempotence" for v in verify(mymax)), "idempotent max: no FP"
    finally:
        os.environ.pop("AF_CROSSHAIR", None)


def test_crosshair_agrees_with_exhaustive_oracle() -> None:
    """非チェリーピック: CrossHair の commutativity 判定が独立 oracle (全数) と一致.

    正しい演算 (add) と非可換演算 (sub / left-biased) の集合で、 CrossHair と
    exhaustive_verify (別経路の決定論検査) の verdict が全件一致することを固定。
    1 関数の手書きでなく、 正/誤両方を含む集合で照合 = favorable でない。
    """
    from af_phase2.exhaustive import exhaustive_verify
    from af_phase2.inferrer import law

    os.environ["AF_CROSSHAIR"] = "1"
    try:
        @law("commutativity")
        def op_add(a: int, b: int) -> int:
            return a + b

        @law("commutativity")
        def op_sub(a: int, b: int) -> int:
            return a - b

        @law("commutativity")
        def op_left(a: int, b: int) -> int:
            return a

        for f in (op_add, op_sub, op_left):
            ch = any(v["law_id"] == "commutativity" for v in verify(f))
            oracle = exhaustive_verify(f, "commutativity") is not None
            assert ch == oracle, f"{f.__name__}: CrossHair={ch} oracle={oracle}"
    finally:
        os.environ.pop("AF_CROSSHAIR", None)
