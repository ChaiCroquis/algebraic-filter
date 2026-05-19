"""Phase 4 minimal prototype demo: 構造化 LLM フィードバック + anti-pattern 蓄積 + 事前 hint.

実走: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase4_feedback.py -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase3.static_checker import check_file  # noqa: E402
from af_phase4.anti_pattern_tracker import (  # noqa: E402
    get_preemptive_hints,
    record_violations,
    reset_history,
)
from af_phase4.feedback_formatter import (  # noqa: E402
    combine_violations,
    format_phase3_violations,
    format_ruff_violations,
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
        assert hints_3, f"3 回で hint 出るはず"
        assert "PERF401" in hints_3[0]
        assert "3 times" in hints_3[0]


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
