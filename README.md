# algebraic-filter

**Algebraic-law-level machine verification guardrail for AI-generated code** — A Claude Code skill + PostToolUse hook that auto-validates Python code at write-time and triggers Claude's self-correction cycle on violations.

[日本語版 README](README.ja.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ChaiCroquis/algebraic-filter/actions/workflows/ci.yml/badge.svg)](https://github.com/ChaiCroquis/algebraic-filter/actions/workflows/ci.yml)

## Overview

AI-generated code can contain algebraic structural defects (purity violations, broken associativity, excessive data movement, etc.) that are invisible to `pass@1` evaluation. algebraic-filter (AF) post-validates `Write`/`Edit` via Claude Code's **PostToolUse hook** and, on violation, returns `exit code 2 + structured feedback` to trigger Claude's **self-correction cycle**.

### Design philosophy

- **Hook over constrained decoding**: CRANE (2025) showed that strong decoding constraints degrade LLM reasoning. AF uses post-hoc verification to preserve LLM autonomy while keeping verification deterministic (zero hallucination).
- **Two-layer structure**: philosophy filter (policy layer: "machine-verifiable → AI executes / not verifiable → reject") + algebraic-filter (physical layer: hook blocks violating code + emits feedback). Complementary design.
- **Concrete implementation of AET-OS Verified Orchestrator Pattern Layer 3** as a Python skill+hook layer (verification layer independent of execution layer + holds veto power).

### 3-layer verification pipeline

```
Claude Code writes/edits
        ↓
PostToolUse hook fires
        ↓
Layer 1 static (tens of ms): ruff PERF/SIM/FURB/ANN/F + AF original AST
Layer 2 algebraic-law PBT (seconds): hypothesis @given (auto-generated from signatures)
Layer 3 data movement (tens of seconds): tracemalloc / memray + threshold judgment
        ↓
violation detected → exit code 2 + structured feedback → Claude self-corrects
```

## Action evidence (small-scale, reproduce-it-yourself)

A/B measurement automated via `claude --print` nested sessions, in `_ab_live/`
(where the hook actually fires), with **functional prompts** (no defect named, no
code pinned), measured against the **full hook select** — clean re-measurement
2026-05-22:

| Evaluation niche | hook OFF clean | hook ON clean | delta |
|---|---|---|---|
| Functional-prompt tasks (5) | **0/5** (11 violations) | **5/5** (0) | **0 → 100%** |

**Read it as a guarantee, not a delta.** The point of a guardrail is the invariant:
with the hook ON, "the hook does not fire" *certifies* a function clean on AF's axes
(lint + data-movement + name-recognized algebraic laws). A capable model writing
clean code already just means low-friction confirmation plus catching the occasional
miss — which is exactly what you want.

> **Read this before quoting the number.** Small-n (5), single-run, AF's own task
> set, one model. On this corpus the effect is **driven almost entirely by the ANN
> (type-annotation) axis**: the model wrote functionally-clean code but omitted
> type hints on every function, and the hook enforced them. The PERF/SIM/
> data-movement differentiators did not trigger (a capable model avoids those
> patterns on its own). The hook is **advisory** — if you pin exact code it will
> keep it despite the hook. **Not a general performance guarantee**; reproduce with
> `python scripts/ab_automation.py`.
>
> The earlier "+80% / +8.3%" headline is **retracted** — it was measured in
> `scratch/` where ruff is disabled by `per-file-ignores` and prompts named the
> defect. See `docs/evidence_summary.md` §1 for the full correction.

## Is this the right tool for you? (applicability matrix)

AF occupies a specialized niche in the Claude Code hook ecosystem. Honest scope articulation so you can pick the right tool for your situation:

| Your situation | Recommended tool |
|---|---|
| Want only Layer 1 (ruff PERF/SIM/FURB/ANN/F lint hook), multi-language (Python / JS / TS / Go / Rust) | [claude-code-quality-hook](https://github.com/dhofheinz/claude-code-quality-hook) — Layer 1 specialist with 3-stage auto-fix pipeline |
| Want Layer 1 **+ algebraic-law PBT auto-generation (Layer 2) + data-movement feedback (Layer 3)** integrated for Python | **algebraic-filter** (this repo) |
| Want generic auto-format / test-runner / traceback compaction hooks | [claude-tools](https://github.com/tarekziade/claude-tools), [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery), or the official [hooks guide](https://code.claude.com/docs/en/hooks-guide) |
| Targeting C / Frama-C ACSL specs | [VeCoGen](https://github.com/VeCoGen/VeCoGen) (independent niche, not Python) |

AF's differentiation is **the combination of Layer 2 (13 algebraic laws, auto-generated from function signatures) + Layer 3 (tracemalloc data-movement) + Claude Code hook integration**, which is unique in the public hook ecosystem at the time of this writing. If you only need Layer 1, the alternatives above are simpler and more battle-tested.

## Install

```bash
pip install -e .

# Optional: Phase 3 contract demo
pip install -e ".[phase3]"

# Optional: Phase 4 strict type-check
pip install -e ".[phase4]"

# Dev (pytest)
pip install -e ".[dev]"
```

### Activation — two tracks (both supported)

AF works as an **additive +α layer**: it composes on top of whatever base
quality tooling you already run (ruff / pyright / another hook), each hook
firing independently on the same edit. Choose either track:

#### Track A — Claude Code plugin (recommended, no manual wiring)

AF ships as a Claude Code plugin (`.claude-plugin/plugin.json` + `hooks/hooks.json`)
**and** a self-hosted marketplace (`.claude-plugin/marketplace.json`).

Install from the marketplace (inside a Claude Code session):

```
/plugin marketplace add ChaiCroquis/algebraic-filter
/plugin install algebraic-filter@algebraic-filter-marketplace
```

Or load locally for development:

```bash
claude --plugin-dir /absolute/path/to/algebraic-filter
```

Either way the PostToolUse hook registers automatically via
`${CLAUDE_PLUGIN_ROOT}` and runs **in addition to** your existing hooks /
other plugins (additive composition — verified end-to-end, see
[docs/evidence_summary.md](docs/evidence_summary.md) §8).

> **Install scope — important.** `claude plugin install` defaults to
> `--scope user`, which means the hook fires in **every project** you open
> (it's a fast no-op on non-`.py` files and clean code, but the `ruff`
> subprocess still launches on each `.py` write everywhere). To limit it:
>
> | `--scope` | Fires in | Use when |
> |---|---|---|
> | `user` (default) | **all your projects** | you always want AF on |
> | `project` | one repo, committed (shared with the team) | team-wide on that repo |
> | `local` | one repo, just you (not committed) | your own work on that repo |
>
> Since AF is most useful on Python with algebraic structure, **`--scope local`
> on the target project** is the safe default:
> `claude plugin install algebraic-filter@algebraic-filter-marketplace --scope local`

The plugin registers its PostToolUse hook automatically via
`${CLAUDE_PLUGIN_ROOT}`; it runs **in addition to** your existing hooks and any
other plugins (additive composition — see [docs/architecture.md](docs/architecture.md)).

> **Prerequisite**: the hook shells out to `ruff` (and optionally `hypothesis`
> for Phase 2, `pyright` for a type-check base). Install what you use:
> `pip install ruff hypothesis`.

#### Track B — standalone hook (manual wiring)

Create `.claude/settings.local.json` in your project:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python -X utf8 /absolute/path/to/algebraic-filter/hooks/posttool_af_check.py"
          }
        ]
      }
    ]
  }
}
```

> **Windows note**: Use **forward slash** (`/`) in command paths. Backslash (`\`) is escape-stripped by bash and causes path mangling that prevents hook startup.

## Quick Start

### 1. Manual violation detection

```bash
# Phase 1 (ruff integration)
python -m ruff check --select=PERF,SIM,FURB,ANN,F samples/violations/perf401_manual_list_comp.py

