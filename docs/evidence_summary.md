# Evidence Summary — algebraic-filter verification results

[日本語版 evidence_summary](evidence_summary.ja.md)

Evidence collected across each Phase + A/B measurement, with Phase 1 withdrawal-criterion check.

---

## 1. A/B measurement results (the actual AF-effect evidence)

### 1-1. Measurement protocol (details: [docs/_ab_measurement/protocol.md](_ab_measurement/protocol.md))

- Round 1 (hook OFF): Rename `.claude/settings.local.json` to disable AF hook
- Round 2 (hook ON): Re-enable hook
- In each round: write violating code + ask Claude to fix
- Count Claude's Edit invocations + final ruff violations (full-layer)

### 1-2. 5-task version (AI-generated raw-code niche)

Bare violating code (no type annotations) written to `scratch/_ab_*.py` and asked to fix.

| Task | OFF Edits | OFF remaining (full-layer) | ON Edits | ON remaining (full-layer) |
|---|---|---|---|---|
| perf401 | 1 | 2 remaining | 2 | 0 |
| sim103 | 1 | 2 remaining | 2 | 0 |
| sim300 | 1 | 2 remaining | 2 | 0 |
| ann001 | 1 | 0 | 1 | 0 |
| intermediate | 1 | 2 remaining | 2 | 0 |

Summary:
- Full-layer success rate: OFF **1/5 = 20%** vs ON **5/5 = 100%** → **+80%**
- Average Edit count: OFF 1.0 vs ON 1.8 → +80% (trade-off, invested in completion-depth)

### 1-3. 12-sample wide version (curated-code niche)

Manifest-driven, 12 ruff-target PASS samples (with type annotations).

| Metric | OFF | ON | delta |
|---|---|---|---|
| Full-layer success rate | 11/12 = 91.7% | 12/12 = 100% | **+8.3%** |
| Average Edit count | 1.0 | 1.08 | +8% (only 1 sample needed +1) |

The single failure (b007_unused_loop_variable hook OFF) is the same pattern as the 5-task version: original code lacked type annotations, so chain violations remained.

### 1-4. Phase 1 withdrawal-criterion check

| Criterion | 5-task | wide | Judgment |
|---|---|---|---|
| pass@1 +5% improvement | +80% | +8.3% | **Cleared in both niches** |
| Edit cycles -10% improvement | +80% increase | +8% increase | Not met (trade-off invested in completion-depth) |
| Both unmet → withdrawal (AND) | pass@1 cleared | pass@1 cleared | **Withdrawal criterion not met = AF effectiveness substantiated** |

### 1-5. Niche-difference articulation

| Niche | AI-generated raw code | Curated code |
|---|---|---|
| Assumed environment | Type-bare function definitions Claude newly generates | Existing samples with single-layer violations only |
| Hook OFF behavior | Fixes only the original violation; ANN001/ANN201 chain violations remain (Claude treats as out-of-scope) | Fixes the original violation; chain violations are few from the start (already high quality) |
| Hook ON behavior | Multi-layer chain detection → fixes all violations in 2 cycles | Single-layer fix in 1 cycle; few additional violations |
| AF effect | **+80% pass@1** (large impact) | **+8.3% pass@1** (cleanup auxiliary) |

→ AF shows **true value in AI-generated raw code**; even in curated code, +8.3% clears the withdrawal criterion.

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

### 6-1. Automated A/B via nested `claude --print` (scripts/ab_automation*.py)

- 5 tasks × 2 rounds = 10 nested sessions
- 12 samples × 2 rounds = 24 nested sessions
- All sessions confirm hook fire + structured feedback injection + Claude self-correction cycle

### 6-2. Manual chai-session end-to-end

[2026-05-20 chai try] Append-loop violation written to `scratch/test_target.py` → hook fired → PERF401 detected → Claude rewrote as list comprehension → hook fired again → ANN001/ANN201 detected → Claude added type annotations → hook PASS.

**Multi-step feedback chain (PERF401 → ANN201 → ANN001 → PASS) verified in a real Claude Code session.**

---

## 7. Competitor comparison (claude-code-quality-hook) — measured 2026-05-20

Head-to-head **detection** comparison on the 46-sample violation corpus.
Competitor stack approximated as **ruff + pyright** (its primary Python layer);
AF stack as **ruff(PERF/SIM/FURB/ANN/F) + Phase 3 AST + Phase 2 runtime PBT**.
This measures *detection coverage only* — it does **not** measure fix-success
rate or the competitor's 3-stage AI-repair pipeline (that requires a Claude
API session = out of this deterministic comparison's scope).

### 7-1. Static layer only (no AF Phase 2 runtime)

| Stack | Detected | Coverage |
|---|---|---|
| AF static (ruff + Phase 3 AST) | 16/46 | 35% |
| competitor (ruff + pyright) | 18/46 | 39% |

**On the pure static layer, the competitor detects more** (pyright catches
type-level defects AF's ruff selection misses). This confirms: for Layer-1
type checking, claude-code-quality-hook is the stronger choice.

### 7-2. Full AF stack (incl. Phase 2 runtime PBT, opt-in)

| Stack | Detected | Coverage |
|---|---|---|
| AF full (ruff + Phase 3 + Phase 2 runtime) | 27/46 | 59% |
| competitor (ruff + pyright) | 18/46 | 39% |

- **AF-only catches (14)**: algebraic-law violations (monoid / commutativity /
  functor / foldable) + data-movement (intermediate-list-chain / string-concat /
  unnecessary-copy) — the competitor has no counterpart layer.
- **competitor-only catches (5)**: `missing_optional_handling`,
  `ruf013_implicit_optional`, `monad_associativity_violation`,
  `monad_right_identity_violation`, `fmap_unit_violation` — pyright catches
  these as **type errors** (a different defect class than AF's law check).

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

- AF's **Layer 1 (lint/type) is not superior** to the competitor; with the
  RUF013 fix it closes one gap but `missing_optional_handling` remains.
- AF's **defensible value is Layer 2/3** (algebraic-law + data-movement),
  where no competitor counterpart exists — but this is verified against
  *hook-off baseline*, not against alternative law-checking approaches.
- The applicability matrix in [README.md](../README.md) correctly routes
  Layer-1-only users to the competitor.

---

## See also

- [docs/architecture.md](architecture.md) — Detailed architecture
- [docs/algebraic_filter_phase0_pre_reg.md](algebraic_filter_phase0_pre_reg.md) — Phase 0 hypotheses + withdrawal criteria (Japanese)
- [docs/algebraic_filter_project_plan.md](algebraic_filter_project_plan.md) — Phase roadmap (Japanese)
- [docs/_ab_measurement/](_ab_measurement/) — A/B protocol + log template + results
- [samples/violations/manifest.json](../samples/violations/manifest.json) — Specification layer (46-sample metadata)
