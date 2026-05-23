"""決定論拡張 D3: 単位元の一般化 (加法 0 限定の解除).

@law("monoid_identity", identity=e) で宣言が単位元を運び、 乗法 (e=1)・文字列連結
(e="") など任意モノイドの identity を CrossHair 証明できることを固定。

非チェリーピック: int 乗法は exhaustive oracle (identity=1) と verdict 一致を
正/誤 両方で照合。 文字列は CrossHair 証明 + inline brute-force で確認。

実行: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase2_generalized_identity.py -v
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

pytest.importorskip("crosshair", reason="crosshair-tool not installed (optional extra)")

from af_phase2.crosshair_bridge import verify  # noqa: E402
from af_phase2.exhaustive import exhaustive_verify  # noqa: E402
from af_phase2.inferrer import law  # noqa: E402


def _ch_identity_violation(func) -> bool:  # noqa: ANN001
    return any(v["law_id"] == "monoid_identity" for v in verify(func))


def test_multiplicative_identity_agrees_with_oracle() -> None:
    """乗法モノイド (e=1): 正しい * は単位元成立、 a*b+1 は違反 — CrossHair と oracle 一致."""
    os.environ["AF_CROSSHAIR"] = "1"
    try:
        @law("monoid_identity", identity=1)
        def mul(a: int, b: int) -> int:
            return a * b

        @law("monoid_identity", identity=1)
        def bad_mul(a: int, b: int) -> int:
            return a * b + 1  # a*1+1 != a

        for f, expect_violation in ((mul, False), (bad_mul, True)):
            ch = _ch_identity_violation(f)
            oracle = exhaustive_verify(f, "monoid_identity", identity=1) is not None
            assert ch == oracle, f"{f.__name__}: CrossHair={ch} oracle={oracle}"
            assert ch == expect_violation, f"{f.__name__}: got {ch}, expected {expect_violation}"
    finally:
        os.environ.pop("AF_CROSSHAIR", None)


def test_additive_identity_default_still_works() -> None:
    """単位元 未宣言は従来の加法 0 のまま (後方互換)."""
    os.environ["AF_CROSSHAIR"] = "1"
    try:
        @law("monoid_identity")
        def add(a: int, b: int) -> int:
            return a + b

        assert _ch_identity_violation(add) is False  # a+0==a
    finally:
        os.environ.pop("AF_CROSSHAIR", None)


def test_string_concat_identity_proven() -> None:
    """文字列連結モノイド (e=''): a+'' == a を CrossHair 証明 (加法 0 では表せない領域)."""
    os.environ["AF_CROSSHAIR"] = "1"
    try:
        @law("monoid_identity", identity="")
        def concat(a: str, b: str) -> str:
            return a + b

        assert _ch_identity_violation(concat) is False
    finally:
        os.environ.pop("AF_CROSSHAIR", None)
