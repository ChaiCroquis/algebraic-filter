"""Phase 3 精度 P3-C2: 証拠ゲート式 flag の横展開監査.

string-concat-in-loop で確立した「陽性の証拠がある時だけ flag」 を他 AST ルールへ監査:
  - explicit-copy: copy chain 証拠 (>=2) の時のみ flag。 単独防御コピーは FP として除外。
  - dict-keys-list / intermediate-list-chain: 正例 (検出) と 負例 (誤検出しない) を固定。

既知の境界: dict-keys-list は list(x.keys()) を常に flag するため、 snapshot が必要な
非 dict の x には false positive が残る (型情報なしには gate 不可、 limitations に明記)。

実行: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase3_evidence_gates.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase3.static_checker import check_source  # noqa: E402


def _rules(src: str) -> list[str]:
    return [v.rule_id for v in check_source(src)]


def test_explicit_copy_single_defensive_not_flagged() -> None:
    """単独の防御的コピーは perf smell でない → flag しない (FP 除外)."""
    src = "def f(data):\n    backup = data.copy()\n    return backup\n"
    assert "explicit-copy" not in _rules(src)


def test_explicit_copy_chain_flagged() -> None:
    """copy chain (>=2: .copy() + 全スライス) は flag (証拠あり)."""
    src = "def f(data):\n    a = data.copy()\n    b = a[:]\n    return b\n"
    assert "explicit-copy" in _rules(src)


def test_dict_keys_list_items_not_flagged() -> None:
    """list でない items() 反復は flag しない (rule は keys/values に scoped)."""
    src = "def f(d):\n    return [(k, v) for k, v in d.items()]\n"
    assert "dict-keys-list" not in _rules(src)


def test_dict_keys_list_keys_flagged() -> None:
    """list(d.keys()) は flag (正例)."""
    src = "def f(d):\n    return list(d.keys())\n"
    assert "dict-keys-list" in _rules(src)


def test_intermediate_chain_single_comprehension_not_flagged() -> None:
    """単一 comprehension は中間 list を作らない → flag しない (FP 除外)."""
    src = "def f(data):\n    return [x * 2 for x in data if x > 0]\n"
    assert "intermediate-list-chain" not in _rules(src)


def test_intermediate_chain_nested_flagged() -> None:
    """list(filter(..., list(map(...)))) の nested 中間 list は flag (正例)."""
    src = "def f(data):\n    return list(filter(lambda x: x > 0, list(map(lambda x: x * 2, data))))\n"
    assert "intermediate-list-chain" in _rules(src)
