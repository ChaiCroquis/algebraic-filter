"""A/B 計測 — AI 担当 preparation 層 (pytest 自動化).

実 Claude Code セッションでの修正サイクル数 / 修正成功率 / 副作用検出 は chai 主権で
別セッション実走 (real session を AI agent 自身は起動不可)。 本 file は AI 担当として
hook OFF / hook ON の機械的差分計測 layer を landing する:

  - hook OFF: ruff 直接 invoke で違反 count (= baseline 違反量)
  - hook ON: AF hook subprocess 経由で block 件数 count (= Veto Power 発動量)

実走: cd algebraic-filter && python -m pytest samples/violations/tests/test_ab_comparison.py -v

Phase 1 後半 A/B 計測との接続: 本 test の結果は機械的差分の baseline、 chai 別セッション
での実走時に「Claude 修正サイクル数」 を追加計測することで完全な A/B 比較になる。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SAMPLES_DIR = Path(__file__).resolve().parent.parent
HOOK_SCRIPT = REPO_ROOT / "hooks" / "posttool_af_check.py"
MANIFEST = json.loads((SAMPLES_DIR / "manifest.json").read_text(encoding="utf-8"))


def _count_ruff_violations(target_dir: Path) -> int:
    """ruff 直接 invoke で `Found N errors` の N を抽出"""
    result = subprocess.run(
        [
            "python",
            "-m",
            "ruff",
            "check",
            "--select=PERF,SIM,FURB,ANN,F",
            str(target_dir.relative_to(REPO_ROOT)).replace("\\", "/"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
    )
    output = (result.stdout or "") + (result.stderr or "")
    m = re.search(r"Found (\d+) error", output)
    return int(m.group(1)) if m else 0


def _count_hook_blocks_for_ruff_samples() -> int:
    """ruff target sample に対し hook を subprocess invoke して exit 2 件数を count"""
    blocked = 0
    for sample in MANIFEST["samples"]:
        if sample["expected_detection"]["tool"] != "ruff":
            continue
        if sample["verification_result"]["phase_0_actual_detection"] not in ("PASS", "PARTIAL"):
            continue
        event = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": f"samples/violations/{sample['file']}",
            },
        }
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(HOOK_SCRIPT)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        if result.returncode == 2:
            blocked += 1
    return blocked


def test_ab_baseline_unfixed_has_violations() -> None:
    """A baseline: hook OFF で unfixed sample に違反が存在する evidence"""
    unfixed_dir = SAMPLES_DIR
    n_unfixed = _count_ruff_violations(unfixed_dir)
    assert n_unfixed > 0, f"unfixed samples should have ruff violations, got {n_unfixed}"


def test_ab_baseline_fixed_has_no_ruff_violations() -> None:
    """A baseline: hook OFF でも fixed sample は ruff 違反が解消されている (ground truth)"""
    fixed_dir = SAMPLES_DIR / "fixed"
    n_fixed = _count_ruff_violations(fixed_dir)
    assert n_fixed == 0, f"fixed samples should have 0 ruff violations, got {n_fixed}"


def test_ab_hook_on_blocks_each_ruff_violation_sample() -> None:
    """B hook-on: hook が ruff target sample 全件で block (exit 2) する"""
    blocked = _count_hook_blocks_for_ruff_samples()
    expected_at_least = 4  # PASS sample が ruff target で 4 件 (perf401/sim103/sim300/ann001)
    assert blocked >= expected_at_least, (
        f"hook ON should block at least {expected_at_least} ruff samples, got {blocked}"
    )


def test_ab_differential_hook_blocks_match_violation_samples() -> None:
    """A/B 差分: hook OFF 違反量 > 0 + hook ON block 件数 ≥ ruff PASS sample 数の整合"""
    n_unfixed_violations = _count_ruff_violations(SAMPLES_DIR)
    n_hook_blocks = _count_hook_blocks_for_ruff_samples()
    # AI 担当範囲: 機械的差分が成立 (hook が違反を検出して block している)
    # chai 別セッション範囲: 実 Claude 修正サイクル数の計測
    assert n_unfixed_violations > 0
    assert n_hook_blocks >= 4
    print(f"\nA/B baseline (AI 担当部分):")
    print(f"  hook OFF (ruff direct): {n_unfixed_violations} violations in unfixed/")
    print(f"  hook ON (AF subprocess): {n_hook_blocks} samples blocked with exit 2")
    print(f"  → 実 Claude セッション側で修正サイクル数 + 修正成功率を chai が追加計測する path")
