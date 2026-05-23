# Evidence Summary — algebraic-filter verification results

[日本語版 evidence_summary](evidence_summary.ja.md)

Evidence collected across each Phase + A/B measurement, with Phase 1 withdrawal-criterion check.

---

## 1. A/B measurement results (in-vivo AF effect)

> **Correction (2026-05-22)** — the earlier "+80% / +8.3% pass@1" figures are
> **RETRACTED as unreliable**. Three compounding flaws, found by actually running
> the measurement:
> 1. **Location**: files were written to `scratch/`, where `pyproject.toml`'s
>    `[tool.ruff.lint.per-file-ignores] "scratch/*.py" = ["ALL"]` disables every
>    ruff rule even with explicit `--select`. So the hook's ruff layer never fired
>    there, and `ruff_check_final` always returned 0 (verified: a PERF401 file in
>    `scratch/` is not blocked; the same file at repo root is).
> 2. **Answer-leak**: prompts named the defect ("then fix the PERF401 violation"),
>    so hook-OFF "fixed" too.
> 3. **Internal inconsistency**: the published 5-task table (OFF 1/5) did not match
>    the automation log (OFF 5/5). The numbers were not reproducible.
>
> The clean re-measurement below replaces them.

### 1-1. Clean protocol (v3, 2026-05-22)

Via `scripts/ab_automation.py` (nested `claude --print`, 5 tasks × OFF/ON):
- **Location `_ab_live/`** (NOT scratch) → the hook's ruff layer actually fires.
- **Functional prompts only** — each task states a behavioral goal, never names a
  defect and never pins exact code, so the model writes freely and can incorporate
  hook feedback.
- Surviving violations measured with the **full hook select**
  (PERF,SIM,FURB,ANN,F,RUF013 + Phase 3 AST) — the same bar the hook enforces.

### 1-2. Result

| Round | Files clean | Surviving violations | Avg edits/task |
|---|---|---|---|
| OFF (hook disabled) | **0/5** | **11** | 0.0 |
| ON (hook enabled) | **5/5** | **0** | 1.0 |

Per task (OFF→ON surviving): perf401 2→0, sim103 2→0, sim300 2→0, ann001 3→0,
intermediate 2→0.

### 1-3. Honest reading (what the effect actually is)

- Under functional prompts the model wrote **functionally-clean code** (no PERF401,
  no Yoda condition, no intermediate-list-chain) — so AF's PERF/SIM/data-movement
  **differentiators did not trigger**; a capable model avoids those patterns on its
  own.
- **Every** OFF function nonetheless shipped **missing type annotations** (ANN001/
  ANN201) — which the model does not add unprompted. The hook (ON) caught these and
  the model self-corrected in 1 edit each → 0 violations.
- So the measured in-vivo effect on this corpus is **0/5 → 5/5 clean (11→0),
  driven almost entirely by the ANN (type-annotation) axis**. Exclude ANN and OFF
  and ON would both be ~clean here. The effect is real but narrow on simple lint;
  AF's larger latent value is on defect classes a model does NOT self-avoid
  (algebraic-law / data-movement), which simply did not occur in these tasks.

> **Read it as a guarantee, not a delta.** A guardrail's value is the *invariant*
> it enforces, not a percentage. With the hook ON (and the model free to revise),
> **no function ships with an AF-detectable structural violation** — "the hook does
> not fire" *certifies* the function clean on AF's axes (lint + data-movement +
> name-recognized algebraic laws). ON 5/5 clean is that invariant holding. A capable
> model that already writes clean code just means **low-friction confirmation +
> catching the occasional miss** (here, type annotations) — exactly the desired
> guardrail behaviour. The guarantee is over AF's *detectable* axes (not intent/
> logic) and is conditional on the model being free to revise (the hook is advisory
> — §1-4).

### 1-4. A second honest finding — the hook is advisory, not forcing

An intermediate run (prompts that pinned "write exactly this code") showed
ON = OFF = 7 surviving: the model **kept the verbatim code despite the hook**,
treating the explicit user instruction as overriding the hook's `exit 2` feedback.
So the hook is **advisory feedback weighed against user intent**, not a hard gate.
It improves outcomes when the instruction leaves room (functional prompts, §1-2),
not when the user pins conflicting exact code.

