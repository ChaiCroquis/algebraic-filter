"""Sample file to see both hybrid hooks fire.

Ask Claude to "fix the issues in scratch/try_me.py" and watch:
  - base (pyright) flag the return-type mismatch in first_positive
  - algebraic-filter flag the monoid-law violation in total (named like a sum
    but subtracts) + the PERF401 manual-append loop in double_positives

(Phase 2 algebraic-law detection requires phase2_runtime=true in
.algebraic-filter.json, or AF_HOOK_PHASE2_PBT=1.)
"""
import functools


def total(xs: list[int]) -> int:
    # named like a sum (associative monoid with identity 0) but subtracts
    return functools.reduce(lambda a, b: a - b, xs, 0)


def double_positives(data: list[int]) -> list[int]:
    result = []
    for x in data:
        if x > 0:
            result.append(x * 2)
    return result


def first_positive(xs: list[int]) -> int:
    for x in xs:
        if x > 0:
            return x
    return None  # type error: annotated -> int but returns None
