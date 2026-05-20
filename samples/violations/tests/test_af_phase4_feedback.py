"""Phase 4 minimal prototype demo: 構造化 LLM フィードバック + anti-pattern 蓄積 + 事前 hint.

実走: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase4_feedback.py -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase3.static_checker import check_file  # noqa: E402
from af_phase4.anti_pattern_tracker import (  # noqa: E402
    get_preemptive_hints,
    record_violations,
)
from af_phase4.feedback_formatter import (  # noqa: E402
    SHAPE_MINIMAL,
    SHAPE_SKELETON_ONLY,
    SHAPE_VERBOSE,
    combine_violations,
    format_phase2_violations,
    format_phase3_violations,
    format_ruff_violations,
    get_active_shape,
    shape_violation_for_output,
)

HOOK_SCRIPT = REPO_ROOT / "hooks" / "posttool_af_check.py"


def test_phase4_format_ruff_violations_structured() -> None:
    """ruff raw output → 統一 schema dict 抽出"""
    ruff_output = """PERF401 Use a list comprehension
  --> samples/violations/perf401_manual_list_comp.py:15:13
   |
13 |     for x in data:
14 |         if x > 0:
15 |             result.append(x * 2)
   |             ^^^^^^^^^^^^^^^^^^^^
help: Replace for loop

