"""決定論拡張 D5: 契約 (事前/事後条件) の CrossHair 証明.

@contract(post=..., pre=...) で宣言した性質を、 代数法則の外で決定論証明できることを固定。
非チェリーピック: 各ケースを独立 oracle (小整数グリッドの brute-force) と verdict 照合し、
成立 / 違反 / pre-guard の 3 形態を網羅。

実行: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase2_contract.py -v
"""
from __future__ import annotations

import itertools
import os
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

pytest.importorskip("crosshair", reason="crosshair-tool not installed (optional extra)")

from af_phase2.crosshair_bridge import verify_contract  # noqa: E402
from af_phase2.inferrer import contract  # noqa: E402


def _ch_violates(func: Callable[[int, int], int]) -> bool:
    return any(v["law_id"] == "contract" for v in verify_contract(func))


def _oracle_violates(
    func: Callable[[int, int], int],
    post: Callable[[int, int, int], bool],
    pre: Callable[[int, int], bool] | None = None,
) -> bool:
    """独立 oracle: 小整数グリッドで post を brute-force (pre が真の入力のみ)."""
    for a, b in itertools.product(range(-6, 7), repeat=2):
        if pre is not None and not pre(a, b):
            continue
        if not post(func(a, b), a, b):
            return True
    return False


def test_contract_post_holds_agrees_with_oracle() -> None:
    """成立する事後条件 (result >= a) は違反なし — CrossHair と oracle 一致."""
    os.environ["AF_CROSSHAIR"] = "1"
    try:
        @contract(post="result >= a")
        def add_abs(a: int, b: int) -> int:
            return a + abs(b)

        ch = _ch_violates(add_abs)
        oracle = _oracle_violates(add_abs, lambda r, a, b: r >= a)
        assert ch == oracle, f"CrossHair={ch} oracle={oracle}"
        assert ch is False
    finally:
        os.environ.pop("AF_CROSSHAIR", None)


def test_contract_post_violation_agrees_with_oracle() -> None:
    """破れる事後条件 (a+b >= a は b<0 で偽) は違反検出 — CrossHair と oracle 一致."""
    os.environ["AF_CROSSHAIR"] = "1"
    try:
        @contract(post="result >= a")
        def add(a: int, b: int) -> int:
            return a + b

        ch = _ch_violates(add)
        oracle = _oracle_violates(add, lambda r, a, b: r >= a)
        assert ch == oracle, f"CrossHair={ch} oracle={oracle}"
        assert ch is True
    finally:
        os.environ.pop("AF_CROSSHAIR", None)


def test_contract_precondition_guards() -> None:
    """pre (b>=0) の下では post (result>=a) が成立 — pre で違反が消える."""
    os.environ["AF_CROSSHAIR"] = "1"
    try:
        @contract(pre="b >= 0", post="result >= a")
        def add(a: int, b: int) -> int:
            return a + b

        ch = _ch_violates(add)
        oracle = _oracle_violates(add, lambda r, a, b: r >= a, pre=lambda a, b: b >= 0)
        assert ch == oracle, f"CrossHair={ch} oracle={oracle}"
        assert ch is False
    finally:
        os.environ.pop("AF_CROSSHAIR", None)
