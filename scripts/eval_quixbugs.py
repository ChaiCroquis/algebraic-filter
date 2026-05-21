"""Neutral-corpus evaluation: AF detection rate on QuixBugs (external, not AF-designed).

QuixBugs (https://github.com/jkoppel/QuixBugs, MIT) = 40 classic algorithms with
a single-line bug each. It is NOT designed around AF's defect classes, so it
measures AF's REAL-WORLD hit rate free of the home-field bias of AF's own
samples/violations/ corpus.

Run (clone QuixBugs first, anywhere):
    git clone https://github.com/jkoppel/QuixBugs <path>
    python scripts/eval_quixbugs.py <path>/python_programs

Reports detection via AF's DIFFERENTIATING layers (Phase 2 algebraic-law +
Phase 3 data-movement). ruff lint (mostly ANN noise on QuixBugs' untyped code)
is excluded so the number reflects what AF *uniquely* catches, not annotation
noise.

Measured 2026-05-21: 1/38 = 3% (max_sublist_sum, via the "sum" name → monoid).
Contrast: AF's own corpus is 28/46 = 61%. The gap is the honest point — AF
detects STRUCTURE (algebraic-law / data-movement); general algorithmic bugs are
LOGIC bugs, structurally out of AF's scope. AF is a specialized verifier, not a
general bug-catcher.
"""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _detect_bugrelevant(path: str) -> tuple[bool, bool]:
    """Return (phase3_hit, phase2_hit) for one file — AF's differentiating layers."""
    from af_phase3.static_checker import check_file
    from af_phase4.phase2_runner import collect_phase2_failures

    try:
        p3 = bool(check_file(path))
    except Exception:
        p3 = False
    try:
        p2 = bool(collect_phase2_failures(path))
    except Exception:
        p2 = False
    return p3, p2


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python scripts/eval_quixbugs.py <QuixBugs>/python_programs")
        print("  (clone: git clone https://github.com/jkoppel/QuixBugs)")
        return 2
    # give AF its best shot
    os.environ.setdefault("AF_CROSSHAIR", "1")
    os.environ.setdefault("AF_HOOK_PHASE2_PBT", "1")

    progs = sorted(glob.glob(os.path.join(argv[1], "*.py")))
    progs = [p for p in progs if "test" not in os.path.basename(p) and "__init__" not in p]
    if not progs:
        print(f"no .py programs found under {argv[1]}")
        return 2

    p2 = p3 = both = 0
    caught: list[str] = []
    for p in progs:
        p3hit, p2hit = _detect_bugrelevant(p)
        p3 += p3hit
        p2 += p2hit
        if p3hit or p2hit:
            both += 1
            caught.append(os.path.basename(p))

    n = len(progs)
    print(f"=== QuixBugs neutral corpus (N={n} buggy programs) ===")
    print(f"AF differentiating layers (Phase2 algebraic / Phase3 data-movement): {both}/{n} = {round(100 * both / n)}%")
    print(f"  Phase3 {p3}/{n} | Phase2 {p2}/{n}")
    print(f"  caught: {caught}")
    print("\nNeutral 3% vs home-field 61% = AF detects STRUCTURE, not general LOGIC bugs.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
