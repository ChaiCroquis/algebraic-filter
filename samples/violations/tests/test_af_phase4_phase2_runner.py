"""Phase 4 拡張 (1b): hook 実行時 Phase 2 PBT runner の opt-in 動作検証.

env var AF_HOOK_PHASE2_PBT で gate、 ON 時のみ phase2_runner が走り、
known 違反 sample (= monoid_associativity_violation.py の my_sum) で
phase2_failures を Phase 4 統一 schema dict として返すこと.

実走: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase4_phase2_runner.py -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase4.phase2_runner import (  # noqa: E402
    collect_phase2_failures,
    is_enabled,
)

HOOK_SCRIPT = REPO_ROOT / "hooks" / "posttool_af_check.py"
SAMPLE_VIOLATION = (
    REPO_ROOT / "samples" / "violations" / "monoid_associativity_violation.py"
)


def test_phase2_runner_disabled_by_default() -> None:
    """env var 未設定 → is_enabled() False、 collect が空 list を返す"""
    os.environ.pop("AF_HOOK_PHASE2_PBT", None)
    assert is_enabled() is False
    failures = collect_phase2_failures(str(SAMPLE_VIOLATION))
    assert failures == [], f"env 未設定で failures は空のはず: {failures}"


def test_phase2_runner_enabled_detects_violation() -> None:
    """env var ON + known 違反 sample → 1 件以上の phase2_failures dict を返す"""
    os.environ["AF_HOOK_PHASE2_PBT"] = "1"
    try:
        assert is_enabled() is True
        failures = collect_phase2_failures(str(SAMPLE_VIOLATION))
        assert failures, "monoid violation sample で failure 検出 0 件は異常"
        # 各 failure dict は format_phase2_violations が期待する key を持つ
        for f in failures:
            assert "law_id" in f
            assert "function_name" in f
            assert "line" in f
            # 関数名が sample の my_sum と一致
            assert f["function_name"] == "my_sum"
    finally:
        os.environ.pop("AF_HOOK_PHASE2_PBT", None)


def test_phase2_runner_handles_nonexistent_file() -> None:
    """存在しない file → 例外送出せず空 list を返す (= safety)"""
    os.environ["AF_HOOK_PHASE2_PBT"] = "1"
    try:
        failures = collect_phase2_failures("/nonexistent/path/to/foo.py")
        assert failures == []
    finally:
        os.environ.pop("AF_HOOK_PHASE2_PBT", None)


def test_phase2_runner_handles_non_py_file() -> None:
    """.py 以外の file → 空 list を返す"""
    os.environ["AF_HOOK_PHASE2_PBT"] = "1"
    try:
        failures = collect_phase2_failures(str(REPO_ROOT / "README.md"))
        assert failures == []
    finally:
        os.environ.pop("AF_HOOK_PHASE2_PBT", None)


def test_hook_with_phase2_env_off_does_not_run_phase2() -> None:
    """env var OFF (= 未設定) で hook 起動 → ruff/Phase 3 のみ動作、 Phase 2 layer 含まない"""
    env = dict(os.environ)
    env.pop("AF_HOOK_PHASE2_PBT", None)
    event = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(SAMPLE_VIOLATION)},
    }
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(HOOK_SCRIPT)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
        env=env,
    )
    # sample に ruff 違反が無ければ exit 0、 ある場合は exit 2 (= どちらでも Phase 2 layer は含まれない)
    if result.returncode == 2 and result.stdout:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        ctx = payload["additionalContext"]
        assert "Phase 2 algebraic-law" not in ctx, (
            f"env OFF で Phase 2 layer が含まれている (= gate 不全): {ctx[:300]}"
        )


def test_hook_with_phase2_env_on_includes_phase2_layer() -> None:
    """env var ON で hook 起動 → Phase 2 algebraic-law layer が context に含まれる"""
    env = dict(os.environ)
    env["AF_HOOK_PHASE2_PBT"] = "1"
    event = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(SAMPLE_VIOLATION)},
    }
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(HOOK_SCRIPT)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
        env=env,
    )
    assert result.returncode == 2, (
        f"env ON + violation sample で exit 2 期待、 got {result.returncode}\n"
        f"stderr: {result.stderr}"
    )
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    ctx = payload["additionalContext"]
    assert "Phase 2 algebraic-law" in ctx, (
        f"env ON で Phase 2 layer が context に含まれていない:\n{ctx[:500]}"
    )
    # law_id + violation_location (= file + line 22) で違反箇所が articulate されていること
    assert "monoid_identity" in ctx
    assert "monoid_associativity_violation.py:22" in ctx
