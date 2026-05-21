"""Neutral mutation benchmark for AF's algebraic-law axis (Phase 2).

WHY THIS EXISTS
---------------
No public benchmark exists for "named functions that violate algebraic laws"
(confirmed by survey 2026-05-21; the closest, arXiv:2307.04346 PBT mutants,
measures PBT quality, not named-function law violation, and is not a reusable
corpus). AF's own 46-sample corpus is home-field (co-designed to match AF's
rules). This script builds a NEUTRAL corpus by *mechanical mutation testing*.

Why mutation testing rather than mining real library code: AF's Phase 2 law
templates hardcode function shapes (monoid = `list[int] -> int` reducer with
`sum` semantics; commutativity = binary `op(a, b)`). Real variadic library
functions (e.g. toolz.merge) do not fit those shapes without rewriting AF's
core. So the base operations here are CANONICAL textbook forms (`return a + b`
has no authorship freedom). Neutrality comes from four controls:

  1. Mechanical mutation (AOR — Arithmetic Operator Replacement, the standard
     cosmic-ray/mutmut operator), applied to EVERY BinOp, not cherry-picked.
  2. A name-gate CONTROL group: the identical mutated bodies under names AF's
     inferrer does NOT recognize (`thingy`/`doit`/`calc`). The recognized-minus-
     control gap isolates pure name-heuristic dependence.
  3. An INDEPENDENT oracle (deterministic exhaustive evaluation over a fixed
     integer domain), separate from AF's random hypothesis sampler, decides
     ground truth (does the variant actually break the law?).
  4. Adversarial FALSE-POSITIVE cases: functions correctly named (`merge`) but
     intentionally law-breaking by design (left/right-biased = non-commutative).
     AF flagging them is the documented two-sided error, measured here.

What it reports (per AF config — set AF_HOOK_PHASE2_PBT=1, optionally
AF_CROSSHAIR=1):
  - recognized-name detection rate on oracle-confirmed defects (TP / (TP+FN))
  - name-gate control detection (expected ~0 — quantifies the heuristic)
  - false-positive rate on oracle-correct variants
  - FP-by-intent rate on the adversarial legitimate-design set

Run:
    AF_HOOK_PHASE2_PBT=1 python scripts/eval_algebra_mutants.py
    AF_HOOK_PHASE2_PBT=1 AF_CROSSHAIR=1 python scripts/eval_algebra_mutants.py
"""
from __future__ import annotations

import ast
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Canonical base operations, written with EXPLICIT binary operators so the
# mechanical AOR mutator has operators to act on. {name} is filled per group.
# law_group selects the independent oracle. recognized/control names come from
# af_phase2/inferrer.py's _NAME_TO_LAWS table (recognized) and deliberately
# absent tokens (control).
_BASES = [
    # law_group,    recognized, control,  source template
    ("monoid", "total", "thingy",
     "def {name}(xs: list[int]) -> int:\n    acc = 0\n    for x in xs:\n        acc = acc + x\n    return acc\n"),
    ("commutativity", "combine", "doit",
     "def {name}(a: int, b: int) -> int:\n    return a + b\n"),
    ("commutativity", "average", "calc",
     "def {name}(a: int, b: int) -> int:\n    return (a + b) // 2\n"),
]

# Adversarial FP-by-intent: correctly named but legitimately law-breaking design.
# A left/right-biased merge is non-commutative ON PURPOSE; AF infers
# commutativity from the name `merge` and will flag it = false positive.
_ADVERSARIAL = [
    ("merge_right_biased", "def merge(a: int, b: int) -> int:\n    return b\n"),
    ("merge_left_biased", "def merge(a: int, b: int) -> int:\n    return a\n"),
]

_AOR_OPS = (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv)


def _mutants(source: str) -> list[str]:
    """All single-AOR mutants of source (replace each BinOp op with each other)."""
    tree = ast.parse(source)
    binops = [n for n in ast.walk(tree) if isinstance(n, ast.BinOp)]
    out: list[str] = []
    for idx, target in enumerate(binops):
        for new_op in _AOR_OPS:
            if isinstance(target.op, new_op):
                continue
            mutated = ast.parse(source)
            mutated_binops = [n for n in ast.walk(mutated) if isinstance(n, ast.BinOp)]
            mutated_binops[idx].op = new_op()
            out.append(ast.unparse(ast.fix_missing_locations(mutated)) + "\n")
    return out


def _compile_func(source: str, name: str):  # noqa: ANN202 - returns a callable
    namespace: dict[str, object] = {}
    exec(compile(source, "<variant>", "exec"), namespace)  # noqa: S102 - trusted local source
    return namespace[name]


