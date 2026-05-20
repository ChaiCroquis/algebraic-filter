# Architecture — algebraic-filter detailed

[日本語版 architecture](architecture.ja.md)

AF design articulated across four axes:

1. [Two-layer structure: philosophy filter + algebraic-filter](#1-two-layer-structure-philosophy-filter--algebraic-filter)
2. [3-layer verification pipeline](#2-3-layer-verification-pipeline)
3. [As AET-OS Verified Orchestrator Pattern Layer 3](#3-as-aet-os-verified-orchestrator-pattern-layer-3)
4. [Phase 0 – Phase 5 composition mapping](#4-phase-0--phase-5-composition-mapping)

---

## 1. Two-layer structure: philosophy filter + algebraic-filter

```
┌──────────────────────────────────────────────┐
│ philosophy filter (policy layer, 2026-05-05) │
│   judgment: "machine-verifiable → AI run /   │
│              not verifiable → reject"        │
└──────────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────┐
│ algebraic-filter (physical layer, this repo) │
│   PostToolUse hook blocks violating code     │
│   with exit 2 + feedback                     │
│   → Claude triggers self-correction cycle    │
└──────────────────────────────────────────────┘
```

### Responsibility split

| Layer | Responsibility | Implementation |
|---|---|---|
| philosophy filter | Judges whether a task is machine-verifiable (delegation decision) | Policy layer, chai's operating principles |
| algebraic-filter | At runtime, detects violations + injects feedback into machine-verifiable tasks | Phase 0-5, this repository |

### Complementarity

- For tasks the philosophy filter deems "AI runnable", AF **blocks violating writes + triggers self-correction at write-time**
- philosophy filter handles conceptual judgment; AF handles physical enforcement = together they complete the AI-delegation guardrail

---

## 2. 3-layer verification pipeline

```
Claude Code writes / edits
        ↓
PostToolUse hook fires (hooks/posttool_af_check.py)
        ↓
┌─────────────────────────────────────┐
│ Layer 1: static (tens of ms)        │
│   ruff PERF/SIM/FURB/ANN/F + AF AST │
│   - purity / intermediate data /    │
│     type annotations                │
└─────────────────────────────────────┘
        ↓ (on violation)
┌─────────────────────────────────────┐
│ Layer 2: algebraic-law PBT (s)      │
│   hypothesis (auto-generated)       │
│   - Monoid / Functor / Monad laws   │
│   - associativity / identity /      │
│     idempotence / commutativity     │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ Layer 3: runtime (tens of s)        │
│   tracemalloc / memray (Linux/macOS)│
│   - memory access counts            │
│   - intermediate-object counts      │
└─────────────────────────────────────┘
        ↓
Phase 4: LLM-optimized feedback formatter
  {layer, location, law, skeleton, fix_example}
        ↓
exit code 2 + JSON additionalContext
        ↓
Claude self-correction cycle
```

### Detection scope per layer

| Layer | Detection target | Implementation | Coverage |
|---|---|---|---|
| 1 Static (ruff) | PERF / SIM / FURB / ANN / F / B / UP / RUF / C | ruff CLI | ~966 rules (Python lint standard) |
| 1 Static (AF AST) | intermediate-list-chain / dict-keys-list / explicit-copy / string-concat-in-loop | `af_phase3/static_checker.py` | 4 rules (AF original contribution) |
| 2 Algebraic-law PBT | Monoid (2) / Functor (2) / Monad (3) / Semigroup (1) / Foldable (1) / Eq (2) / Commutativity / Idempotence (2) | `af_phase2/law_templates.py` | 13 laws |
| 3 Data movement | allocation bytes / intermediate-list count / threshold check | `af_phase3/runtime_checker.py` | tracemalloc (Windows + Unix) |

### Energy-efficiency rationale

Cheap layers reject first:
- Layer 1 (tens of ms): ruff + AST = filters most violations
- Layer 2 (seconds): hypothesis = function-specific algebraic-law violations
- Layer 3 (tens of seconds): tracemalloc = data-movement violations

Later stages cost more → catching at earlier stages saves later compute.

---

## 3. As AET-OS Verified Orchestrator Pattern Layer 3

The three-layer structure articulated in [docs/AIエージェントアーキテクチャ調査報告.pdf](AIエージェントアーキテクチャ調査報告.pdf) §5.1, with AF's position:

| AET-OS layer | Role | AF mapping |
|---|---|---|
| 1 Strategic | Meta-Architect (task decomposition / resource allocation) | Out of AF scope (Claude Code + chai's policy judgment) |
| 2 Execution | Worker / Specialist (code generation) | Out of AF scope (Claude Code handles) |
| **3 Verification** | **Verifier / Auditor (formal-spec generation + solver + safety check), holds Veto Power** | **AF directly implements = Python skill+hook layer for the verification layer** |

### Concrete implementation of veto power

AF hook's `exit code 2` = the physical implementation of AET-OS verification layer's **veto power**:
- On detection, hook returns exit 2 + `decision: "block"` + structured feedback
- Claude (execution layer) accepts the block and enters a correction cycle (verification layer is independent of + holds strong authority over execution layer)

### Alignment with SETS independent-verifier philosophy

AET-OS PDF §3.2 verbatim:
> The verification phase should be assigned an independent process with a different perspective from generation (e.g. a different prompt strategy, or an external tool like the formal methods described below). This design pattern is effective.

AF's correspondence:
- Hook runs as a subprocess (process independent of Claude session)
- Verification tools are ruff / hypothesis / tracemalloc (LLM-independent deterministic tools)
- Structured feedback exercises veto power over Claude (independent-perspective fix demand)

### Relationship with CrossHair / QWED

CrossHair + QWED, recommended in AET-OS PDF §4.2, are the Python formal-verification standard. AF integrates them as:
- CrossHair = `af_phase3/scalpel_bridge.py` (Phase 3 extension via Docker container)
- QWED "LLM is an untrusted translator" philosophy = AF's overall design (verify LLM generation with deterministic tools)

---

## 4. Phase 0 – Phase 5 composition mapping

| Phase | Role | Key files | Status |
|---|---|---|---|
| 0 Pre-reg | Hypotheses H1-H4 + withdrawal criteria + baseline | [docs/algebraic_filter_phase0_pre_reg.md](algebraic_filter_phase0_pre_reg.md) | ✓ closed (2026-05-19) |
| 1 PostToolUse hook | Hook script + 46 violation samples + manifest-driven TDD | [hooks/posttool_af_check.py](../hooks/posttool_af_check.py) + [samples/violations/](../samples/violations/) | ✓ end-to-end verified |
| 2 Algebraic-law PBT auto-gen | inferrer + law_templates + generator | [af_phase2/](../af_phase2/) | ✓ 13 laws + 100% subset coverage |
| 3 Data movement | static_checker + runtime_checker + Scalpel Docker | [af_phase3/](../af_phase3/) + [af_phase3_scalpel/](../af_phase3_scalpel/) | ✓ extended |
| 4 LLM-optimized feedback | feedback_formatter (Phase 1+2+3 unified schema) + anti_pattern_tracker (per-rule threshold) | [af_phase4/](../af_phase4/) | ✓ integrated + A/B verified |
| 5 OSS release | README + LICENSE + pyproject + GitHub push | This repository | ✓ initial push |

### Phase 0 binding contract achievement

- H1 existing-tool coverage ≥70% → mini-prototype 78.6% PASS
- H2 differentiation-axis independence → VeCoGen is C-targeted; AF in independent Python skill-layer niche → PASS
- H3 baseline measurement ≥10 violations → 59 in LayerForge → PASS (sense gap noted)
- H4 AET-OS alignment → Verified Orchestrator Pattern Layer 3 mapping landed (full PASS promotion)
- S0-1〜S0-5 all met → Phase 1 launch authorized

### Phase 1 withdrawal criterion 1 cleared

A/B measurement evidence (see [docs/evidence_summary.md](evidence_summary.md)):
- 5-task version (raw-code niche): pass@1 +80%
- 12-sample wide version (curated niche): pass@1 +8.3%
- Both niches clear withdrawal criterion (+5%) **on this corpus** (small n, single run, AF's own samples — not a general guarantee)

---

## See also

- [docs/algebraic_filter_project_plan.md](algebraic_filter_project_plan.md) — Phase roadmap details (Japanese)
- [docs/algebraic_filter_related_work.md](algebraic_filter_related_work.md) — Related-work comparison (Japanese)
- [docs/_index/aet_os_reference.md](_index/aet_os_reference.md) — AET-OS PDF index + mapping (Japanese)
- [docs/tool_landscape.md](tool_landscape.md) — Tool-selection rationale (Japanese)
