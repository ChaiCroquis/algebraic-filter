#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PostToolUse hook for algebraic-filter (AF) — Phase 1 + Phase 3 統合版.

Claude Code が Write / Edit / MultiEdit で .py file を更新した直後に発火する。
  Phase 1 layer: ruff PERF/SIM/FURB/ANN/F の標準静的検査
  Phase 3 layer: af_phase3.static_checker による data movement violation 検出
            (中間 list chain / dict.keys() list / explicit copy / string concat in loop)

違反検出時 exit code 2 + JSON で additionalContext を Claude に注入する.

仕様 (Claude Code Hook API、 2026 年初頭):
  stdin  : JSON event (tool_name / tool_input.file_path / etc.)
  stdout : (optional) JSON response with decision / additionalContext
  exit 0 : allow (違反なし or 非対象)
  exit 2 : block with feedback (Phase 1 or Phase 3 違反検出)
"""
from __future__ import annotations

import contextlib
import json
import subprocess
import sys
from pathlib import Path

# AF プロジェクト root を sys.path に追加 (af_phase3 import 用)
_HOOK_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _HOOK_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from af_phase3.static_checker import check_file as _phase3_check_file  # type: ignore
except Exception:
    _phase3_check_file = None  # type: ignore

try:
    from af_phase4.anti_pattern_tracker import (  # type: ignore
        get_preemptive_hints as _phase4_get_hints,
        record_violations as _phase4_record,
    )
    from af_phase4.feedback_formatter import (  # type: ignore
        combine_violations as _phase4_combine,
        shape_violation_for_output as _phase4_shape,
    )
except Exception:
    _phase4_get_hints = None  # type: ignore
    _phase4_record = None  # type: ignore
    _phase4_combine = None  # type: ignore
    _phase4_shape = None  # type: ignore

try:
    from af_phase4.phase2_runner import (  # type: ignore
        collect_phase2_failures as _phase2_collect,
        is_enabled as _phase2_enabled,
    )
except Exception:
    _phase2_collect = None  # type: ignore
    _phase2_enabled = None  # type: ignore


# RUF013 (implicit-optional) を追加 = competitor (pyright) との比較実測で判明した
# 型安全 gap を 1 件閉じる (= ruf013_implicit_optional sample)。
# RUF 全体は RUF002 (docstring unicode ambiguity) の false-positive を生むため、
# RUF013 のみ pin 追加 (fixed/ ground-truth で FP ゼロを実測確認、 2026-05-20)。
SELECT_RULES = "PERF,SIM,FURB,ANN,F,RUF013"
MAX_FEEDBACK_CHARS = 2000


def _read_event() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def _run_ruff(file_path: str) -> tuple[int, str]:
    result = subprocess.run(
        ["python", "-m", "ruff", "check", f"--select={SELECT_RULES}", file_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def _run_phase3(file_path: str) -> list:
    if _phase3_check_file is None:
        return []
    try:
        return _phase3_check_file(file_path)
    except Exception:
        return []


def _run_phase2(file_path: str) -> list:
    """Phase 2 PBT runner (opt-in via env var AF_HOOK_PHASE2_PBT)."""
    if _phase2_collect is None or _phase2_enabled is None:
        return []
    if not _phase2_enabled():
        return []
    try:
        return _phase2_collect(file_path)
    except Exception:
        return []


def _format_feedback(
    file_path: str,
    ruff_output: str,
    phase3_violations: list,
    phase2_failures: list | None = None,
) -> dict:
    parts = [
        "## AF hook (algebraic-filter) detected violations",
        "",
        f"file: `{file_path}`",
        "",
    ]

    # Phase 4 構造化 payload (= 統一 schema 化、 Claude が parse しやすい形)
    structured: list = []
    rule_ids: list[str] = []
    if _phase4_combine is not None:
        try:
            structured = _phase4_combine(
                ruff_output, phase3_violations, file_path, phase2_failures
            )
            rule_ids = [v["violation_law"] for v in structured]
        except Exception:
            structured = []
            rule_ids = []

    if structured:
        parts.extend(["### Phase 4 — structured violations (layer-unified)", ""])
        for v in structured[:10]:
            if _phase4_shape is not None:
                parts.extend(_phase4_shape(v))
            else:
                parts.append(
                    f"- **{v['violation_law']}** ({v['layer']}) at `{v['violation_location']}`"
                )
                parts.append(f"  - skeleton: {v['alternative_skeleton']}")
                parts.append(f"  - fix example: `{v['fix_example']}`")
        parts.append("")

    # Phase 4 anti-pattern tracker: 違反を history に記録 + pre-emptive hint 取得
    hints: list[str] = []
    if _phase4_record is not None and rule_ids:
        with contextlib.suppress(Exception):
            _phase4_record(rule_ids, file_path)
    if _phase4_get_hints is not None and rule_ids:
        try:
            hints = _phase4_get_hints(rule_ids)
        except Exception:
            hints = []

    if hints:
        parts.extend(["### Phase 4 — pre-emptive hints (repeated violation alert)", ""])
        parts.extend(f"- {h}" for h in hints)
        parts.append("")

    # 旧 Phase 1 raw output + Phase 3 list は補助として残置 (互換性)
    if ruff_output.strip():
        parts.extend([
            "### Phase 1 raw (ruff output)",
            "",
            "```",
            ruff_output[:MAX_FEEDBACK_CHARS],
            "```",
            "",
        ])
    if phase3_violations:
        parts.extend(["### Phase 3 raw (AST violations)", ""])
        parts.extend(
            f"- `{v.rule_id}` (line {v.line}): {v.message}"
            for v in phase3_violations[:10]
        )
        parts.append("")

    parts.extend([
        "### Action",
        "- Apply the suggested skeleton + fix example from Phase 4 structured section.",
        "- If pre-emptive hint appeared, review the alternative skeleton before re-writing.",
        "- Re-write the file and AF will re-check.",
    ])
    return {
        "decision": "block",
        "reason": "algebraic-filter detected violations in AI-written code",
        "additionalContext": "\n".join(parts),
    }


def main() -> int:
    event = _read_event()
    tool_name = event.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return 0

    tool_input = event.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path.endswith(".py"):
        return 0

    ruff_rc, ruff_output = _run_ruff(file_path)
    phase3_violations = _run_phase3(file_path)
    phase2_failures = _run_phase2(file_path)

    has_phase1_violation = ruff_rc != 0
    has_phase3_violation = bool(phase3_violations)
    has_phase2_violation = bool(phase2_failures)

    if (
        not has_phase1_violation
        and not has_phase3_violation
        and not has_phase2_violation
    ):
        return 0

    feedback = _format_feedback(
        file_path,
        ruff_output if has_phase1_violation else "",
        phase3_violations,
        phase2_failures if has_phase2_violation else None,
    )
    print(json.dumps(feedback, ensure_ascii=False), file=sys.stdout)
    return 2


if __name__ == "__main__":
    sys.exit(main())