_MONOID_TEST_LISTS = [[], [0], [1], [1, 2, 3], [5, -3, 2, 7], [10, 10], [-1, -2, -3, -4]]


def _oracle_violates(law_group: str, func) -> bool:  # noqa: ANN001
    """Independent ground truth: does func break the law AF infers for its name?

    Deterministic exhaustive evaluation, separate from AF's hypothesis sampler.
    """
    try:
        if law_group == "monoid":
            return any(func(xs) != sum(xs) for xs in _MONOID_TEST_LISTS)
        # commutativity
        return any(
            func(a, b) != func(b, a)
            for a in range(-5, 6)
            for b in range(-5, 6)
        )
    except Exception:
        # a mutant that raises (e.g. division by zero) is itself a defect
        return True


def _af_flags(source: str, name: str) -> bool:
    """True if AF Phase 2 (collect_phase2_failures, the hook path) flags it."""
    from af_phase4.phase2_runner import collect_phase2_failures

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / f"variant_{name}.py"
        path.write_text(source, encoding="utf-8")
        try:
            return bool(collect_phase2_failures(str(path)))
        except Exception:
            return False


@dataclass
class Tally:
    tp: int = 0
    fn: int = 0
    fp: int = 0
    tn: int = 0

    def add(self, *, violates: bool, flagged: bool) -> None:
        if violates and flagged:
            self.tp += 1
        elif violates and not flagged:
            self.fn += 1
        elif not violates and flagged:
            self.fp += 1
        else:
            self.tn += 1

    def detection(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom else 0.0

    def fp_rate(self) -> float:
        denom = self.fp + self.tn
        return self.fp / denom if denom else 0.0


def _evaluate_group(name: str, group_name: str, sources: list[str], law_group: str, tally: Tally) -> None:
    for src in sources:
        func = _compile_func(src, name)
        violates = _oracle_violates(law_group, func)
        flagged = _af_flags(src, name)
        tally.add(violates=violates, flagged=flagged)


def main() -> int:
    if not os.environ.get("AF_HOOK_PHASE2_PBT") and not os.environ.get("AF_CROSSHAIR"):
        print("set AF_HOOK_PHASE2_PBT=1 (and optionally AF_CROSSHAIR=1) to enable Phase 2")
        return 2

    recognized = Tally()
    control = Tally()
    for law_group, rec_name, ctrl_name, template in _BASES:
        base_src = template.format(name=rec_name)
        variants = [base_src, *_mutants(base_src)]
        _evaluate_group(rec_name, "recognized", variants, law_group, recognized)
        ctrl_src = template.format(name=ctrl_name)
        ctrl_variants = [ctrl_src, *_mutants(ctrl_src)]
        _evaluate_group(ctrl_name, "control", ctrl_variants, law_group, control)

    # adversarial FP-by-intent (recognized name, legitimately non-commutative)
    fp_intent_flagged = sum(1 for nm, src in _ADVERSARIAL if _af_flags(src, "merge"))

    cfg = []
    if os.environ.get("AF_HOOK_PHASE2_PBT"):
        cfg.append("sampling")
    if os.environ.get("AF_CROSSHAIR"):
        cfg.append("crosshair")
    print(f"=== AF Phase 2 neutral mutation benchmark (config: {'+'.join(cfg)}) ===")
    print("Recognized-name functions (inferrer fires):")
    print(f"  detection on oracle-confirmed defects: {recognized.tp}/{recognized.tp + recognized.fn}"
          f" = {round(100 * recognized.detection())}%   (TP={recognized.tp} FN={recognized.fn})")
    print(f"  false-positive rate on correct variants: {recognized.fp}/{recognized.fp + recognized.tn}"
          f" = {round(100 * recognized.fp_rate())}%   (FP={recognized.fp} TN={recognized.tn})")
    print("Name-gate CONTROL (identical bodies, unrecognized names):")
    print(f"  detection on oracle-confirmed defects: {control.tp}/{control.tp + control.fn}"
          f" = {round(100 * control.detection())}%   (expected ~0 — pure name heuristic)")
    print(f"Name-gate effect = {round(100 * recognized.detection())}% - "
          f"{round(100 * control.detection())}% = "
          f"{round(100 * (recognized.detection() - control.detection()))} pts of detection is name-dependent")
    print(f"FP-by-intent (legitimately non-commutative `merge`): {fp_intent_flagged}/{len(_ADVERSARIAL)} flagged")
    print("\nHonest reading: AF Phase 2 detects law violations ONLY on names its")
    print("inferrer recognizes; the same defect under another name passes clean,")
    print("and a legitimately law-breaking design under a recognized name is a FP.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
