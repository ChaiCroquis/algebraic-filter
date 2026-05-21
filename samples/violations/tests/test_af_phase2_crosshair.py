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
