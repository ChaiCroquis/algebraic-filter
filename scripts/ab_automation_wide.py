"""A/B 計測 wide 拡張版: manifest.json から ruff-target PASS sample を全件抽出して自動実走.

ab_automation.py の 5 task 固定版から、 manifest 駆動 で 約 12 sample (= ruff target + PASS) に拡張。
全 layer ruff check (PERF/SIM/FURB/ANN/F) で完成度差分集計。

実走: cd algebraic-filter && python scripts/ab_automation_wide.py
出力: docs/_ab_measurement/log_auto_wide_<timestamp>.json
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
SAMPLES_DIR = REPO_ROOT / "samples" / "violations"
MANIFEST_PATH = SAMPLES_DIR / "manifest.json"
CLAUDE_CMD = r"C:\Users\user\AppData\Roaming\npm\claude.cmd"

FULL_RUFF_SELECT = "PERF,SIM,FURB,ANN,F"


def load_target_samples() -> list[dict]:
    """manifest から ruff-target + PASS sample を抽出."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return [
        s
        for s in manifest["samples"]
        if s["expected_detection"]["tool"] == "ruff"
        and s["verification_result"]["phase_0_actual_detection"] == "PASS"
        and (SAMPLES_DIR / s["file"]).exists()
        and (SAMPLES_DIR / "fixed" / s["file"]).exists()
    ]


def disable_hook() -> None:
    if SETTINGS.exists():
        SETTINGS.rename(SETTINGS_DISABLED)


def enable_hook() -> None:
    if SETTINGS_DISABLED.exists():
        SETTINGS_DISABLED.rename(SETTINGS)


def build_prompt(sample: dict, mode: str) -> tuple[str, str]:
    sample_id = sample["id"]
    sample_file = SAMPLES_DIR / sample["file"]
    code = sample_file.read_text(encoding="utf-8")
    rule_id = sample["expected_detection"]["rule_id"]
    target = f"scratch/_ab_{sample_id}_{mode}.py"
    prompt = (
        f"A/B 計測のため {target} に以下のコードを Write してください:\n\n"
        f"{code}\n"
        f"Write 後、 {rule_id} 違反を Edit で修正してください。 "
        f"完了後、 Edit ツールを何回呼んだか数字で 'Edit count: <数字>' の形式で articulate してください。"
    )
    return prompt, target


def run_nested_task(sample: dict, mode: str) -> dict:
    sample_id = sample["id"]
    prompt, target = build_prompt(sample, mode)
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
        for pat in (
            r"Edit count[\s:：]+(\d+)",
            r"Edit ツール呼び出し回数[\s:：*]+(\d+)",
            r"(\d+)\s*回\s*Edit",
        ):
            m = re.search(pat, output)
            if m:
                edit_count = int(m.group(1))
                break
        return {
            "sample_id": sample_id,
            "mode": mode,
            "target": target,
            "exit_code": result.returncode,
            "elapsed_seconds": round(elapsed, 1),
            "edit_count": edit_count,
            "stdout_tail": output[-400:],
        }
    except subprocess.TimeoutExpired:
        return {
            "sample_id": sample_id,
            "mode": mode,
            "target": target,
            "exit_code": -1,
            "elapsed_seconds": 300.0,
            "edit_count": None,
            "stdout_tail": "(timeout)",
        }


def full_ruff_check(target: str) -> int:
    """全 layer ruff check の violation 数 (= 0 が clean)."""
    full = REPO_ROOT / target
    if not full.exists():
        return -1
    result = subprocess.run(
        ["python", "-m", "ruff", "check", f"--select={FULL_RUFF_SELECT}", str(full)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
    )
    output = (result.stdout or "") + (result.stderr or "")
    m = re.search(r"Found (\d+) error", output)
    if m:
        return int(m.group(1))
    if "All checks passed" in output:
        return 0
    return -1


def run_round(samples: list[dict], mode: str) -> list[dict]:
    print(f"\n=== Round: {mode.upper()} ({len(samples)} samples) ===")
    results = []
    for sample in samples:
        print(f"  [{sample['id']}] starting...")
        r = run_nested_task(sample, mode)
        final_violations = full_ruff_check(r["target"])
        r["final_full_violations"] = final_violations
        results.append(r)
        print(
            f"  [{sample['id']}] exit={r['exit_code']} edits={r['edit_count']} "
            f"full_violations={final_violations} elapsed={r['elapsed_seconds']}s"
        )
    return results


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    samples = load_target_samples()
    print(f"target samples ({len(samples)}):")
    for s in samples:
        print(f"  - {s['id']} ({s['expected_detection']['rule_id']})")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    disable_hook()
    off_results = run_round(samples, "off")
    enable_hook()
    on_results = run_round(samples, "on")

    def avg_edits(results: list[dict]) -> float | None:
        vals = [r["edit_count"] for r in results if r["edit_count"] is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    def full_success(results: list[dict]) -> int:
        return sum(1 for r in results if r.get("final_full_violations") == 0)

    summary = {
        "timestamp": timestamp,
        "sample_count": len(samples),
        "off": {
            "avg_edit_count": avg_edits(off_results),
            "full_layer_success": full_success(off_results),
            "details": off_results,
        },
        "on": {
            "avg_edit_count": avg_edits(on_results),
            "full_layer_success": full_success(on_results),
            "details": on_results,
        },
    }

    log_file = LOG_DIR / f"log_auto_wide_{timestamp}.json"
    log_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== Summary saved to {log_file} ===")
    n = summary["sample_count"]
    off_succ = summary["off"]["full_layer_success"]
    on_succ = summary["on"]["full_layer_success"]
    off_avg = summary["off"]["avg_edit_count"]
    on_avg = summary["on"]["avg_edit_count"]
    print(f"OFF: avg_edits={off_avg}, full_layer_success={off_succ}/{n} ({off_succ/n*100:.1f}%)")
    print(f"ON : avg_edits={on_avg}, full_layer_success={on_succ}/{n} ({on_succ/n*100:.1f}%)")
    if off_succ is not None and on_succ is not None and n > 0:
        delta_pct = (on_succ - off_succ) / n * 100
        print(f"Delta: full_layer_success +{delta_pct:.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
