"""AF hook (hooks/posttool_af_check.py) の動作検証 5 tests.

Phase 1 planned tests 5 件 (manifest.json test_coverage.phase_1_planned_tests に articulate 済) を
hook 動作の 5 ケース (exit 2 + structured feedback + 3 safety nets) として実現。

実走: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_hook.py -v
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HOOK_SCRIPT = REPO_ROOT / "hooks" / "posttool_af_check.py"


def _invoke_hook(event: dict) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(HOOK_SCRIPT)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, (result.stdout or ""), (result.stderr or "")


def test_af_hook_emits_exit_2_on_violation() -> None:
    """Phase 1 planned test: AF hook が違反検出時に exit code 2 を返す"""
    event = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "samples/violations/perf401_manual_list_comp.py",
        },
    }
    exit_code, stdout, stderr = _invoke_hook(event)
    assert exit_code == 2, (
        f"expected exit 2 (block with feedback), got {exit_code}\n"
        f"stdout: {stdout[:300]}\nstderr: {stderr[:300]}"
    )


def test_af_hook_provides_structured_feedback() -> None:
    """Phase 1 planned test: AF hook stdout が decision=block + additionalContext を含む JSON"""
    event = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "samples/violations/perf401_manual_list_comp.py",
        },
    }
    _, stdout, _ = _invoke_hook(event)
    payload = json.loads(stdout.strip().splitlines()[-1])
    assert payload["decision"] == "block"
    assert "additionalContext" in payload
    assert "PERF401" in payload["additionalContext"]
    assert "list comprehension" in payload["additionalContext"]


def test_af_hook_no_op_on_clean_file() -> None:
    """safety net: 違反なし file (fixed/) では exit 0、 stdout 空"""
    event = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "samples/violations/fixed/perf401_manual_list_comp.py",
        },
    }
    exit_code, stdout, _ = _invoke_hook(event)
    assert exit_code == 0
    assert stdout.strip() == ""


def test_af_hook_skips_non_python_file() -> None:
    """safety net: .py 以外 (.md/.json/.txt 等) は対象外で exit 0"""
    event = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "docs/foo.md",
        },
    }
    exit_code, stdout, _ = _invoke_hook(event)
    assert exit_code == 0
    assert stdout.strip() == ""


def test_af_hook_skips_non_target_tool() -> None:
    """safety net: Write/Edit/MultiEdit 以外 (Read/Bash/etc.) は対象外で exit 0"""
    event = {
        "tool_name": "Read",
        "tool_input": {
            "file_path": "samples/violations/perf401_manual_list_comp.py",
        },
    }
    exit_code, stdout, _ = _invoke_hook(event)
    assert exit_code == 0
    assert stdout.strip() == ""
