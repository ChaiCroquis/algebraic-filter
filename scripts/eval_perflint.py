"""In-domain neutral-corpus evaluation: AF detection rate on perflint fixtures.

QuixBugs (eval_quixbugs.py) is the OUT-of-domain floor: general logic bugs that
AF is not designed to catch (3%). This script is the complementary IN-domain
measure: perflint (https://github.com/tonybaloney/perflint, MIT) is the
performance-anti-pattern linter that is the UPSTREAM SOURCE of ruff's PERF rules
AF already uses. Its functional fixtures (unnecessary list() cast, dict.items()
discarding key/value, list-copy, loop-invariant) are exactly the data-movement
micro-anti-patterns AF's Phase 1 PERF + Phase 3 AST target -- but they are
authored by perflint's author to match perflint's rules, NOT by AF to match AF's
rules, so they are a genuine neutral corpus free of AF's home-field bias.

Run (clone perflint first, anywhere):
    git clone https://github.com/tonybaloney/perflint <path>
    python scripts/eval_perflint.py <path>/tests/functional

Reports detection via AF's perf-relevant layers:
  - Phase 1 ruff PERF/SIM/FURB (ANN/F annotation noise excluded, same as the
    QuixBugs eval -- the fixtures are untyped)
  - Phase 3 data-movement AST (AF's own contribution, independent of ruff)

The point of the pair: AF detects STRUCTURE. On in-domain neutral data (perf
anti-patterns) it performs well; on out-of-domain neutral data (QuixBugs logic
bugs) it floors at 3%. Both numbers are honest and complementary.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# perf-relevant Phase 1 rules only -- ANN/F are annotation/undefined-name noise
# on untyped fixtures (mirrors eval_quixbugs.py excluding ANN).
_PERF_SELECT = "PERF,SIM,FURB"


def _ruff_perf_hit(path: str) -> bool:
    """True if ruff flags any PERF/SIM/FURB violation in this file."""
    try:
        proc = subprocess.run(
            ["ruff", "check", f"--select={_PERF_SELECT}", "--quiet", path],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    return bool(proc.stdout.strip())


def _phase3_hit(path: str) -> bool:
    """True if AF's Phase 3 data-movement AST checker flags this file."""
    from af_phase3.static_checker import check_file

    try:
        return bool(check_file(path))
    except Exception:
        return False


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python scripts/eval_perflint.py <perflint>/tests/functional")
        print("  (clone: git clone https://github.com/tonybaloney/perflint)")
        return 2

    progs = sorted(glob.glob(os.path.join(argv[1], "*.py")))
    progs = [p for p in progs if "__init__" not in p]
    if not progs:
        print(f"no .py fixtures found under {argv[1]}")
        return 2

    results = [(p, _ruff_perf_hit(p), _phase3_hit(p)) for p in progs]
    perf = sum(1 for _, perf_hit, _p3 in results if perf_hit)
    p3 = sum(1 for _, _pf, p3_hit in results if p3_hit)
    caught = [os.path.basename(p) for p, perf_hit, p3_hit in results if perf_hit or p3_hit]
    both = len(caught)

    n = len(progs)
    print(f"=== perflint in-domain neutral corpus (N={n} fixture files) ===")
    print(f"AF perf-relevant layers (Phase1 PERF/SIM/FURB + Phase3 AST): {both}/{n} = {round(100 * both / n)}%")
    print(f"  Phase1 PERF/SIM/FURB {perf}/{n} | Phase3 AST {p3}/{n}")
    print(f"  caught: {caught}")
    print("\nIn-domain (perf anti-patterns) vs out-of-domain QuixBugs 3% = AF detects STRUCTURE.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