Found 1 error.
"""
    violations = format_ruff_violations(ruff_output, "samples/violations/perf401_manual_list_comp.py")
    assert len(violations) == 1
    v = violations[0]
    assert v["layer"] == "Phase 1 ruff"
    assert v["violation_law"] == "PERF401"
    assert "samples/violations/perf401_manual_list_comp.py:15" in v["violation_location"]
    assert v["alternative_skeleton"] == "list comprehension"
    assert v["fix_example"] == "[x * 2 for x in data if x > 0]"


def test_phase4_format_phase3_violations_structured() -> None:
    """Phase 3 StaticViolation → 統一 schema dict"""
    sample = REPO_ROOT / "samples" / "violations" / "intermediate_list_chain.py"
    phase3_vios = check_file(str(sample))
    formatted = format_phase3_violations(phase3_vios, str(sample))
    assert len(formatted) >= 1
    chain_violations = [v for v in formatted if v["violation_law"] == "intermediate-list-chain"]
    assert chain_violations
    v = chain_violations[0]
    assert v["layer"] == "Phase 3 AST"
    assert v["alternative_skeleton"] == "single comprehension or generator chain"


def test_phase4_combine_violations_unifies_phase1_and_phase3() -> None:
    """combine_violations が Phase 1 + Phase 3 を 1 list に集約"""
    sample = REPO_ROOT / "samples" / "violations" / "intermediate_list_chain.py"
    phase3_vios = check_file(str(sample))
    ruff_mock = "PERF401 Use a list comprehension\n  --> foo.py:1:1\n"
    combined = combine_violations(ruff_mock, phase3_vios, str(sample))
    layers = {v["layer"] for v in combined}
    assert "Phase 1 ruff" in layers
    assert "Phase 3 AST" in layers


def test_phase4_anti_pattern_tracker_records_and_recalls() -> None:
    """record_violations 3 回 → get_preemptive_hints で hint message 取得"""
    with tempfile.TemporaryDirectory() as tmp:
        hist = Path(tmp) / "history.json"

        # 1 回目 + 2 回目: hint 出ない
        record_violations(["PERF401"], "f.py", history_path=hist)
        record_violations(["PERF401"], "f.py", history_path=hist)
        hints_2 = get_preemptive_hints(["PERF401"], history_path=hist, threshold=3)
        assert hints_2 == [], f"2 回でまだ hint 出ないはず: {hints_2}"

        # 3 回目: hint 出る
        record_violations(["PERF401"], "f.py", history_path=hist)
        hints_3 = get_preemptive_hints(["PERF401"], history_path=hist, threshold=3)
        assert hints_3, "3 回で hint 出るはず"
        assert "PERF401" in hints_3[0]
        assert "3 times" in hints_3[0]


def test_phase4_format_phase2_violations_structured() -> None:
    """Phase 2 代数法則 failure dict list → 統一 schema dict list"""
    phase2_failures = [
        {
            "law_id": "monoid_associativity",
            "function_name": "my_sum",
            "line": 12,
            "counter_example": "(a, b, c) = (1, 2, 3)",
        },
        {
            "law_id": "commutativity",
            "function_name": "weighted_avg",
            "line": 7,
        },
    ]
    formatted = format_phase2_violations(phase2_failures, "samples/violations/foo.py")
    assert len(formatted) == 2

    v0 = formatted[0]
    assert v0["layer"] == "Phase 2 algebraic-law"
    assert v0["violation_law"] == "monoid_associativity"
    assert "samples/violations/foo.py:12" in v0["violation_location"]
    assert v0["alternative_skeleton"]  # 非空 (= 法則説明 skeleton landed)
    assert v0["fix_example"]  # 非空
    assert "counter-example" in v0["violation_message"]

    v1 = formatted[1]
    assert v1["violation_law"] == "commutativity"
    assert "samples/violations/foo.py:7" in v1["violation_location"]


def test_phase4_combine_violations_with_phase2() -> None:
    """combine_violations が phase2_failures 引数で Phase 1 + 2 + 3 を 1 list に集約"""
    sample = REPO_ROOT / "samples" / "violations" / "intermediate_list_chain.py"
    phase3_vios = check_file(str(sample))
    ruff_mock = "PERF401 Use a list comprehension\n  --> foo.py:1:1\n"
    phase2_failures = [{"law_id": "monoid_identity", "function_name": "agg", "line": 3}]
    combined = combine_violations(ruff_mock, phase3_vios, str(sample), phase2_failures)
    layers = {v["layer"] for v in combined}
    assert "Phase 1 ruff" in layers
    assert "Phase 2 algebraic-law" in layers
    assert "Phase 3 AST" in layers


def test_phase4_combine_violations_backward_compatible_no_phase2() -> None:
    """phase2_failures = None (= 既定) の場合 v0.1.0 互換 (Phase 1 + 3 のみ)"""
    sample = REPO_ROOT / "samples" / "violations" / "intermediate_list_chain.py"
    phase3_vios = check_file(str(sample))
    ruff_mock = "PERF401 Use a list comprehension\n  --> foo.py:1:1\n"
    combined = combine_violations(ruff_mock, phase3_vios, str(sample))
    layers = {v["layer"] for v in combined}
    assert "Phase 2 algebraic-law" not in layers, "phase2_failures 未指定時は Phase 2 含まない"


def test_phase4_per_rule_threshold_override_heavy_violation() -> None:
    """重い違反 (= 代数法則) は override で 2 回目に hint、 default 3 を待たない"""
    with tempfile.TemporaryDirectory() as tmp:
        hist = Path(tmp) / "history.json"

        # 1 回目: hint 出ない
        record_violations(["monoid_associativity"], "f.py", history_path=hist)
        hints_1 = get_preemptive_hints(["monoid_associativity"], history_path=hist)
        assert hints_1 == [], f"1 回ではまだ hint 出ないはず: {hints_1}"

        # 2 回目: override threshold=2 で hint 出る (= default 3 を待たない)
        record_violations(["monoid_associativity"], "f.py", history_path=hist)
        hints_2 = get_preemptive_hints(["monoid_associativity"], history_path=hist)
        assert hints_2, "2 回で override threshold=2 により hint 出るはず"
        assert "monoid_associativity" in hints_2[0]
        assert "threshold=2" in hints_2[0]


def test_phase4_per_rule_threshold_default_light_violation() -> None:
    """軽微違反 (= PERF401 等) は default threshold=3 のまま、 override 適用なし"""
    with tempfile.TemporaryDirectory() as tmp:
        hist = Path(tmp) / "history.json"

        # 2 回目: default threshold=3 なので hint 出ない (= override 不在)
        record_violations(["PERF401"], "f.py", history_path=hist)
        record_violations(["PERF401"], "f.py", history_path=hist)
        hints_2 = get_preemptive_hints(["PERF401"], history_path=hist)
        assert hints_2 == [], f"PERF401 は default threshold=3、 2 回では hint 出ないはず: {hints_2}"

        # 3 回目: default threshold=3 で hint 出る
        record_violations(["PERF401"], "f.py", history_path=hist)
        hints_3 = get_preemptive_hints(["PERF401"], history_path=hist)
        assert hints_3, "PERF401 は 3 回で default threshold=3 により hint 出るはず"
        assert "threshold=3" in hints_3[0]


_SAMPLE_VIOLATION_DICT = {
    "layer": "Phase 1 ruff",
    "violation_location": "foo.py:15",
    "violation_law": "PERF401",
    "violation_message": "Use a list comprehension",
    "alternative_skeleton": "list comprehension",
    "fix_example": "[x * 2 for x in data if x > 0]",
}


def test_phase4_shape_verbose_emits_skeleton_and_fix() -> None:
    """verbose shape (= default) は skeleton + fix example 両方を出力 (3 行)"""
    lines = shape_violation_for_output(_SAMPLE_VIOLATION_DICT, shape=SHAPE_VERBOSE)
    assert len(lines) == 3
    joined = "\n".join(lines)
    assert "PERF401" in joined
    assert "skeleton:" in joined
    assert "fix example:" in joined


def test_phase4_shape_minimal_emits_head_only() -> None:
    """minimal shape は law_id + location の 1 行のみ (= token 節約)"""
    lines = shape_violation_for_output(_SAMPLE_VIOLATION_DICT, shape=SHAPE_MINIMAL)
    assert len(lines) == 1
    assert "PERF401" in lines[0]
    assert "foo.py:15" in lines[0]
    assert "skeleton:" not in lines[0]
    assert "fix example:" not in lines[0]


def test_phase4_shape_skeleton_only_omits_fix() -> None:
    """skeleton_only shape は skeleton 添えるが fix example は省略 (2 行)"""
    lines = shape_violation_for_output(_SAMPLE_VIOLATION_DICT, shape=SHAPE_SKELETON_ONLY)
    assert len(lines) == 2
    joined = "\n".join(lines)
    assert "skeleton:" in joined
    assert "fix example:" not in joined


def test_phase4_get_active_shape_env_switch() -> None:
    """env var AF_FEEDBACK_SHAPE で active shape が切り替わる、 不正値は verbose fallback"""
    saved = os.environ.get("AF_FEEDBACK_SHAPE")
    try:
        os.environ["AF_FEEDBACK_SHAPE"] = "minimal"
        assert get_active_shape() == SHAPE_MINIMAL
        os.environ["AF_FEEDBACK_SHAPE"] = "skeleton_only"
        assert get_active_shape() == SHAPE_SKELETON_ONLY
        os.environ["AF_FEEDBACK_SHAPE"] = "bogus_value"
        assert get_active_shape() == SHAPE_VERBOSE  # 不正値は verbose
        os.environ.pop("AF_FEEDBACK_SHAPE", None)
        assert get_active_shape() == SHAPE_VERBOSE  # 未設定は verbose
    finally:
        if saved is None:
            os.environ.pop("AF_FEEDBACK_SHAPE", None)
        else:
            os.environ["AF_FEEDBACK_SHAPE"] = saved


def test_phase4_hook_emits_structured_feedback() -> None:
    """hook を sample で起動 → JSON output に Phase 4 structured + Phase 1 raw + Phase 3 raw が含まれる"""
    # history を一旦リセット (= clean state、 ただし test 後に元状態は戻さない、 minor accept)
    event = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(REPO_ROOT / "samples" / "violations" / "perf401_manual_list_comp.py")},
    }
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(HOOK_SCRIPT)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
    )
    assert result.returncode == 2, f"expected exit 2, got {result.returncode}\nstderr: {result.stderr}"
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    ctx = payload["additionalContext"]
    assert "Phase 4" in ctx, f"Phase 4 section not in payload:\n{ctx[:500]}"
    assert "PERF401" in ctx
    assert "list comprehension" in ctx
    # structured payload の skeleton / fix example marker
    assert "skeleton:" in ctx
    assert "fix example:" in ctx
