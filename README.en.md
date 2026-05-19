# algebraic-filter

**Algebraic-law-level machine verification guardrail for AI-generated code** — A Claude Code skill + PostToolUse hook that auto-validates Python code at write-time and triggers Claude's self-correction cycle on violations.

[日本語版 README](README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ChaiCroquis/algebraic-filter/actions/workflows/ci.yml/badge.svg)](https://github.com/ChaiCroquis/algebraic-filter/actions/workflows/ci.yml)

## Overview

AI-generated code contains a large amount of algebraic structural defects (purity violations, broken associativity, excessive data movement, etc.) that are invisible to `pass@1` evaluation. algebraic-filter (AF) post-validates `Write`/`Edit` via Claude Code's **PostToolUse hook** and, on violation, returns `exit code 2 + structured feedback` to trigger Claude's **self-correction cycle**.

### Design philosophy

- **Hook over constrained decoding**: CRANE (2025) showed that strong decoding constraints degrade LLM reasoning. AF uses post-hoc verification to preserve LLM autonomy while keeping verification deterministic (zero hallucination).
- **Two-layer structure**: philosophy filter (policy layer) + algebraic-filter (physical layer, this OSS), complementary design. The policy layer uses a 4-step decision tree: (1) machine-verifiable → AI runs / (2) 100% reproducible → AI runs / (3) business domain → user-only / (4) reduces cognitive load → AI default-runs, else drop the task. "I want it easy" = cognitive-load reduction is the top principle that articulates the AI delegation boundary. Details: [docs/philosophy_filter_integration.en.md](docs/philosophy_filter_integration.en.md) (includes individual-integration paths).
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

## Action evidence (Phase 1 withdrawal-criterion cleared)

A/B measurement automated via `claude --print` nested sessions:

| Evaluation niche | hook OFF completion | hook ON completion | delta |
|---|---|---|---|
| **AI-generated raw code** (no type annotations, 5 samples) | 20% | 100% | **+80%** |
| **Curated code** (typed, 12 samples) | 91.7% | 100% | +8.3% |

Both niches clear Phase 1 withdrawal criterion (`pass@1 +5%`) = AF effectiveness substantiated.

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

### Claude Code hook registration

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
- `inferrer.py` — Function signature → law ID inference (12 keywords + type-strategy auto-selection)
- `law_templates.py` — 13 law templates (Monoid / Functor / Foldable / Monad / Semigroup / Eq / Commutativity / Idempotence)
- `generator.py` — `auto_test()` / `auto_test_monad_pair()` / `auto_test_class_idempotence()` APIs

### Phase 3: Data-movement feedback ([af_phase3/](af_phase3/))
- `static_checker.py` — AST visitor with AF-original 4 rules (intermediate-list-chain / dict-keys-list / explicit-copy / string-concat-in-loop)
- `runtime_checker.py` — tracemalloc measurement + threshold judgment + `RuntimeViolation` structured payload
- `scalpel_bridge.py` — Scalpel CFG analysis via Python 3.10 Docker container (workaround for typed-ast Python 3.13 incompatibility)

### Phase 4: LLM-optimized feedback formatting ([af_phase4/](af_phase4/))
- `feedback_formatter.py` — Unifies Phase 1 + Phase 3 violations into a 5-field schema (layer / location / law / skeleton / fix_example)
- `anti_pattern_tracker.py` — JSON history persistence + pre-emptive hint on 3rd violation of same rule

### Sample / Test corpus ([samples/violations/](samples/violations/))
- 46 violation samples + 46 ground-truth fixes + [manifest.json](samples/violations/manifest.json) (specification layer with expected_detection / what_to_verify / what_is_the_problem / expected_fix for each sample)
- TDD growth: adding a manifest entry → pytest parametrize auto-grows the test suite (touch-less expansion design)

## Phase 0 – Phase 5 status

| Phase | Status | Highlights |
|---|---|---|
| 0 Pre-reg + baseline | ✓ closed (2026-05-19) | H1-H4 / S0-1〜S0-5 all met, LayerForge baseline confirmed |
| 1 PostToolUse hook | ✓ end-to-end verified | 46 samples + 5 hook tests + 4 A/B tests |
| 2 Algebraic-law PBT auto-generation | ✓ deepened | 13 laws + 100% hypothesis-target subset coverage |
| 3 Data movement | ✓ extended | 4 AST rules + tracemalloc + Scalpel Docker bridge |
| 4 LLM-optimized feedback | ✓ minimal prototype | Unified schema + history + pre-emptive hint |
| 5 OSS release | ✓ initial push | GitHub public repo + v0.1.0 release |

## Documentation index

### Top-level

| File | Content |
|---|---|
| [USAGE.en.md](USAGE.en.md) | Usage guide (4 use cases: hook activation / manual CLI / Phase 2 API / A/B measurement) |
| [CONTRIBUTING.en.md](CONTRIBUTING.en.md) | Contribution guide (sample addition / law extension / Phase 3 static rule addition / PR checklist) |
| [LICENSE](LICENSE) | MIT License |

### `docs/`

| File | Content |
|---|---|
| [docs/architecture.en.md](docs/architecture.en.md) | Detailed architecture (two-layer / 3-layer pipeline / AET-OS Layer 3 mapping / Phase 0-5 composition) |
| [docs/evidence_summary.en.md](docs/evidence_summary.en.md) | Evidence summary (A/B +80%/+8.3% / Phase 0 H1-H4 / Phase 2 100% subset / Phase 3 100% subset / end-to-end Claude self-correction) |
| [docs/troubleshooting.en.md](docs/troubleshooting.en.md) | Known issues + countermeasures (Windows path mangling / Scalpel typed-ast / memray Windows / session reload / auto-mode classifier) |
| [docs/philosophy_filter_integration.en.md](docs/philosophy_filter_integration.en.md) | Two-layer integration design with the philosophy filter (policy layer) — 4-step decision tree + AF as physical-layer implementation + 4 paths for individual integration |

Japanese versions: [README.md](README.md), [USAGE.md](USAGE.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [docs/*.md](docs/) (non-`.en` suffix files).

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
