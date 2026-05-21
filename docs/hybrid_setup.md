# Hybrid setup — base quality tool + algebraic-filter (+α)

[日本語版](hybrid_setup.ja.md)

How to run **claude-code-quality-hook (base) + algebraic-filter (+α)** together
so each fires on every `.py` write and catches its own defect class:

- **base** ([claude-code-quality-hook](https://github.com/dhofheinz/claude-code-quality-hook)):
  ruff defaults + **pyright type-checking** + (optional) 3-stage AI repair.
- **+α** (algebraic-filter): algebraic-law PBT (Layer 2) + data-movement (Layer 3) —
  the defect classes pyright/ruff can't see.

These are complementary: in measurement the two detect **disjoint** defects
(type errors vs algebraic-law violations), so running both loses nothing.
Verified end-to-end (see [Verification](#verification) below).

## Prerequisites

Use a venv so nothing is installed globally (pyright is pip-installable — no
global `npm` needed):

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   |   macOS/Linux: source .venv/bin/activate
pip install ruff hypothesis pyright   # ruff: both tools; hypothesis: AF Phase 2; pyright: base type-check
```

> Launch `claude` **from the activated venv** so both hooks (which call bare
> `python`) inherit the venv's deps.

## Step 1 — base: claude-code-quality-hook

```bash
git clone https://github.com/dhofheinz/claude-code-quality-hook
cd claude-code-quality-hook
./setup.sh        # writes .claude/settings.json hook + .quality-hook.json
```

Recommended base config (`.quality-hook.json`) — **detection + block only**,
which avoids the AI-repair stage (it spawns nested `claude` agents and is not
Windows-ready):

```json
{
  "type_checking": { "enabled": true },
  "claude_code": { "enabled": false }
}
```

> **Windows**: the base crashes on cp932 when printing its `✓` output. Run
> Claude Code (and the hook) with `PYTHONUTF8=1` set in the environment.

This wires the base hook into your project's `.claude/settings.json`.

## Step 2 — +α: algebraic-filter plugin

Inside a Claude Code session, in your target project:

```
/plugin marketplace add ChaiCroquis/algebraic-filter
/plugin install algebraic-filter@algebraic-filter-marketplace --scope local
```

`--scope local` keeps AF active **only in this project** (not all your
projects). Optional — enable the algebraic-law runtime (executes the written
module; trusted/throwaway dirs only):

```json
// .algebraic-filter.json in the project root
{ "phase2_runtime": true }
```

## Step 3 — how composition behaves

Both hooks are `PostToolUse` on `Write|Edit|MultiEdit`. The base lives in
`.claude/settings.json`; AF is a plugin hook. Claude Code runs **both** on each
edit (settings hooks + plugin hooks compose — neither overrides the other):

- a **type error** → base blocks (pyright) with its feedback
- an **algebraic-law / data-movement** defect → AF blocks with its structured feedback
- a file with **both** → both fire, each reporting its own defect class

## Caveats

- **Verbosity**: when both fire, Claude sees two feedback blocks. Not a
  conflict, just more text. (If too noisy, narrow the base's rule set or use
  AF's `feedback_shape: minimal`.)
- **Hook order is not guaranteed** between settings hooks and plugin hooks;
  treat them as unordered. For pure detection+block this is irrelevant.
- **ruff runs twice** (base: ruff defaults; AF: PERF/SIM/FURB/ANN/F/RUF013) —
  different rule sets, minor double work (~16ms each via the ruff binary).
- **Windows**: keep `PYTHONUTF8=1` for the base.

## Verification

This hybrid was measured 2026-05-21 (real competitor hook, not a mock). On a
file with both a type error and a `monoid_identity` violation:

- base (competitor) → `exit 2`, pyright caught
  `reportReturnType: "None" is not assignable to "int"`
- AF (+α) → `exit 2`, Phase 2 caught `monoid_identity at target.py:4`
  (recorded to history: [_plugin_verification/hybrid_competitor_plus_af_2026-05-21.json](_plugin_verification/hybrid_competitor_plus_af_2026-05-21.json))

Both fired independently, each catching its own defect class = the +α layer
composes cleanly on top of the base. See also [evidence_summary.md](evidence_summary.md) §8.
