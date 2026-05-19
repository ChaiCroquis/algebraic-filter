"""Phase 2 minimal prototype demo: 関数シグネチャから法則推論 → @given test 自動生成 → 違反検出.

Phase 1 で landed した 46 sample のうち 3 sample に対し、 af_phase2.auto_test()
が法則推論 + PBT を自動で行い、 違反を articulate できるかを demo。

実走: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase2_auto_generation.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SAMPLES_DIR = REPO_ROOT / "samples" / "violations"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SAMPLES_DIR))

from af_phase2.generator import auto_test  # noqa: E402


def test_phase2_auto_detects_monoid_violation() -> None:
    """#5 monoid_associativity_violation を auto_test が検出 (= my_sum 命名から monoid_identity 推論 → FAIL)"""
    from monoid_associativity_violation import my_sum  # noqa

    results = auto_test(my_sum)
    monoid_fails = [r for r in results if r.law_id == "monoid_identity" and r.status == "FAIL"]
    assert monoid_fails, (
        f"expected monoid_identity FAIL for my_sum (subtraction reduce), got {results}"
    )


def test_phase2_auto_detects_functor_violation() -> None:
    """#15 functor_id_violation を auto_test が検出 (= my_map 命名から functor_identity 推論 → FAIL)"""
    # ただし複数の sample で my_map を定義しているため import 整理
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "functor_id_sample", SAMPLES_DIR / "functor_id_violation.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    results = auto_test(mod.my_map)
    functor_fails = [r for r in results if r.law_id == "functor_identity" and r.status == "FAIL"]
    assert functor_fails, (
        f"expected functor_identity FAIL for my_map (+0.0001 offset), got {results}"
    )


def test_phase2_auto_detects_commutativity_violation() -> None:
    """#21 weighted_average_commutativity_violation を auto_test が検出 (= average 命名から commutativity 推論 → FAIL)"""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "weighted_avg_sample", SAMPLES_DIR / "weighted_average_commutativity_violation.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    results = auto_test(mod.average)
    commut_fails = [r for r in results if r.law_id == "commutativity" and r.status == "FAIL"]
    assert commut_fails, (
        f"expected commutativity FAIL for average (weighted asymmetric), got {results}"
    )


def test_phase2_auto_passes_on_fixed_monoid() -> None:
    """fixed/monoid_associativity_violation の my_sum (addition reduce) で auto_test PASS"""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "fixed_monoid_sample", SAMPLES_DIR / "fixed" / "monoid_associativity_violation.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    results = auto_test(mod.my_sum)
    monoid_passes = [r for r in results if r.law_id == "monoid_identity" and r.status == "PASS"]
    assert monoid_passes, (
        f"expected monoid_identity PASS for fixed my_sum (addition), got {results}"
    )