### 1-5. Phase 1 withdrawal-criterion check

pass@1 (zero-violation rate): OFF **0%** → ON **100%** on this corpus → clears the
+5% criterion. Caveats: small n (5 tasks), single run, AF's own task set,
**ANN-dominated** — not a general guarantee.

---

## 2. Phase 0 H1-H4 hypothesis verification

Details: [docs/algebraic_filter_phase0_pre_reg.md](algebraic_filter_phase0_pre_reg.md) §10 (Japanese)

| Hypothesis | Target | Measured | Judgment |
|---|---|---|---|
| H1 existing-tool coverage ≥70% | 78.6% | Mini-prototype: 5 ruff + 2 hypothesis/tracemalloc, 5.5/7 detect | **✓ PASS** |
| H2 differentiation-axis independence | VeCoGen etc. don't cover Python skill layer | VeCoGen is C-targeted; AF in independent Python + Claude Code skill+hook niche | **✓ PASS** |
| H3 baseline measurement ≥10 violations | LayerForge has 59 | ruff PERF+SIM+FURB 12 + ANN+F 47 = 59 | **✓ PASS** (sense gap noted) |
| H4 AET-OS alignment | Structural correspondence + no conflict | Verified Orchestrator Pattern Layer 3 mapping landed | **✓ PASS (full promotion)** |

S0-1〜S0-5 all met → Phase 1 launch authorized (chai sovereign judgment 2026-05-19)

---

## 3. Phase 2 law auto-generation coverage

Details: [samples/violations/tests/test_af_phase2_coverage.py](../samples/violations/tests/test_af_phase2_coverage.py)

### 3-1. Single-function API (`auto_test()`)

| Sample | Expected law | Detected |
|---|---|---|
| monoid_associativity_violation | monoid_identity | ✓ FAIL |
| monoid_identity_violation | monoid_identity | ✓ FAIL |
| functor_id_violation | functor_identity | ✓ FAIL |
| fmap_compose_violation | functor_compose | ✓ FAIL |
| fmap_const_violation | functor_identity | ✓ FAIL |
| weighted_average_commutativity | commutativity | ✓ FAIL |
| commutativity_violation_in_named_commutative | commutativity | ✓ FAIL (after type-strategy inference) |
| intersect_commutativity_violation | commutativity | ✓ FAIL (after type-strategy inference) |

**8/8 = 100% detection**

### 3-2. Monad pair API (`auto_test_monad_pair()`)

| Sample | Expected law | Detected |
|---|---|---|
| monad_left_identity_violation | monad_left_identity | ✓ FAIL |
| monad_right_identity_violation | monad_right_identity | ✓ FAIL |
| monad_associativity_violation | monad_associativity | ✓ FAIL |

**3/3 = 100% detection**

### 3-3. Class-based API (`auto_test_class_idempotence()`)

| Sample | Expected detection | strict result | flexible result |
|---|---|---|---|
| idempotence_violation_in_named_set_add | FakeSet.add idempotence | FAIL ✓ | FAIL ✓ |
| idempotence_of_set_remove | FakeSet.remove idempotence | ERROR (ValueError on empty instance) | violation evidence ✓ |
| idempotence_of_dict_update | Counter.update idempotence | FAIL ✓ | FAIL ✓ |

**strict 2/3 + flexible 3/3 = 100% detection**

### 3-4. Total hypothesis-target subset coverage

Total: **single 8 + monad 3 + class 3 = 14/14 = 100%**

Wide measurement on the entire 46-sample manifest:
- Detected (FAIL): 10/46 = 21.7%
- Inferred-but-passed (law applies but no violation): 1/46
- No-law-inferred (function-name keyword no match): 30/46 (responsibility of separate layers: ruff / tracemalloc / DEFERRED)
- Errored (argument count mismatch etc.): 5/46

→ 100% detection in hypothesis-target subset; 21.7% in wide measurement (AF Phase 2 niche is specialized for keyword-driven algebraic laws)

### 3-5. Proof depth: deterministic (CrossHair) vs sampled (hypothesis)

