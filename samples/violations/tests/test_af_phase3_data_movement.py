"""Phase 3 minimal prototype demo: static AST checker + tracemalloc runtime checker.

Phase 1 sample (intermediate_list_chain / dict_keys_list_for_iter / unnecessary_copy_chain /
string_concat_in_loop / multi_step_intermediate_chain) に対して Phase 3 の static + runtime
checker が data movement violation を検出できることを demo。

実走: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase3_data_movement.py -v
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SAMPLES_DIR = REPO_ROOT / "samples" / "violations"
sys.path.insert(0, str(REPO_ROOT))

from af_phase3.runtime_checker import check_threshold, measure  # noqa: E402
from af_phase3.static_checker import check_file  # noqa: E402


def _load_module(file_name: str):
    spec = importlib.util.spec_from_file_location(
        f"phase3_{file_name.replace('.py', '')}", SAMPLES_DIR / file_name
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_phase3_static_detects_intermediate_list_chain() -> None:
    """#6 intermediate_list_chain を AST checker が 検出"""
    violations = check_file(str(SAMPLES_DIR / "intermediate_list_chain.py"))
    rule_ids = [v.rule_id for v in violations]
    assert "intermediate-list-chain" in rule_ids, f"expected intermediate-list-chain, got {rule_ids}"


def test_phase3_static_detects_multi_step_chain() -> None:
    """#20 multi_step_intermediate_chain を AST checker が 検出"""
    violations = check_file(str(SAMPLES_DIR / "multi_step_intermediate_chain.py"))
    rule_ids = [v.rule_id for v in violations]
    assert "intermediate-list-chain" in rule_ids, f"expected intermediate-list-chain, got {rule_ids}"


def test_phase3_static_detects_dict_keys_list() -> None:
    """#38 dict_keys_list_for_iter を AST checker が 検出"""
    violations = check_file(str(SAMPLES_DIR / "dict_keys_list_for_iter.py"))
    rule_ids = [v.rule_id for v in violations]
    assert "dict-keys-list" in rule_ids, f"expected dict-keys-list, got {rule_ids}"


def test_phase3_static_detects_explicit_copy() -> None:
    """unnecessary_copy_chain を AST checker が .copy() 検出"""
    violations = check_file(str(SAMPLES_DIR / "unnecessary_copy_chain.py"))
    rule_ids = [v.rule_id for v in violations]
    assert "explicit-copy" in rule_ids, f"expected explicit-copy, got {rule_ids}"


def test_phase3_static_detects_string_concat_in_loop() -> None:
    """#37 string_concat_in_loop を AST checker が 検出"""
    violations = check_file(str(SAMPLES_DIR / "string_concat_in_loop.py"))
    rule_ids = [v.rule_id for v in violations]
    assert "string-concat-in-loop" in rule_ids, f"expected string-concat-in-loop, got {rule_ids}"


def test_phase3_static_clean_on_fixed_intermediate() -> None:
    """fixed/intermediate_list_chain (single comprehension) で violation 0 件"""
    violations = check_file(str(SAMPLES_DIR / "fixed" / "intermediate_list_chain.py"))
    chain_violations = [v for v in violations if v.rule_id == "intermediate-list-chain"]
    assert chain_violations == [], f"fixed sample should have 0 chain violations, got {chain_violations}"


def test_phase3_runtime_detects_excessive_allocation() -> None:
    """unnecessary_copy_chain の process() で 閾値超過 violation を runtime checker が検出"""
    mod = _load_module("unnecessary_copy_chain.py")
    data = list(range(5000))
    # threshold は 100 bytes — process() は data.copy / [:] / list() の 3 chain で
    # 数百 bytes の allocation を引き起こすため 100 bytes threshold で violation 検出される設計
    violation, m = check_threshold(mod.process, data, max_bytes=100)
    assert violation is not None, f"expected excessive-data-movement violation, got measurement {m}"
    assert violation.rule_id == "excessive-data-movement"
    assert violation.measured_bytes > violation.threshold_bytes


def test_phase3_static_wide_coverage() -> None:
    """Phase 1 全 46 sample に対する Phase 3 static checker の検出 wide coverage 実測."""
    import json

    manifest = json.loads((SAMPLES_DIR / "manifest.json").read_text(encoding="utf-8"))
    samples = manifest["samples"]

    detected = 0
    total = 0
    detail: list[str] = []
    for s in samples:
        file_path = SAMPLES_DIR / s["file"]
        if not file_path.exists():
            continue
        total += 1
        violations = check_file(str(file_path))
        if violations:
            detected += 1
            rule_ids = sorted(set(v.rule_id for v in violations))
            detail.append(f"  [DETECT] {s['file']} -> {rule_ids}")

    pct = detected / total * 100 if total else 0
    print(f"\n=== Phase 3 static checker wide coverage ({total} samples) ===")
    print("\n".join(detail))
    print(f"detected: {detected}/{total} = {pct:.1f}%")
    print(
        "\n適用 niche articulate: Phase 3 static checker は data-movement target sample"
        " (= intermediate list / dict.keys() list / explicit copy / string concat in loop)"
        " に効く。 algebraic-law target / 型注釈 target は別 layer (Phase 2) の独自 contribution 領域。"
    )

    # 関連 sample (data movement target) 約 8 件 / 全 46 = ~17% を articulate evidence
    assert detected >= 5, f"detected {detected} < 5 target (data-movement wide coverage)"


def test_phase3_runtime_passes_on_fixed_intermediate() -> None:
    """fixed/intermediate_list_chain は閾値以下 (single comprehension で allocation 抑制)"""
    spec = importlib.util.spec_from_file_location(
        "phase3_fixed_intermediate",
        SAMPLES_DIR / "fixed" / "intermediate_list_chain.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    data = list(range(100))
    # 小さい input + single comprehension なら allocation 小さい
    violation, m = check_threshold(mod.transform, data, max_bytes=100 * 1024)
    # 違反 None or 小さい measurement
    if violation is not None:
        # 1MB 等の絶対量で violation でも relative には fixed の方が unfixed より小さい
        pass
    assert m.total_size_bytes < 100 * 1024
