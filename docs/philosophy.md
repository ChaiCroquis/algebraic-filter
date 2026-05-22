# Why algebraic-filter exists

[日本語版](philosophy.ja.md)

> Aim high, stay honest. This document holds both: the large ideal AF is reaching
> for, and the honest, modest reality of what it guarantees today.

## The one-sentence thesis

AI code generation is **probabilistic** — it samples plausible code, it does not
prove anything. algebraic-filter carves a **deterministically-guaranteed island
out of that probabilistic ocean**: a set of properties that, for any code passing
the hook, are *certified* true by deterministic tools (no sampling, no LLM, no
"probably"). Inside that island a human no longer has to review those properties.

**Expanding the island = expanding how much you can safely delegate to AI without
checking it yourself.** That is the whole point.

## The ideal (aim high)

- **Determinism over probabilism.** Every property moved from "trust the AI, then
  a human reviews it" to "a deterministic tool proves it" is risk *removed*, not
  risk *reduced*. A proven associativity cannot silently regress; a probabilistic
  "looks right" can.
- **Shrink the human review surface.** The dream is a growing region where the
  question "did the AI get this right?" is replaced by "this class of error cannot
  have shipped." Review effort then concentrates only on what is genuinely
  un-formalizable.
- **The physical arm of a two-layer guardrail.** A policy layer (the *philosophy
  filter*) decides "machine-verifiable → delegate to AI / not verifiable → keep a
  human." AF is the physical layer that *enforces that decision at code-write
  time* via the hook.
- **A serious lineage, re-aimed.** "Expand the deterministically-verifiable region"
  is the 50-year program of formal methods — type systems, SMT solvers, CrossHair,
  Frama-C. The method is Lindy-strong. The timely, novel angle is pointing it at
  the question AI suddenly made urgent: **how much can I *not* check and still be
  safe?** A trust boundary, drawn at the moment code is written.
- **North star.** Widen the island until delegating to AI, on the axes it covers,
  requires zero human worry.

## The reality (stay honest)

The island is, today, **thin**. On code that passes the hook, AF deterministically
certifies only:

| Guaranteed axis | Tool | Honest note |
|---|---|---|
| Lint (PERF / SIM / FURB / ANN / F / RUF013) | ruff | Real, but this is ruff — not unique to AF |
| Data-movement (intermediate-list / dict-keys-list / explicit-copy / string-concat-in-loop) | AF AST | 4 rules, AF's own contribution |
| Algebraic-law violations (Monoid / Functor / …) | hypothesis | **Only on name-recognized functions** (~50% keyword coverage; two-sided error) |
| Associativity / commutativity, proven | CrossHair (opt-in) | The part that is genuine **proof**, not rule-matching — but narrow (binary funcs only) |

**Outside the island — still probabilistic, still the human's job:** logic
correctness, security, concurrency, and spec/intent. AF does not touch these. It
verifies *structure*, never *intent*.

Two honest properties of the mechanism itself:

- **The hook is advisory, not forcing.** It *certifies what passes*; it does not
  compel the AI to produce passing code. Instruct "write exactly this" and the
  model keeps it despite the hook. So this is *conditional certification* ("if it
  passed, these axes are clean"), not enforcement.
- **Measured value is modest, and honestly so.** The in-vivo A/B — after an
  earlier overclaim (+80%) was retracted for being mis-measured — is OFF 0/5 → ON
  5/5 clean, driven almost entirely by the type-annotation axis on a capable model.
  See [evidence_summary.md](evidence_summary.md) §1 and
  [limitations.md](limitations.md).

## The danger we deliberately guard against

**False confidence is the failure mode.** "AF passed, so it's safe" is true *only*
for the axes AF covers. If a human reads an AF pass as "logic and security were
reviewed," the safety device becomes a hazard — it licenses skipping review that
was never done. So the island's shoreline is **painted loudly and always**: every
claim ships with its scope (see [limitations.md](limitations.md) "What
'verification' precisely means"). A guarantee whose boundary is unclear is worse
than no guarantee.

## Honest current standing

AF is **not a finished cathedral. It is the first, thin, honestly-measured island
of a serious idea.** Its value scales with the island's area, and growing that
area is the explicit, stated program — not an afterthought. A capable model that
already writes clean code does not diminish this: it means the guardrail confirms
cleanliness cheaply and catches the occasional miss, which is exactly what a
guardrail should do.

Aim high — a world where AI-written code can be safely delegated on ever more axes.
Stay honest — today that is a small but real, deterministically-guaranteed slice,
with its boundary drawn in plain sight.
