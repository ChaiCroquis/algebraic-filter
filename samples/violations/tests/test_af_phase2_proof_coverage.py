"""Phase 2 精度 P2-B3: 「証明済み (CrossHair) vs サンプリングのみ (hypothesis)」 の内訳を固定.

決定論の島の厚み = CrossHair で *証明* できる法則数 / 全法則テンプレ数。
本テストはその内訳を回帰固定し、 evidence_summary / limitations の記述と同期させる。

実行: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase2_proof_coverage.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase2.crosshair_bridge import _LAW_CONTRACT  # noqa: E402
from af_phase2.law_templates import LAW_REGISTRY  # noqa: E402

# CrossHair で決定論的に証明できる法則 (binary 関数が対象)。 2026-05-22 に
# identity + idempotence を追加し 3 -> 5、 2026-05-24 に eq 則 2 つを追加し 5 -> 7。
_PROVABLE = {
    "monoid_associativity",
    "semigroup_associativity",
    "commutativity",
    "monoid_identity",
    "idempotence",
    "eq_reflexivity",
    "eq_symmetry",
}


def test_crosshair_provable_law_set() -> None:
    """CrossHair 証明可能な法則集合が想定どおり (= 決定論の島の境界を固定)."""
    assert set(_LAW_CONTRACT) == _PROVABLE, set(_LAW_CONTRACT)


def test_provable_is_subset_of_all_law_templates() -> None:
    """証明可能法則は全法則テンプレの部分集合 (= サンプリング側も存在する)."""
    assert set(LAW_REGISTRY) >= _PROVABLE, _PROVABLE - set(LAW_REGISTRY)


def test_proof_coverage_ratio_documented() -> None:
    """文書同期: 7/14 が証明済み、 残り 7 はサンプリングのみ.

    この数が変わったら evidence_summary / limitations の記述も更新すること。
    """
    provable = len(_LAW_CONTRACT)
    total = len(LAW_REGISTRY)
    assert provable == 7, provable
    assert total == 14, total
    assert total - provable == 7  # hypothesis-sampling-only