Detection above is mostly **hypothesis sampling** (probabilistic confidence). The
**deterministically-proven** core is narrower: **7 of 14 law templates** have a
CrossHair SMT-proof path on binary functions — associativity, semigroup-assoc,
commutativity, additive identity, binary idempotence, eq-reflexivity, eq-symmetry
(thickened 3→5→7 on 2026-05-22/24). The other 7 (functor / monad / foldable)
remain sampling-only. Guarded by `test_af_phase2_proof_coverage.py`. This is the
honest "deep proven core" number — see [limitations.md](limitations.md) "deterministic
island".

---

## 4. Phase 3 static + runtime coverage

Details: [samples/violations/tests/test_af_phase3_data_movement.py](../samples/violations/tests/test_af_phase3_data_movement.py)

### 4-1. Static AST checker (4 rules)

| Sample | Detected rule | Result |
|---|---|---|
| intermediate_list_chain.py | intermediate-list-chain | ✓ |
| multi_step_intermediate_chain.py | intermediate-list-chain | ✓ |
| dict_keys_list_for_iter.py | dict-keys-list | ✓ |
| unnecessary_copy_chain.py | explicit-copy | ✓ |
| string_concat_in_loop.py | string-concat-in-loop | ✓ |
| fixed/intermediate_list_chain.py | 0 (ground-truth check) | ✓ |

**5/5 = 100% detection** (data-movement target subset)

### 4-2. tracemalloc runtime

unnecessary_copy_chain.process() with 760 bytes allocation > 100 bytes threshold → `excessive-data-movement` violation detected ✓
fixed/intermediate_list_chain.transform() with allocation < threshold → PASS ✓

### 4-3. 46-sample wide coverage (AST checker)

- Detected (≥1 rule fires): 5/46 = 10.9%
- 100% detection in data-movement target subset (5/5)
- Remaining 41 samples are in independent contribution niches of other layers (algebraic laws / type annotations / ruff standard)

### 4-4. Scalpel Docker bridge

[af_phase3/scalpel_bridge.py](../af_phase3/scalpel_bridge.py) — Workaround for typed-ast Python 3.13 incompatibility, via Python 3.10 container with `docker run --rm -v`:
- intermediate_list_chain.py → transform function CFG ✓
- multi_step_intermediate_chain.py → transform_3_steps CFG ✓
- monoid_associativity_violation.py → my_sum CFG ✓ (works for Phase 2 samples too)

---

## 5. Phase 4 structured payload + anti-pattern

Details: [samples/violations/tests/test_af_phase4_feedback.py](../samples/violations/tests/test_af_phase4_feedback.py)

### 5-1. Unified schema (5 fields)

Phase 1 ruff output + Phase 3 StaticViolation are unified into `{layer, violation_location, violation_law, alternative_skeleton, fix_example}`:

```json
{
  "layer": "Phase 1 ruff",
  "violation_location": "samples/violations/perf401_manual_list_comp.py:15",
  "violation_law": "PERF401",
  "alternative_skeleton": "list comprehension",
  "fix_example": "[x * 2 for x in data if x > 0]"
}
```

### 5-2. Anti-pattern tracker + pre-emptive hint

JSON history persistence (`hooks/af_violation_history.json`):
- `record_violations(rule_ids, file_path)` to add history
- `get_preemptive_hints(rule_ids, threshold=3)` to issue warning hints when cumulative count for a rule reaches 3

Example hint:
```
WARNING: rule `PERF401` has been triggered 3 times across sessions.
Pre-emptive hint: review the alternative skeleton before re-writing.
```

### 5-3. Hook integration

[hooks/posttool_af_check.py](../hooks/posttool_af_check.py) integrates Phase 1 + Phase 3 + Phase 4 into three layers:
- Phase 4 structured section (parseable by Claude, with skeleton + fix_example)
- Phase 1 raw ruff output (detailed context)
- Phase 3 raw AST violation list
- Action section (fix steps articulated)
- Pre-emptive hint section (via history)

---

## 6. End-to-end evidence (real Claude session)

### 6-1. Automated A/B via nested `claude --print` (scripts/ab_automation.py)

Clean re-measurement 2026-05-22 (v3): 5 tasks × OFF/ON = 10 nested sessions, in
`_ab_live/`, functional prompts, full-select measurement → §1-2 (OFF 0/5 → ON
5/5; 11→0 surviving). The hook fired and the model self-corrected (1 edit/task)
in the ON round.

