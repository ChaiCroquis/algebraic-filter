"""A/B 計測自動化 v2: nested claude --print で 5 task x 2 round 実走 (修正版).

v1 の致命的欠陥 2 点を修正:
  1. 測定場所が scratch/ だった -> scratch/*.py は pyproject の per-file-ignores
     ["ALL"] で全 ruff ルール無効 = hook の ruff 層が発火せず、 ruff_check_final も
     常に 0。 v2 は per-file-ignores 対象外の _ab_live/ に書く (= ruff 実発火)。
  2. プロンプトが欠陥名 + 修正指示を含んでいた (answer-leak) = hook OFF でも Claude が
     直してしまい OFF/ON 差が出ない。 v2 は neutral prompt (コードを書くだけ、 欠陥名・
     修正指示なし) -> OFF は違反を出荷、 ON は hook feedback で自己修正。

さらに intermediate task は ruff ルールでなく AF Phase 3 AST rule のため、 ruff でなく
af_phase3.static_checker.check_file で測定 (= 各 task をその所有 layer で計測)。

実走: cd algebraic-filter && python scripts/ab_automation.py
出力: docs/_ab_measurement/log_auto_v2_<timestamp>.json
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SETTINGS = REPO_ROOT / ".claude" / "settings.local.json"
SETTINGS_DISABLED = REPO_ROOT / ".claude" / "settings.local.json.disabled"
AB_LIVE = REPO_ROOT / "_ab_live"  # per-file-ignores 対象外 = ruff 実発火する throwaway dir
LOG_DIR = REPO_ROOT / "docs" / "_ab_measurement"
CLAUDE_CMD = r"C:\Users\user\AppData\Roaming\npm\claude.cmd"

# (tag, functional_goal, measure_kind, ruff_select) ; measure_kind in {"ruff", "phase3"}
# v3: 純粋な機能要件のみ (欠陥名なし / コード固定なし / anti-pattern 誘導なし)。
# AI は自由に実装でき、 hook feedback を指示と weigh せず取り込める = 自己修正効果を測れる。
TASKS = [
    ("perf401",
     "a function named double_positives(data) that returns a list containing each positive number from data, doubled",
     "ruff", "PERF"),
    ("sim103",
     "a function named is_positive(x) that returns whether x is greater than zero",
     "ruff", "SIM"),
    ("sim300",
     "a function named check_status(status) that returns the string 'ok' when status is zero, otherwise 'error'",
     "ruff", "SIM"),
    ("ann001",
     "a function named add(x, y) that returns the sum of x and y",
     "ruff", "ANN"),
    ("intermediate",
     "a function named transform(data) that returns a list of each positive number in data, doubled",
     "phase3", ""),
]


def disable_hook() -> None:
    if SETTINGS.exists():
        SETTINGS.rename(SETTINGS_DISABLED)


def enable_hook() -> None:
    if SETTINGS_DISABLED.exists():
        SETTINGS_DISABLED.rename(SETTINGS)


def _parse_edit_count(output: str) -> int | None:
    for pat in (
        r"Edit count[\s:：]+(\d+)",
        r"Edit\s+called\s+(\d+)\s+times?",
        r"(\d+)\s*回\s*Edit",
    ):
        m = re.search(pat, output)
        if m:
            return int(m.group(1))
    return None


def run_nested_task(tag: str, mode: str, goal: str) -> dict[str, object]:
    """nested claude --print で 1 task 実行 (v3 functional prompt = 機能要件のみ)."""
    target = f"_ab_live/_ab_{tag}_{mode}.py"
    prompt = (
        f"Write {goal}. Put it in the file {target}.\n"
        f"After the file exists, report how many times you called the Edit tool, "
        f"in the form 'Edit count: N'."
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
    except subprocess.TimeoutExpired:
        return {"tag": tag, "mode": mode, "target": target, "exit_code": -1,
                "elapsed_seconds": 300.0, "edit_count": None, "stdout_tail": "(timeout)"}
    elapsed = round(time.time() - start, 1)
    output = (result.stdout or "") + (result.stderr or "")
    return {
        "tag": tag,
        "mode": mode,
        "target": target,
        "exit_code": result.returncode,
        "elapsed_seconds": elapsed,
        "edit_count": _parse_edit_count(output),
        "stdout_tail": output[-800:],
    }


def measure_final(tag: str, kind: str, sel: str, target: str) -> dict[str, object]:
    """task 完了後の残存違反数を所有 layer で測定 (ruff は _ab_live で実発火)."""
    full = REPO_ROOT / target
    if not full.exists():
        return {"violations": -1, "raw": "(file not found)"}
    if kind == "phase3":
        sys.path.insert(0, str(REPO_ROOT))
        from af_phase3.static_checker import check_file
        try:
            n = len(check_file(str(full)))
        except Exception as exc:  # noqa: BLE001
            return {"violations": -1, "raw": f"phase3 error: {exc}"}
        return {"violations": n, "raw": f"phase3 intermediate-list-chain count={n}"}
    result = subprocess.run(
        ["python", "-m", "ruff", "check", f"--select={sel}", str(full)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=REPO_ROOT,
    )
    output = (result.stdout or "") + (result.stderr or "")
    m = re.search(r"Found (\d+) error", output)
    if m:
        return {"violations": int(m.group(1)), "raw": output[-300:]}
    if "All checks passed" in output:
        return {"violations": 0, "raw": "All checks passed"}
    return {"violations": -1, "raw": output[-300:]}


def run_round(mode: str) -> list[dict[str, object]]:
    print(f"\n=== Round: {mode.upper()} ===")
    results: list[dict[str, object]] = []
    for tag, goal, kind, sel in TASKS:
        print(f"  task {tag} ({mode}) ...")
        r = run_nested_task(tag, mode, goal)
        mf = measure_final(tag, kind, sel, str(r["target"]))
        r["final_violations"] = mf["violations"]
        r["final_raw"] = mf["raw"]
        r["measure_kind"] = kind
        results.append(r)
    return results


def _summarize(results: list[dict[str, object]]) -> dict[str, object]:
    clean = [r for r in results if r["final_violations"] == 0]
    edits = [r["edit_count"] for r in results if isinstance(r["edit_count"], int)]
    return {
        "clean_count": len(clean),
        "total": len(results),
        "avg_edit_count": round(sum(edits) / len(edits), 2) if edits else None,
        "total_surviving_violations": sum(
            r["final_violations"] for r in results if isinstance(r["final_violations"], int) and r["final_violations"] > 0
        ),
    }


def main() -> int:
    AB_LIVE.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {}
    try:
        disable_hook()
        off = run_round("off")
        enable_hook()
        on = run_round("on")
    finally:
        enable_hook()  # 異常終了でも hook を必ず復元
    summary = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S"),
        "design": "v3 functional-prompt (no defect name, no code pinning) + _ab_live (ruff fires) + per-layer measure",
        "off": {**_summarize(off), "details": off},
        "on": {**_summarize(on), "details": on},
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = LOG_DIR / f"log_auto_v3_{summary['timestamp']}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== SUMMARY ===")
    print(f"OFF surviving violations total: {summary['off']['total_surviving_violations']} | clean {summary['off']['clean_count']}/{summary['off']['total']}")
    print(f"ON  surviving violations total: {summary['on']['total_surviving_violations']} | clean {summary['on']['clean_count']}/{summary['on']['total']}")
    print(f"log: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