# Phase 3 (AF original AST rules)
python -c "from af_phase3.static_checker import check_file; print(check_file('samples/violations/intermediate_list_chain.py'))"

# Phase 2 (algebraic-law PBT auto-generation)
python -c "
import sys; sys.path.insert(0, 'samples/violations')
from monoid_associativity_violation import my_sum
from af_phase2.generator import auto_test
print(auto_test(my_sum))
"
```

### 2. Automatic hook integration in Claude Code session

When Claude writes violating code to e.g. `scratch/test_target.py`, the PostToolUse hook:
1. Detects Phase 1 ruff PERF/SIM/FURB/ANN/F violations
2. Detects Phase 3 AST original rules (intermediate list chain / dict.keys() list / etc.)
3. Injects Phase 4 structured feedback (`{violation_law, alternative_skeleton, fix_example}`) via `additionalContext`
4. Accumulates anti-patterns (pre-emptive hint on 3rd repeat of same violation)

Claude parses the hook's structured feedback and enters a **self-correction cycle**.

### 3. A/B measurement (automated)

```bash
# 5 tasks × 2 rounds (~5 min)
python scripts/ab_automation.py

# 12 samples × 2 rounds (~10 min, manifest-driven)
python scripts/ab_automation_wide.py
```

Results saved to `docs/_ab_measurement/log_auto_*.json`.

## Architecture

### Phase 1: PostToolUse hook (integration layer)
- [hooks/posttool_af_check.py](hooks/posttool_af_check.py) — 3-layer integration: Phase 1 ruff + Phase 3 AST + Phase 4 structured feedback

### Phase 2: Algebraic-law PBT auto-generation ([af_phase2/](af_phase2/))
- `inferrer.py` — Function name → law ID inference via **word-boundary token** match (not substring) + intent synonyms; type-strategy auto-selection
- `law_templates.py` — 13 law templates (Monoid / Functor / Foldable / Monad / Semigroup / Eq / Commutativity / Idempotence)
- `generator.py` — `auto_test()` / `auto_test_monad_pair()` / `auto_test_class_idempotence()` APIs
- `crosshair_bridge.py` — **opt-in** (`AF_CROSSHAIR`/`crosshair_verify`) CrossHair SMT **proof** of associativity/commutativity for binary functions (deterministic; catches rare-value violations sampling misses, FP-zero — measured). Default OFF.

> **Scope of "auto-generation"**: law inference is a **keyword + type heuristic**,
> not a general prover. It fires only when a function's name/signature matches a
> known pattern (e.g. `sum`/`merge`/`concat` → Monoid; `fmap`/`map` → Functor).
> On AF's own 46-sample corpus it activates on ~15 (the algebraically-shaped
> ones); on arbitrary code it may not fire at all. monad-pair laws need the
> explicit `auto_test_monad_pair()` API (not auto-wired into the hook runner).

### Phase 3: Data-movement feedback ([af_phase3/](af_phase3/))
- `static_checker.py` — AST visitor with AF-original 4 rules (intermediate-list-chain / dict-keys-list / explicit-copy / string-concat-in-loop)
- `runtime_checker.py` — tracemalloc measurement + threshold judgment + `RuntimeViolation` structured payload
- `scalpel_bridge.py` — Scalpel CFG analysis via Python 3.10 Docker container (workaround for typed-ast Python 3.13 incompatibility)

### Phase 4: LLM-optimized feedback formatting ([af_phase4/](af_phase4/))
- `feedback_formatter.py` — Unifies Phase 1 + Phase 2 + Phase 3 violations into a 5-field schema (layer / location / law / skeleton / fix_example); shape variants (`AF_FEEDBACK_SHAPE`)
- `anti_pattern_tracker.py` — JSON history persistence + per-rule-threshold pre-emptive hint
- `phase2_runner.py` — opt-in hook-time Phase 2 runner (`AF_HOOK_PHASE2_PBT` hypothesis sampling and/or `AF_CROSSHAIR` proof)
- `config.py` — switch layer: `.algebraic-filter.json` (or `AF_CONFIG_PATH`) with env override; safe defaults (all risky/heavy behavior OFF)

### Config & switches
All risky/heavy layers are opt-in, default OFF, auditable in one file
([.algebraic-filter.json.example](.algebraic-filter.json.example)). Precedence:
**env var > `.algebraic-filter.json` > safe default**.

| Switch | Env | Default | Effect |
|---|---|---|---|
| Phase 2 runtime (hypothesis) | `AF_HOOK_PHASE2_PBT` | OFF | import + execute the written module to property-test inferred laws |
| CrossHair proof | `AF_CROSSHAIR` | OFF | SMT-prove assoc/commut of binary functions (deterministic) |
| Feedback shape | `AF_FEEDBACK_SHAPE` | `verbose` | `verbose` / `skeleton_only` / `minimal` |

### Sample / Test corpus ([samples/violations/](samples/violations/))
- 46 violation samples + 46 ground-truth fixes + [manifest.json](samples/violations/manifest.json) (specification layer with expected_detection / what_to_verify / what_is_the_problem / expected_fix for each sample)
- TDD growth: adding a manifest entry → pytest parametrize auto-grows the test suite (touch-less expansion design)

## Phase 0 – Phase 5 status

| Phase | Status | Highlights |
|---|---|---|
| 0 Pre-reg + baseline | ✓ closed (2026-05-19) | H1-H4 / S0-1〜S0-5 all met, LayerForge baseline confirmed |
| 1 PostToolUse hook | ✓ end-to-end verified | 46 samples + 5 hook tests + 4 A/B tests |
| 2 Algebraic-law PBT auto-generation | ✓ deepened | 13 laws; 100% on the hypothesis-target subset, ~21.7% across the full 46-sample corpus (specialized niche) |
| 3 Data movement | ✓ extended | 4 AST rules + tracemalloc + Scalpel Docker bridge |
| 4 LLM-optimized feedback | ✓ integrated + A/B verified | Unified schema (Phase 1+2+3) + history + per-rule threshold + pre-emptive hint |
| 5 OSS release | ✓ initial push | GitHub public repo + v0.1.0 release |

## Documentation index

### Top-level

| File | Content |
|---|---|
| [USAGE.md](USAGE.md) | Usage guide (4 use cases: hook activation / manual CLI / Phase 2 API / A/B measurement) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide (sample addition / law extension / Phase 3 static rule addition / PR checklist) |
| [LICENSE](LICENSE) | MIT License |

### `docs/`

| File | Content |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Detailed architecture (two-layer / 3-layer pipeline / AET-OS Layer 3 mapping / Phase 0-5 composition) |
| [docs/hybrid_setup.md](docs/hybrid_setup.md) | Hybrid setup guide — run a base quality tool (claude-code-quality-hook / pyright) + AF as +α, with verified composition |
| [docs/limitations.md](docs/limitations.md) | Measured boundaries — what AF does / extends / structurally cannot (false-negative probes + Phase 2 38% name coverage + structure-vs-intent line) |
| [docs/evidence_summary.md](docs/evidence_summary.md) | Evidence summary (A/B clean re-measurement OFF 0/5→ON 5/5 ANN-dominated; +80%/+8.3% retracted / Phase 0 H1-H4 / Phase 2 100% subset / Phase 3 100% subset / end-to-end Claude self-correction) |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Known issues + countermeasures (Windows path mangling / Scalpel typed-ast / memray Windows / session reload / auto-mode classifier) |

Japanese versions: [README.ja.md](README.ja.md), [USAGE.ja.md](USAGE.ja.md), [CONTRIBUTING.ja.md](CONTRIBUTING.ja.md), and [docs/*.ja.md](docs/) (`.ja` suffix files).

## Related projects

- **philosophy filter** (policy layer): "machine-verifiable → AI executes / not verifiable → reject" judgment. AF is its physical-implementation arm.
- **AET-OS** (Agentic Evolutionary Technology - Operating System): Verified Orchestrator Pattern. AF implements its Layer 3 (Verification Layer).

## References

- Banerjee et al. *CRANE: Reasoning with constrained LLM generation*, 2025 — Trade-off of constrained decoding
- Mündler et al. *Type-Constrained Code Generation with Language Models*, PLDI 2025 — Effect of type constraints
- He et al. *Use Property-Based Testing to Bridge LLM Code Generation and Validation*, 2025 — PBT × LLM
- Maaz et al. *Agentic Property-Based Testing: Finding Bugs Across the Python Ecosystem*, [arXiv:2510.09907](https://arxiv.org/abs/2510.09907) — Complementary direction to AF Phase 4
- VeCoGen (Sevenhuijsen et al., 2025 FormaliSE) — C-targeted; AF occupies independent Python skill-layer niche

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues / PRs welcome. To add a violation sample, edit [samples/violations/manifest.json](samples/violations/manifest.json) plus add files under [samples/violations/](samples/violations/) and [samples/violations/fixed/](samples/violations/fixed/). The manifest-driven TDD-growth design auto-grows the test suite.
