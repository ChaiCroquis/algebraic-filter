# Philosophy Filter Integration — Combining AF with the policy layer

Design articulation for running AF (algebraic-filter) together with a **philosophy filter (policy layer)** as a two-layer AI-delegation guardrail.

[日本語版](philosophy_filter_integration.md)

---

## Two-layer structure overview

```
┌──────────────────────────────────────────────┐
│ Policy layer (Philosophy Filter)             │
│   Pre-judgment before delegating tasks to AI:│
│   4-step decision tree                       │
│     (machine-verifiable / reproducible /     │
│      business domain / cognitive-load        │
│      reduction)                              │
└──────────────────────────────────────────────┘
                  ↓ tasks judged "AI-runnable"
┌──────────────────────────────────────────────┐
│ Physical layer (Algebraic Filter, this OSS)  │
│   PostToolUse hook auto-validates at write:  │
│   - Phase 1 ruff (PERF/SIM/FURB/ANN/F)       │
│   - Phase 2 algebraic-law PBT (hypothesis)   │
│   - Phase 3 data movement (tracemalloc)      │
│   - Phase 4 structured feedback              │
│   on violation → exit 2 + self-correction    │
└──────────────────────────────────────────────┘
```

The policy layer decides "**Is this task safe to hand to AI?**" and the physical layer (AF) verifies "**Is the code AI produced correct?**" — complementary design.

---

## philosophy filter 4-step decision tree (policy layer, generalized)

Evaluate in 4 steps before delegating to AI:

| # | Judgment | AI delegate | Examples |
|---|---|---|---|
| 1 | **Machine-verifiable** | ✓ AI runs | code violation detection / unit tests / lint check (= AF's core domain) |
| 2 | **100% reproducible procedure** | ✓ AI runs | file formatting / refactoring / docs generation |
| 3 | **Business domain** | ✗ user-only | release decisions / contract interpretation / received-asset meaning / timing decisions |
| 4 | **Reduces cognitive load** | ✓ AI by default; if not, **drop the task entirely** | repetitive work → AI automates / one-off low-value work → discard |

**Top principle**: "I want it easy" = cognitive-load reduction. The act of throwing a judgment back at the user itself raises cognitive load and violates the philosophy. Verbal replay of already-verified tasks is unnecessary; default to autonomous AI progression.

---

## Running AF as the philosophy filter's physical-layer implementation

| Flow | Policy layer | Physical layer (AF) |
|---|---|---|
| 1. Task received | Evaluate via 4-step decision tree | (idle) |
| 2. AI-run judgment | "AI-runnable" → hand off to AF | (idle) |
| 3. AI writes | (idle) | Claude generates code via `Write` / `Edit` |
| 4. Write-time verification | (idle) | PostToolUse hook fires → ruff + AST + algebraic-law + data movement |
| 5. Violation detected | (idle) | exit 2 + structured feedback → Claude self-correction cycle |
| 6. Correction complete | Completion report (with L1-L4 mechanical verification) | (idle) |
| 7. Business judgment | Final "business domain" call is user's | (idle) |

→ Policy layer + physical layer = **completed AI-delegation guardrail**.

---

## AF standalone vs two-layer operation

| Use case | AF standalone | Two-layer |
|---|---|---|
| Violation detection (at write-time) | ✓ | ✓ |
| Claude self-correction cycle | ✓ | ✓ |
| Pre-delegation task judgment | ✗ | ✓ (policy layer filters first) |
| Top-principle (cognitive-load reduction) alignment | (partial) | ✓ (complete) |
| Business-judgment articulation in completion reports | (optional) | ✓ (template included) |

AF standalone still has value (ruff + algebraic-law + data-movement verification), but two-layer operation **completes the AI-delegation guardrail**.

---

## Paths for individual integration

The philosophy filter is designed to run at the **individual OS layer** — the space where each user articulates their own operating principles. Four representative paths for an AF user to set up the policy layer themselves:

### 1. Articulate the 4-step decision tree in CLAUDE.md

Add the decision tree to `~/.claude/CLAUDE.md` (the universal operating doc loaded at Claude Code session start):

```markdown
## Delegation policy

### 4-step decision tree (pre-delegation pre-judgment)

1. Machine-verifiable → AI runs
2. 100% reproducible procedure → AI runs
3. Business domain (release / contract / received assets / timing) → user-only
4. Reduces cognitive load → AI default-runs / if not, drop the task entirely
```

### 2. Make it physical via Claude Code skill / hook

Turn the delegation judgment into a Claude Code skill (e.g. chai's `secretary` skill) and set up a PostToolUse hook that blocks "user-delegation questions" as a physical layer:

```python
# Example: hooks/pretool_delegation_guard.py
# When tool_name == "AskUserQuestion", scan the question text
# If no business-domain keywords match → block
# "Continue autonomously, or re-call with explicit exception articulated"
```

### 3. Permanently land it as a profile doc

Articulate operating principles in a profile doc (e.g. `~/.claude/profile/cognitive_load_principles.md`) so they're loaded at every session start.

### 4. Articulate operational evolution in ADRs

Record changes to the delegation policy in Architecture Decision Records (e.g. `~/.claude/decisions/YYYY-MM-DD_*.md`) as a reviewable audit trail.

---

## chai's individual operation example (publicly-shareable subset)

The AF author chai's operation example (details are personal; only generalized principles articulated):

- 4-step decision tree articulated in `~/.claude/profile/cognitive_load_principles.md` (personal canonical philosophy store)
- Delegation-judgment 3-layer enforcement (prompt layer + physical-layer hook + context layer) integrated
- chai's personal operating principles are out-of-scope for OSS publication (individual OS layer); AF users are free to build the same pattern independently

For details: AF author's operating principles are outside the AF project scope; each user sets up the policy layer as an individual OS layer.

---

## See also

- [README.en.md](../README.en.md) — AF overview + design philosophy
- [docs/architecture.en.md](architecture.en.md) — Two-layer structure + 3-layer verification pipeline
- [docs/_index/aet_os_reference.md](_index/aet_os_reference.md) — AF positioned as AET-OS Verified Orchestrator Pattern Layer 3
- [CONTRIBUTING.en.md](../CONTRIBUTING.en.md) — AF contribution guide (sample addition / law extension)
