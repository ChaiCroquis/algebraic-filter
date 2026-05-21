"""Miss-driven improvement loop: run AF, collect misses, separate clustered vs tail.

The loop (chai's design): run AF over a labeled corpus of known-violation
functions, collect false negatives (misses), and SEPARATE each miss into:

  - clustered     = bulk-fixable by a clean lever (type -> pyright, perf -> ruff,
                    boundary -> wider strategy, intent-named algebra -> keyword
                    extension). Loop has high ROI here.
  - non-clustered = hard tail (intent-less name, no clean low-FP fix; only
                    explicit declaration opt-in). Loop asymptotes here.

It prints the clustered : non-clustered RATIO — the decision metric for whether
the loop is worth continuing on a given corpus.

Run:
    python scripts/miss_loop.py                 # built-in illustrative corpus
    python scripts/miss_loop.py corpus.json     # external labeled corpus

External corpus format (JSON): a list of
    {"id": str, "code": str, "violation_type": str, "function_name": str}
where violation_type in: algebra-assoc | algebra-commut | algebra-idem |
type-error | perf | boundary.

HONEST CAVEAT: the built-in corpus is hand-built and its names overlap the
classifier's intent-synonym list (co-design), so its ratio is ILLUSTRATIVE,
not a population estimate. Run on an independent labeled corpus for a real
ratio — that is the whole point of tool-ifying this.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

SELECT_RULES = "PERF,SIM,FURB,ANN,F,RUF013"

# Names carrying algebraic intent. Keep in sync conceptually with
# af_phase2.inferrer._NAME_TO_LAWS (recognized) + reasonable extension synonyms.
_INTENT_NAMES = {
    "sum", "fold", "reduce", "aggregate", "concat", "tally", "accumulate",
    "total", "add", "plus", "gather", "collect", "map", "fmap", "transform",
    "merge", "average", "intersect", "union", "combine", "blend", "mix",
    "normalize", "canonicalize", "dedup", "sanitize",
}


def classify_miss(violation_type: str, function_name: str) -> tuple[bool, str]:
    """Separate a miss into clustered (bulk-fixable) vs non-clustered (hard tail).

    Returns (is_clustered, fix_path).
    """
    tokens = set(function_name.lower().replace("-", "_").split("_"))
    if violation_type == "type-error":
        return True, "pyright (hybrid) — clean bulk fix"
    if violation_type == "perf":
        return True, "ruff rule — clean bulk fix"
    if violation_type == "boundary":
        return True, "widen hypothesis strategy range — clean bulk fix"
    if violation_type.startswith("algebra"):
        if tokens & _INTENT_NAMES:
            return True, "keyword extension (name carries intent) — bulk fix"
        return False, "hard tail (no intent signal; structural=90% FP / explicit-declaration opt-in only)"
    return False, "hard tail (unclassified)"


def af_detects(code: str) -> bool:
    """True if any AF layer (ruff Phase1 / Phase3 AST / Phase2 PBT) flags the code."""
    from af_phase3.static_checker import check_file
    from af_phase4.phase2_runner import collect_phase2_failures

    os.environ.setdefault("AF_HOOK_PHASE2_PBT", "1")
    tmp = Path(tempfile.mkdtemp()) / "probe.py"
    tmp.write_text(code, encoding="utf-8")
    ruff = subprocess.run(
        ["python", "-m", "ruff", "check", f"--select={SELECT_RULES}", str(tmp)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if ruff.returncode != 0:
        return True
    try:
        if check_file(str(tmp)):
            return True
    except Exception:
        pass
    try:
        if collect_phase2_failures(str(tmp)):
            return True
    except Exception:
        pass
    return False


def _builtin_corpus() -> list[dict[str, str]]:
    sub = "import functools\ndef {n}(xs: list[int]) -> int:\n    return functools.reduce(lambda a, b: a - b, xs, 0)\n"
    com = "def {n}(a: int, b: int) -> int:\n    return a - b\n"
    typ = "def {n}(x: int) -> str:\n    return x + 1\n"
    perf = "def {n}(data: list[int]) -> list[int]:\n    r = []\n    for x in data:\n        if x > 0:\n            r.append(x * 2)\n    return r\n"
    def mk(tmpl: str, vtype: str, names: tuple[str, ...]) -> list[dict[str, str]]:
        return [
            {"id": n, "code": tmpl.format(n=n), "violation_type": vtype, "function_name": n}
            for n in names
        ]

    return [
        *mk(sub, "algebra-assoc", ("my_sum", "tally", "accumulate_total", "thingy", "process_items")),
        *mk(com, "algebra-commut", ("merge", "blend", "do_op")),
        *mk(typ, "type-error", ("coerce", "convert", "head")),
        *mk(perf, "perf", ("dbl", "scale_up")),
    ]


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        corpus = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        source = argv[1]
    else:
        corpus = _builtin_corpus()
        source = "built-in (ILLUSTRATIVE — not a population estimate)"

    print(f"=== miss-loop over corpus: {source} (N={len(corpus)}) ===")
    misses: list[dict[str, str]] = []
    caught = 0
    for row in corpus:
        if af_detects(row["code"]):
            caught += 1
        else:
            misses.append(row)

    print(f"detected {caught}/{len(corpus)} | misses {len(misses)}\n")
    print("=== separation (clustered = bulk-fixable / non-clustered = hard tail) ===")
    clustered = non_clustered = 0
    for m in misses:
        is_cl, path = classify_miss(m["violation_type"], m["function_name"])
        clustered += is_cl
        non_clustered += not is_cl
        tag = "CLUSTERED " if is_cl else "NON-CLUST."
        print(f"  {m['function_name']:18s} [{m['violation_type']:14s}] {tag}: {path}")

    total = clustered + non_clustered
    if total:
        print(
            f"\n=== ratio: clustered {clustered}/{total} = {round(100 * clustered / total)}% "
            f": non-clustered {non_clustered}/{total} = {round(100 * non_clustered / total)}% ==="
        )
        print("(clustered = where the loop has high ROI; non-clustered = irreducible tail)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
