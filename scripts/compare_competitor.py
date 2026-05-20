"""Reproducible competitor detection comparison: AF vs claude-code-quality-hook.

Measures **detection coverage** on the samples/violations/ corpus for:
  - AF stack:        ruff(PERF/SIM/FURB/ANN/F/RUF013) + Phase 3 AST + Phase 2 runtime PBT
  - competitor stack: ruff DEFAULT (no --select, = E/F) + pyright

This reproduces docs/evidence_summary.md §7. Run:
    python scripts/compare_competitor.py

Output: a timestamped JSON under docs/_comparison/ with per-sample detail +
aggregate counts, and a printed summary table.

Honesty notes (kept in the output):
  - The 46 samples are AF's home-field corpus (designed around AF's target
    defects), NOT a neutral benchmark. Numbers show defect-class targeting,
    not general superiority.
  - pyright is optional; if not installed the competitor pyright column is
    recorded as null (not 0) so the artifact never silently understates it.
  - Fix-success / competitor AI-repair pipeline is NOT measured here
    (requires permission-bypassed nested agents; see §7-2).
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

AF_RUFF_SELECT = "PERF,SIM,FURB,ANN,F,RUF013"
OUT_DIR = REPO_ROOT / "docs" / "_comparison"


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def _sample_paths() -> list[str]:
    paths = sorted(glob.glob(str(REPO_ROOT / "samples" / "violations" / "*.py")))
    return [p for p in paths if "__init__" not in p]


def _ruff_hits(samples: list[str], select: str | None) -> set[str]:
    hits: set[str] = set()
    base = ["python", "-m", "ruff", "check"]
    for s in samples:
        cmd = base + ([f"--select={select}"] if select else []) + [s]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            hits.add(_norm(s))
    return hits


def _safe_detect(checker, sample: str) -> bool:  # noqa: ANN001
    """Run a detector on one sample, swallowing any error (returns False)."""
    try:
        return bool(checker(sample))
    except Exception:
        return False


def _phase3_hits(samples: list[str]) -> set[str]:
    from af_phase3.static_checker import check_file

    return {_norm(s) for s in samples if _safe_detect(check_file, s)}


def _phase2_hits(samples: list[str]) -> set[str]:
    os.environ["AF_HOOK_PHASE2_PBT"] = "1"
    from af_phase4.phase2_runner import collect_phase2_failures

    return {_norm(s) for s in samples if _safe_detect(collect_phase2_failures, s)}


def _pyright_hits(samples: list[str]) -> set[str] | None:
    try:
        r = subprocess.run(
            ["python", "-m", "pyright", "--outputjson", *samples],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        data = json.loads(r.stdout)
    except Exception:
        return None
    hits: set[str] = set()
    by_base = {_norm(s).split("/")[-1]: _norm(s) for s in samples}
    for d in data.get("generalDiagnostics", []):
        if d.get("severity") in ("error", "warning"):
            base = d.get("file", "").replace("\\", "/").split("/")[-1]
            if base in by_base:
                hits.add(by_base[base])
    return hits


def main() -> int:
    samples = _sample_paths()
    n = len(samples)

    af_ruff = _ruff_hits(samples, AF_RUFF_SELECT)
    af_p3 = _phase3_hits(samples)
    af_p2 = _phase2_hits(samples)
    af_full = af_ruff | af_p3 | af_p2

    comp_ruff = _ruff_hits(samples, None)  # competitor uses ruff defaults
    comp_pyright = _pyright_hits(samples)
    comp_full = comp_ruff | (comp_pyright or set())

    af_only = sorted(x.split("/")[-1] for x in (af_full - comp_full))
    comp_only = sorted(x.split("/")[-1] for x in (comp_full - af_full))

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "corpus_size": n,
        "corpus_bias_disclosure": (
            "These 46 samples were designed by AF to showcase its target "
            "defects (algebraic-law / perf / data-movement). This is AF's "
            "home field, NOT a neutral benchmark. Numbers show defect-class "
            "targeting, not general superiority."
        ),
        "af_ruff_select": AF_RUFF_SELECT,
        "competitor_ruff_select": "(ruff defaults, no --select)",
        "pyright_available": comp_pyright is not None,
        "counts": {
            "af_ruff": len(af_ruff),
            "af_phase3": len(af_p3),
            "af_phase2": len(af_p2),
            "af_full": len(af_full),
            "competitor_ruff_default": len(comp_ruff),
            "competitor_pyright": None if comp_pyright is None else len(comp_pyright),
            "competitor_full": len(comp_full),
            "af_only": len(af_only),
            "competitor_only": len(comp_only),
            "overlap": len(af_full & comp_full),
        },
        "af_only_samples": af_only,
        "competitor_only_samples": comp_only,
        "not_measured": (
            "Fix-success rate and competitor's 3-stage AI-repair pipeline are "
            "NOT measured (competitor AI stage spawns permission-bypassed "
            "nested agents; harness safety prevents this). See §7-2."
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = record["timestamp"].replace(":", "").replace("-", "").replace("T", "_")
    out_path = OUT_DIR / f"competitor_comparison_{stamp}.json"
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"=== AF vs competitor detection comparison (N={n}) ===")
    print(f"competitor ruff (defaults): {len(comp_ruff)}")
    py_str = "N/A (pyright not installed)" if comp_pyright is None else str(len(comp_pyright))
    print(f"competitor pyright:         {py_str}")
    print(f"competitor full:            {len(comp_full)}/{n}")
    print(f"AF ruff ({AF_RUFF_SELECT}): {len(af_ruff)}")
    print(f"AF full:                    {len(af_full)}/{n}")
    print(f"AF-only: {len(af_only)} | competitor-only: {len(comp_only)} | overlap: {len(af_full & comp_full)}")
    print(f"\nsaved: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
