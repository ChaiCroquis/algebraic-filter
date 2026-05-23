# Limitations & boundaries (measured)

[日本語版](limitations.ja.md)

An honest, measured map of what algebraic-filter (AF) can do, what is an
extension, and what is structurally out of scope. All rows are backed by a
probe you can reproduce (see [Reproduce](#reproduce)).

> One-line boundary: **AF verifies *structure* (algebraic laws / data movement /
> lint), not *intent* (whether the code matches the spec).** It can tell that
> `average` should be commutative; it cannot tell whether `average` should add 1.

## What "verification" precisely means

Two points that are easy to over-read:

**1. What Phase 2 guarantees — law-level, not correctness, and name-gated.**
Phase 2 checks whether a function satisfies an algebraic *law* (e.g. `sum` is
associative, `average` is commutative), not whether it is correct. "Satisfies
the law" ≠ "matches the spec": a commutative `average` that wrongly adds 1 still
passes. The guarantee has three conditions, all required:

- the inferrer **recognizes the name** (otherwise no law is checked at all);
- only the **law inferred from that name** is checked (`merge` → commutativity
  only; a broken associativity on `merge` is not checked);
- strength is two-tier — **hypothesis sampling = probabilistic confidence, not
  proof** (a violation that only shows on rare inputs can be missed); **CrossHair
  (opt-in) = deterministic proof, but bounded** to binary functions, for **7 of
  14 law templates** (associativity, semigroup-assoc, commutativity, additive
  identity, binary idempotence, eq-reflexivity, eq-symmetry; the other 7 —
  functor/monad/foldable — stay sampling-only).

Precise sentence: *Phase 2 guarantees that a recognized-name function satisfies
its inferred law, at sampling confidence (or CrossHair proof where applicable).*
Strong, but conditional and narrow.

**2. Coverage is decided by defect CLASS, not by difficulty.**
Whether AF catches a bug depends on its kind, not how hard it is — a hard bug of
the right class is caught; an easy bug of the wrong class passes clean.

- **In class (caught — AF's usable niche):** algebraic-law violations,
  data-movement inefficiency, lint (PERF/SIM/FURB/F/RUF), types (pyright in
  hybrid mode).
- **Out of class (passes → route to another tool):** general logic bugs,
  security, concurrency, spec intent, and law violations on unrecognized names.

The algebraic-law class alone carries an **extra double gate** the others do not:
**a recognized name AND the bug manifesting as a violation of the inferred law.**

## ① What it does (measured true positives)

| Capability | Layer | Notes |
|---|---|---|
| Lint defects: PERF / SIM / FURB / ANN / F / RUF013 | 1 (ruff) | ~16 ms via the ruff binary |
| Data movement: intermediate-list-chain / dict-keys-list / explicit-copy / string-concat-in-loop | 3 (AST) | + tracemalloc runtime. **Evidence-gated** (P3): explicit-copy fires only on a copy *chain* (≥2 ops), not a lone defensive `x.copy()`; string-concat needs str evidence. Known residual FP: `dict-keys-list` flags any `list(x.keys())`, so a deliberate snapshot of a non-dict is a false positive (no type info to gate). |
| Algebraic-law violations (Monoid / Functor / Monad / …) | 2 (hypothesis) | **only on keyword-named functions** — see ③ |
| Purity / determinism (no global·nonlocal·I/O·random/time/uuid) | static AST (`af_phase3/purity_checker.py`) | D4: decides "no first-order impurity" without executing — a default-level deterministic guarantee (purity underwrites algebraic-law reasoning). **Sound but not complete**: catches first-order signals only, not impurity via a called function or in-place arg mutation. |
| Structured feedback → Claude self-correction | 4 | clean re-measurement (2026-05-22): OFF 0/5 → ON 5/5 clean, ANN-dominated, small-n own tasks (the earlier 20→100%/91.7→100% is retracted — see evidence_summary §1) |

On AF's own 46-sample corpus: full-stack detection **28/46 (61%)**.

> **Neutral-corpus check (no home-field bias)** — two external corpora, measured
> 2026-05-21, both reproducible (see [Reproduce](#reproduce)). The honest
> gradient by domain match:
>
> | Corpus | Domain match | Detection | Note |
> |---|---|---|---|
> | [QuixBugs](https://github.com/jkoppel/QuixBugs) (MIT, 38 algo bugs) | **out-of-domain** (logic bugs) | **1/38 = 3%** | floor — `scripts/eval_quixbugs.py` |
> | [perflint](https://github.com/tonybaloney/perflint) (MIT, 8 fixtures) | **in-domain** (perf anti-patterns) | **2/8 = 25%** (= 2/6 = 33% of what perflint itself flags) | `scripts/eval_perflint.py` |
> | AF's own 46 samples | home-field (co-designed) | **28/46 = 61%** | upper bound |
>
> 3% → 25/33% → 61% is the honest point, not a defect. QuixBugs bugs are general
> **logic** bugs, structurally outside AF's **structure** axis (floor). perflint
> is in-domain but a *superset* of AF's coverage — AF catches the ruff-ported
> subset (PERF101/102/401-403) but not perflint-only categories (use-tuple,
> loop-invariant-statement, memoryview). The home-field 61% is the co-designed
> ceiling. AF is a specialized structural verifier, not a general bug-catcher.
>
> **The neutral corpus also did its de-biasing job**: perflint's `global_usage`
> fixture (a `float` accumulator `total += i`) was a *false positive* of the
> Phase 3 `string-concat-in-loop` rule (it matched any `x += …` in a loop with
> no type evidence). Fixed 2026-05-21 by gating on str evidence (literal/f-string
> init, `str()`, or `: str` annotation); regression-guarded by
> `test_phase3_string_concat_no_fp_on_numeric_accumulator`.

## ② Extensible (reachable with work)

| Gap | Effort |
|---|---|
| Inferrer keyword coverage (`mean` / `compute` / `process` currently skipped) | small — add keywords (synonyms `add`/`plus`/`total`/`accumulate` already added) |
| More algebraic laws (beyond the current 13) | small–medium |
| Type-checking (pyright) | **already available** via the hybrid / Docker mode |
| SMT proof (CrossHair) of binary laws | **already available** opt-in (`AF_CROSSHAIR`); now covers **7 of 14 law templates** (assoc, semigroup-assoc, commutativity, monoid identity — additive 0 by default or a declared element via `@law("monoid_identity", identity=e)`, e.g. mult e=1 / str-concat e="" —, binary idempotence, eq-reflexivity, eq-symmetry — thickened 3→5→7 on 2026-05-22/24). Cost **type-dependent — ~0.3 s for int, ~8 s for str/dict/complex** (measured 2026-05-21). Works on int/float/str/dict/branches/loops/recursion; functor/monad/foldable laws still hypothesis-only |
| Contract proof (pre/post conditions) | **available** opt-in (D5): `@contract(post="result >= 0", pre="b >= 0")` is proved by CrossHair (`verify_contract`) — extends deterministic verification beyond algebraic laws to any decidable stated property (e.g. `len(out) == len(inp)`). Same SMT engine + cost profile |
| Other languages (TypeScript / Rust) | large — different ecosystems; Rust's trait system fits the algebra axis best |

## ③ Structurally out of scope (measured misses)

Probes fed deliberately-defective code and recorded the hook's exit code
(`AF_HOOK_PHASE2_PBT=1`). `exit 0` = miss (clean pass):

| Defect probe | Result |
|---|---|
| off-by-one (`xs[len(xs)]`) | exit 0 — **miss** |
| type error (`-> str` returns int), AF alone | exit 0 — **miss** (pyright covers it in hybrid) |
| security (`eval(user_input)`) | exit 0 — **miss** |
| concurrency / shared mutable aliasing | exit 0 — **miss** |
| **monoid violation on a non-keyword-named function** (`thingy` that subtracts) | exit 0 — **miss** |
| semantic bug on a keyword-named function (`my_average` that adds 1) | exit 2 — caught (because `average` → commutativity, and +1 broke it) |

The last two rows are the key nuance: AF catches a semantic bug **only when it
manifests as an algebraic-law violation on a function whose name the inferrer
recognizes**. Rename the function and the same bug passes clean.

### Phase 2 inferrer is a name heuristic, not semantic understanding

Measured keyword coverage over 32 common function names: **16/32 = 50%**
trigger law inference (was 12/32 = 38% before the 2026-05-21 miss-loop
iteration2 improvement — monoid/commutativity synonyms added + word-boundary
matching).

- Recognized (✓): `sum` `total` `add` `plus` `accumulate` `merge` `concat`
  `combine` `union` `fold` `reduce` `aggregate` `fmap` `map` `transform`
  `average` (+ synonyms `tally` `gather` `collect` `blend` `mix`)
- Still skipped (·): `join` `apply` `compose` `mean` `max` `min` `count`
  `sort` `filter` `compute` `process` `handle` `calc` `thingy` …

> **Precision fix (same change)**: matching is now **word-boundary** (token),
> not substring. This removed pre-existing false matches measured before the
> fix: `consume`/`summary`/`assume` → no longer matched `sum`;
> `remap`/`transformer` → no longer matched `map`/`transform`; `combiner` →
> no longer matched `combine`. So this iteration **raised recall (38→50%) AND
> cut false positives** at once.

> **Deferred (measured)**: idempotence synonyms (`normalize`/`canonicalize`/
> `dedup`/`sanitize`) were NOT added — they emit `ERROR` (not clean PASS)
> because the `idempotence` law template is not robust for arbitrary-typed
> unary functions. Adding them would create false positives; deferred until
> the template is hardened.

Consequence — Phase 2 has **two-sided error**:
- **false negatives**: a real law violation on a non-recognized name (e.g.
  `add` that isn't associative) is missed.
- **false positives**: a function correctly named `merge` but intentionally
  *not* commutative (e.g. left-biased merge) would be flagged.

> **Precision fix — declaration as an OPT-IN path (P1, 2026-05-22)**: an
> *opt-in* way to verify a *declared* law instead of guessing from the name. Two
> decorators (`af_phase2.inferrer`):
> - `@law("commutativity")` — verifies the declared law, **name-independent**
>   (catches the false-negative *for declared functions*, e.g. `thingy`).
> - `@no_law` (or `@law()`) — declares "no law", suppressing the name heuristic
>   (removes the false-positive *for declared functions*, e.g. a deliberately
>   non-commutative `merge`).
>
> **Honest scope — this does NOT change the default.** Declared laws take
> priority; undeclared functions still use the name heuristic. So the two-sided
> error is **closed only for functions that opt in to declaration, not rooted out
> by default**. The neutral mutation benchmark — which declares nothing — is
> **unchanged**: name-gate effect still 100%, FP-by-intent still 2/2
> (re-measured 2026-05-24). What the unit tests prove is that the declaration
> *mechanism* works (`test_af_phase2_declared_laws.py`), not that the default
> behaviour improved. Declaration is a capability you reach for, not an automatic
> fix.

> **Neutral mutation benchmark (no home-field bias), measured 2026-05-21** via
> `scripts/eval_algebra_mutants.py`. No public corpus of "named functions that
> violate algebraic laws" exists (survey confirmed), so this is a *mechanical
> mutation* benchmark: canonical operations (`return a + b` etc.) under standard
> AOR mutation, with an independent deterministic oracle and a name-gate control
> group. Result (identical under `sampling` and `sampling+crosshair`):
>
> | Measure | Result | Reading |
> |---|---|---|
> | Detection on recognized names (oracle-confirmed defects) | **7/7 = 100%** | precise + complete *within* the niche |
> | False positives on still-correct mutants (recognized) | **0/8 = 0%** | does not over-flag correct code |
> | Detection on name-gate **control** (identical bugs, unrecognized names) | **0/7 = 0%** | the same defect renamed passes clean |
> | **Name-gate effect** | **100 pts** | *all* of Phase 2's detection is name-dependent |
> | FP-by-intent (legitimately non-commutative `merge`) | **2/2 flagged** | the false-positive arm, quantified |
>
> The honest summary: Phase 2 is a **precise but entirely name-gated** verifier.
> Inside the recognized niche it is 100%/0% (catch/FP) on mechanical mutants;
> outside it (renamed, or legitimately law-breaking by design) it is structurally
> blind or wrong. This is the algebraic-law analogue of the QuixBugs 3% floor:
> capability is real but niche-bounded. Guarded by
> `test_phase2_name_gate_property`.

## Two honest records (A/B re-measurement, 2026-05-22)

Open judgment calls, recorded in the open rather than buried:

1. **The A/B self-correction headline was wrong, and is retracted.** The earlier
   "+80% / +8.3% pass@1" was measured in `scratch/` — where `per-file-ignores =
   ["ALL"]` disables ruff even with explicit `--select`, so the hook's ruff layer
   never fired — and with prompts that named the defect (so hook-OFF "fixed" too).
   The clean re-measurement (functional prompts in `_ab_live/`, full select) is
   **OFF 0/5 → ON 5/5 clean (11→0 violations), driven almost entirely by the
   type-annotation (ANN) axis** — a real but modest, ANN-dominated effect on a
   capable model, not a +80% boost. Read it as a guarantee (no AF-detectable
   violation ships), not a delta. Full correction:
   [evidence_summary.md](evidence_summary.md) §1.
2. **The hook is advisory, not a hard gate.** Its `exit 2` feedback is weighed
   against user intent: if you instruct "write exactly this code," the model keeps
   it despite the hook (measured: ON = OFF = 7). AF improves outcomes when the
   instruction leaves room to revise, and *informs* (does not *force*) otherwise.

## The honest takeaway

AF's value is **automatic structural guardrails**; spec/intent correctness
remains the job of tests, human review, and (for types) pyright. "Out of scope"
here is a deliberate niche boundary, not a defect: AF guards the structure
axis well within its niche, and routes everything else to the appropriate tool.

## Reproduce

```bash
# false-negative probes (buggy code outside AF's defect classes)
# inferrer keyword coverage
# both were run inline 2026-05-21; the exact probe code is in this commit message
python -m pytest samples/violations/tests/   # positive-side coverage (117 passed)
python scripts/compare_competitor.py          # AF vs competitor detection (28/46 vs 7/46)
python scripts/miss_loop.py                   # miss separation: clustered (bulk-fixable) vs hard tail ratio
python scripts/miss_loop.py my_corpus.json    # ...on YOUR labeled corpus (escapes the built-in co-design bias)
# neutral external corpora (no home-field bias) — the honest gradient
git clone https://github.com/jkoppel/QuixBugs C:/work/_quixbugs        # out-of-domain
python scripts/eval_quixbugs.py C:/work/_quixbugs/python_programs      # 1/38 = 3%
git clone https://github.com/tonybaloney/perflint C:/work/_perflint   # in-domain
python scripts/eval_perflint.py C:/work/_perflint/tests/functional    # 2/8 = 25%
# algebraic-law axis: neutral mechanical mutation benchmark (no external clone)
AF_HOOK_PHASE2_PBT=1 python scripts/eval_algebra_mutants.py           # recognized 100% / control 0%
```

See also [evidence_summary.md](evidence_summary.md) (positive evidence) and
[hybrid_setup.md](hybrid_setup.md) (covering the type-check gap via pyright).
