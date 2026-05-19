"""A/B 計測自動化 prototype: nested claude --print で 5 task × 2 round 実走.

protocol.md の手動手順を script 化。 各 task で:
  - hook OFF round: settings.local.json を rename して hook 無効化
  - hook ON round: settings restore して hook 有効化
  - nested session に違反コード書き込み + 修正依頼
  - stdout から Edit 回数を正規表現で parse
  - ruff check で最終 violation 数を取得

実走: cd algebraic-filter && python scripts/ab_automation.py
出力: docs/_ab_measurement/log_auto_<timestamp>.md
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SETTINGS = REPO_ROOT / ".claude" / "settings.local.json"
SETTINGS_DISABLED = REPO_ROOT / ".claude" / "settings.local.json.disabled"
SCRATCH = REPO_ROOT / "scratch"
LOG_DIR = REPO_ROOT / "docs" / "_ab_measurement"
# Windows: subprocess.run([..., "claude", ...]) は .cmd 拡張子未解決のため絶対 path 指定
CLAUDE_CMD = r"C:\Users\user\AppData\Roaming\npm\claude.cmd"

# task definitions: (tag, violation_code, fix_instruction, ruff_select)
TASKS = [
    (
        "perf401",
        '''def double_positives(data):
    result = []
    for x in data:
        if x > 0:
            result.append(x * 2)
    return result
''',
        "PERF401 違反を Edit で修正してください",
        "PERF",
    ),
    (
        "sim103",
        '''def is_positive(x):
    if x > 0:
        return True
    else:
        return False
''',
        "SIM103 違反を Edit で修正してください",
        "SIM",
    ),
    (
        "sim300",
        '''def check_status(status):
    if 0 == status:
        return "ok"
    return "error"
''',
        "SIM300 違反を Edit で修正してください",
        "SIM",
    ),
    (
        "ann001",
        '''def add(x, y):
    return x + y
''',
        "ANN001 違反を Edit で修正してください",
        "ANN",
    ),
    (
        "intermediate",
        '''def transform(data):
    return list(filter(lambda x: x > 0, list(map(lambda x: x * 2, data))))
''',
        "中間 list materialization を解消するよう Edit で修正してください",
        "PERF",
    ),
]


def disable_hook() -> None:
    if SETTINGS.exists():
        SETTINGS.rename(SETTINGS_DISABLED)


def enable_hook() -> None:
    if SETTINGS_DISABLED.exists():
        SETTINGS_DISABLED.rename(SETTINGS)


def run_nested_task(tag: str, mode: str, code: str, instruction: str) -> dict:
    """nested claude --print で 1 task 実行、 結果 parse."""
    target = f"scratch/_ab_{tag}_{mode}.py"
    prompt = (
        f"A/B 計測のため {target} に以下のコードを Write してください:\n\n"
        f"{code}\n"
        f"Write 後、 {instruction}。 "
        f"完了後、 Edit ツールを何回呼んだか数字で 'Edit count: <数字>' の形式で articulate してください。"
    )
    start = time.time()
    try:
        result = subprocess.run(
            [CLAUDE_CMD, "--print", "--allowedTools", "Write,Edit,Read"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            cwd=REPO_ROOT,
        )
        elapsed = time.time() - start
        output = (result.stdout or "") + (result.stderr or "")
        edit_count = None
        # 複数 articulate 形式に対応した正規表現
        for pat in (
            r"Edit count[\s:：]+(\d+)",
            r"Edit ツール呼び出し回数[\s:：*]+(\d+)",
            r"Edit\s+called\s+(\d+)\s+times?",
            r"(\d+)\s*回\s*Edit",
        ):
            m = re.search(pat, output)
            if m:
                edit_count = int(m.group(1))
                break
        return {
            "tag": tag,
            "mode": mode,
            "target": target,
            "exit_code": result.returncode,
            "elapsed_seconds": round(elapsed, 1),
            "edit_count": edit_count,
            "stdout_tail": output[-800:],
        }
    except subprocess.TimeoutExpired:
        return {
            "tag": tag,
            "mode": mode,
            "target": target,
            "exit_code": -1,
            "elapsed_seconds": 300.0,
            "edit_count": None,
            "stdout_tail": "(timeout)",
        }


def ruff_check_final(target: str, ruff_select: str) -> dict:
    """task 完了後の ruff violation 数を取得."""
    full = REPO_ROOT / target
    if not full.exists():
        return {"violations": -1, "raw": "(file not found)"}
    result = subprocess.run(
        ["python", "-m", "ruff", "check", f"--select={ruff_select}", str(full)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
    )
    output = (result.stdout or "") + (result.stderr or "")
    m = re.search(r"Found (\d+) error", output)
    if m:
        return {"violations": int(m.group(1)), "raw": output[-300:]}
    if "All checks passed" in output:
        return {"violations": 0, "raw": "All checks passed"}
    return {"violations": -1, "raw": output[-300:]}


def run_round(mode: str) -> list[dict]:
    print(f"\n=== Round: {mode.upper()} ===")
    results = []
    for tag, code, instruction, ruff_select in TASKS:
        print(f"  [{tag}] starting...")
        r = run_nested_task(tag, mode, code, instruction)
        rc = ruff_check_final(r["target"], ruff_select)
        r["final_ruff_violations"] = rc["violations"]
        r["final_ruff_raw_tail"] = rc["raw"][-200:]
        results.append(r)
        print(f"  [{tag}] exit={r['exit_code']} edits={r['edit_count']} violations={rc['violations']} elapsed={r['elapsed_seconds']}s")
    return results


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # Round 1: hook OFF
    disable_hook()
    off_results = run_round("off")

    # Round 2: hook ON
    enable_hook()
    on_results = run_round("on")

    # 集計
    def avg_edits(results: list[dict]) -> float | None:
        vals = [r["edit_count"] for r in results if r["edit_count"] is not None]
        return sum(vals) / len(vals) if vals else None

    def success_count(results: list[dict]) -> int:
        return sum(1 for r in results if r["final_ruff_violations"] == 0)

    summary = {
        "timestamp": timestamp,
        "tasks": len(TASKS),
        "off": {
            "avg_edit_count": avg_edits(off_results),
            "success_count": success_count(off_results),
            "details": off_results,
        },
        "on": {
            "avg_edit_count": avg_edits(on_results),
            "success_count": success_count(on_results),
            "details": on_results,
        },
    }

    log_file = LOG_DIR / f"log_auto_{timestamp}.json"
    log_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== Summary saved to {log_file} ===")
    print(f"OFF: avg_edits={summary['off']['avg_edit_count']}, success={summary['off']['success_count']}/{len(TASKS)}")
    print(f"ON : avg_edits={summary['on']['avg_edit_count']}, success={summary['on']['success_count']}/{len(TASKS)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