> Prior scratch-based runs (5×2 and 12×2) are **retracted**: they wrote to
> `scratch/` (ruff per-file-ignores ALL → ruff layer dead) with answer-leak
> prompts. Their JSON logs (`log_auto_*.json`) are kept locally as a record but
> are not valid effectiveness evidence.

### 6-2. Verified hook-fire behaviour (location matters — measured 2026-05-22)

| Write target | ruff layer (PERF/SIM/FURB/ANN) | Phase 3 AST |
|---|---|---|
| `scratch/*.py` | **does NOT fire** (`per-file-ignores = ["ALL"]`) | fires |
| `_ab_live/` or repo root (not ignored) | **fires** (exit 2 + feedback) | fires |

Verified directly: a PERF401 file in `scratch/` is not blocked; the identical
file in `_ab_live/` / root is blocked with `exit 2`. An intermediate-list-chain
file is blocked anywhere (Phase 3 ignores ruff config). In the v3 ON round the
model received the hook feedback and self-corrected (e.g. `add(x, y)` →
`add(x: int, y: int) -> int`).

> Correction: an earlier note claimed the hook fired on `scratch/test_target.py`;
> that contradicts the verified `per-file-ignores` behaviour and is removed.

---

## 7. Competitor comparison (claude-code-quality-hook) — measured 2026-05-20

Head-to-head comparison on the 46-sample violation corpus. The competitor's
**actual** Python stack (read from its source `quality-hook.py`) is
**`ruff check` with NO `--select` (= ruff defaults E/F) + pyright**, NOT the
AF rule selection. AF stack = **ruff(PERF/SIM/FURB/ANN/F/RUF013) + Phase 3 AST
+ Phase 2 runtime PBT**.

> ⚠️ **Corpus bias disclosure (read first)**: these 46 samples were *designed
> by AF* to showcase AF's target defects (algebraic laws / perf / data-movement).
> This is **AF's home field, not a neutral benchmark**. On a corpus dominated by
> type errors, the competitor's pyright would lead. The numbers below show
> *which tool targets which defect class*, NOT a general superiority ranking.

### 7-1. Detection — corrected with competitor's actual config

| Stack | Detected | Coverage |
|---|---|---|
| competitor ruff (defaults E/F) | **0**/46 | 0% |
| competitor pyright | 7/46 | 15% |
| **competitor full (ruff default + pyright)** | **7**/46 | **15%** |
| AF ruff (PERF/SIM/FURB/ANN/F/RUF013) | 12/46 | 26% |
| **AF full (ruff + Phase 3 + Phase 2 runtime)** | **28**/46 | **61%** |

**Correction note**: an earlier draft of this section wrongly gave the
competitor *AF's* ruff selection (yielding 18/46). That was an over-credit.
The competitor's ruff runs with defaults and catches **0** of this corpus's
perf/algebraic samples — its entire 7 comes from pyright type checking.

- **AF-only catches (25)**: algebraic-law (monoid / commutativity / functor /
  foldable) + perf/data-movement (intermediate-list-chain / string-concat /
  unnecessary-copy) + AF's ruff selection (PERF/SIM/FURB/ANN) — none of which
  the competitor's default ruff targets.
- **competitor-only catches (4)**: `missing_optional_handling`,
  `fmap_unit_violation`, `monad_associativity_violation`,
  `monad_right_identity_violation` — pyright catches these as **type errors**
  (a different defect class than AF's algebraic-law check).

### 7-2. Fix-outcome model — competitor's AI-repair NOT measured

The competitor's headline "3-stage AI auto-fix" pipeline **did not activate**
in a protected environment:

- Standalone invocation logged `Claude Code not available` → the competitor
  hard-codes `subprocess.run(['claude', ...])`, which Windows `CreateProcess`
  cannot resolve (`.cmd` not auto-appended) → AI stage skipped.
- Its AI stage spawns `claude -p ... --dangerously-skip-permissions` nested
  autonomous agents. Running that is a distinct risk class (permission-bypassed
  agent spawning) requiring explicit sovereign approval; **not executed**.
- **When its AI stage is unavailable, the competitor returns `exit 2 + feedback`
  and delegates the fix to the calling Claude — the SAME outcome model as AF.**

So fix-success quality of the competitor's AI pipeline is **unmeasured**
(honest limitation). AF's own fix-success is measured separately (§1: clean
re-measurement OFF 0/5 → ON 5/5, ANN-dominated; the earlier 20→100%/91.7→100%
figures are retracted — see §1 correction note).

### 7-3. Actioned gap closure

- **`ruf013_implicit_optional`** → closed by adding `RUF013` to AF's ruff
  select (verified: catches the sample, zero false-positive on the `fixed/`
  ground-truth corpus; `RUF` wholesale rejected because `RUF002` flags
  ambiguous Unicode `×` in docstrings).
- **`missing_optional_handling`** → genuine AF gap; requires pyright-style
  dataflow analysis that ruff cannot perform. Not closed (honest limitation).
- **monad / fmap_unit laws** → AF Phase 2 coverage gap: `auto_test()`
  single-function API skips monad-pair laws (needs `auto_test_monad_pair`,
  not wired into the runner). Known Phase 2 limitation.

### 7-4. Honest positioning conclusion

- AF and the competitor **target different defect classes**: AF =
  algebraic-law / perf / data-movement; competitor = type errors (pyright).
  On AF's home-field corpus AF leads 28 vs 7, but this overstates general
  superiority (corpus bias above).
- The competitor's default ruff is **weaker on lint** than AF's selection
  (catches 0 here) but its **pyright is a real type-checking edge** AF lacks
  (4 type-error catches AF misses; `missing_optional_handling` is a true gap).
- AF's **defensible value is Layer 2/3** (algebraic-law + data-movement),
  where no competitor counterpart exists — verified against *hook-off baseline*,
  not against alternative law-checking approaches.
- The competitor is **not Windows-ready** (claude `.cmd` resolution + cp932
  encoding crashes), whereas AF handles both.
- The applicability matrix in [README.md](../README.md) correctly routes
  Layer-1-type-checking users to the competitor.

---

## 8. "+α plugin on any base" — live composition verification (2026-05-21)

The additive-layer model (AF as a Claude Code plugin sitting on top of any
base tooling) is verified at two levels:

### 8-1. Deterministic composition (5 tests, [test_plugin_packaging.py](../samples/violations/tests/test_plugin_packaging.py))
- plugin.json / hooks.json valid + PostToolUse + `${CLAUDE_PLUGIN_ROOT}`
- hook command resolves and exits 0 on clean file
- history path writable under a simulated read-only install
- **additive composition**: a mock "base" type-checker hook + the AF hook
  both fire on ONE file (type error + monoid violation), each catching its
  own defect class with zero cross-contamination.

### 8-2. Live plugin load (real `claude --plugin-dir` session)
Ran `claude --plugin-dir <AF> --print` and asked it to write a violating
function. Evidence ([_plugin_verification/live_plugin_load_hook_fire_2026-05-21.json](_plugin_verification/live_plugin_load_hook_fire_2026-05-21.json)):
- The session **loaded AF as a plugin** and the PostToolUse hook **fired on
  the live Write** — the model itself reported: *"a PostToolUse plugin hook
  (algebraic-filter, ruff-based) flagged the write with three findings"*.
- The anti-pattern history recorded 3 real violations (PERF401 / ANN001 /
  ANN201) at the written file path = physical proof the hook executed.
- **Design philosophy confirmed live**: the model *declined* to "fix" PERF401
  because it conflicted with the user's explicit instruction — i.e. the hook
  gives feedback but the LLM keeps autonomy (hook over constrained decoding).

> Scope: single manual smoke run, one model, on Windows. Proves the
> plugin-load + hook-fire + additive-feedback path works end-to-end; it is
> not a statistical claim.

---

## See also

- [docs/architecture.md](architecture.md) — Detailed architecture
- [docs/algebraic_filter_phase0_pre_reg.md](algebraic_filter_phase0_pre_reg.md) — Phase 0 hypotheses + withdrawal criteria (Japanese)
- [docs/algebraic_filter_project_plan.md](algebraic_filter_project_plan.md) — Phase roadmap (Japanese)
- [docs/_ab_measurement/](_ab_measurement/) — A/B protocol + log template + results
- [samples/violations/manifest.json](../samples/violations/manifest.json) — Specification layer (46-sample metadata)
