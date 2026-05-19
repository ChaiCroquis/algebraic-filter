# USAGE — algebraic-filter user guide

[日本語版 USAGE](USAGE.ja.md)

Four primary use cases of AF:

1. [Enable hook in Claude Code session](#1-enable-hook-in-claude-code-session)
2. [Manual violation detection via CLI](#2-manual-violation-detection-via-cli)
3. [Phase 2 algebraic-law PBT auto-generation API](#3-phase-2-algebraic-law-pbt-auto-generation-api)
4. [A/B measurement of AF effect](#4-ab-measurement-of-af-effect)

---

## 1. Enable hook in Claude Code session

### 1-1. Install

```bash
git clone https://github.com/ChaiCroquis/algebraic-filter.git
cd algebraic-filter
pip install -e .
```

### 1-2. Project-local hook registration

Create `.claude/settings.local.json` in your project root (merge if file exists):

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

**Windows users required**: Use **forward slash** (`/`) in command paths. Backslash (`\`) gets stripped (`\w`, `\a`, `\h`, `\p`) by bash escape rules, causing path mangling that prevents hook startup. Details: [docs/troubleshooting.md](docs/troubleshooting.md)

### 1-3. Start Claude Code session and verify

```bash
# In your AF project or any project that uses AF
cd /path/to/your-project
claude
```

In the session, ask Claude to write violating code:

```
Write the following code to scratch/test_hook.py and then fix the PERF401 violation:

def double_positives(data):
    result = []
    for x in data:
        if x > 0:
            result.append(x * 2)
    return result
```

Expected behavior:
1. Claude writes `scratch/test_hook.py` via the Write tool
2. AF hook fires → ruff PERF401 detected → exit 2 + structured feedback
3. Claude parses the feedback (skeleton + fix_example) and rewrites as a list comprehension
4. Claude calls Edit again → hook fires again → remaining violations (ANN001/ANN201) detected → another feedback
5. Claude adds type annotations → hook passes (exit 0)

---

## 2. Manual violation detection via CLI

### 2-1. Phase 1 (ruff integration)

```bash
python -m ruff check --select=PERF,SIM,FURB,ANN,F samples/violations/perf401_manual_list_comp.py
```

### 2-2. Phase 3 (AF original AST rules)

```python
from af_phase3.static_checker import check_file

violations = check_file("samples/violations/intermediate_list_chain.py")
for v in violations:
    print(f"{v.rule_id} (line {v.line}): {v.message}")
```

Detected rules (4):
- `intermediate-list-chain` — `list(map/filter(..., list(...)))`
- `dict-keys-list` — `list(d.keys())` / `list(d.values())`
- `explicit-copy` — `.copy()` method call
- `string-concat-in-loop` — `result += x` inside a for-body

### 2-3. Phase 3 runtime tracemalloc

```python
from af_phase3.runtime_checker import check_threshold
from samples.violations.intermediate_list_chain import transform

data = list(range(10000))
violation, measurement = check_threshold(transform, data, max_bytes=100*1024)
if violation:
    print(f"{violation.rule_id}: {violation.measured_bytes} bytes > {violation.threshold_bytes}")
print(f"function {measurement.function_name}: {measurement.total_size_bytes} bytes, {measurement.allocation_count} allocations")
```

### 2-4. Phase 4 structured feedback formatter

```python
from af_phase4.feedback_formatter import combine_violations
from af_phase3.static_checker import check_file

ruff_output = "..."  # output of `ruff --select=PERF,...`
phase3_violations = check_file("path/to/file.py")
combined = combine_violations(ruff_output, phase3_violations, "path/to/file.py")
for v in combined:
    print(f"[{v['layer']}] {v['violation_law']} at {v['violation_location']}")
    print(f"  skeleton: {v['alternative_skeleton']}")
    print(f"  fix: {v['fix_example']}")
```

---

## 3. Phase 2 algebraic-law PBT auto-generation API

### 3-1. Single callable

```python
from af_phase2.generator import auto_test
from samples.violations.monoid_associativity_violation import my_sum

results = auto_test(my_sum)
for r in results:
    print(f"law={r.law_id} status={r.status}")
    if r.error:
        print(f"  error: {r.error}")
```

Expected output:
```
law=monoid_identity status=FAIL
  error: my_sum([1])=-1, sum=1
law=monoid_associativity status=FAIL
  ...
```

Inference rules (function name keywords + type signatures):
- `sum / fold / aggregate / reduce` → `monoid_identity` + `monoid_associativity`
- `map / fmap / transform` → `functor_identity` + `functor_compose`
- `merge / average / intersect / union / combine` → `commutativity`

### 3-2. Monad pair (pure + bind)

```python
from af_phase2.generator import auto_test_monad_pair
from samples.violations.monad_left_identity_violation import pure, bind

results = auto_test_monad_pair(pure, bind)
# → 3 laws: monad_left_identity / monad_right_identity / monad_associativity
```

### 3-3. Class-based idempotence

```python
from af_phase2.generator import auto_test_class_idempotence
from samples.violations.idempotence_violation_in_named_set_add import FakeSet

results = auto_test_class_idempotence(FakeSet, "add")
```

---

## 4. A/B measurement of AF effect

### 4-1. Automated (nested claude --print)

5 tasks × 2 rounds:
```bash
python scripts/ab_automation.py
```

12 samples × 2 rounds (manifest-driven):
```bash
python scripts/ab_automation_wide.py
```

Results saved to `docs/_ab_measurement/log_auto_*.json`.

### 4-2. Manual A/B (separate Claude session)

Procedure: [docs/_ab_measurement/protocol.md](docs/_ab_measurement/protocol.md)

```powershell
# Round 1 hook OFF
Move-Item .claude\settings.local.json .claude\settings.local.json.disabled
claude   # → submit 5 tasks in order

# Round 2 hook ON
Move-Item .claude\settings.local.json.disabled .claude\settings.local.json
claude   # → repeat same 5 tasks with _on suffix
```

Log template: [docs/_ab_measurement/log_template.md](docs/_ab_measurement/log_template.md)

### 4-3. Metrics and judgment

| Metric | Measurement | Phase 1 withdrawal criterion |
|---|---|---|
| pass@1 improvement (full-layer success rate) | Number of samples reaching 0 violations via `ruff --select=PERF,SIM,FURB,ANN,F` | AF effective if +5% or more |
| Edit-cycle count | Number of Claude Edit-tool invocations | AF effective if -10% or more |
| Side-effect detection | New violations beyond the original one | 0 (ideal) |

Judgment: AF withdrawal triggered only if **both** "pass@1 +5% improvement" and "Edit cycles -10% improvement" fail. Either one met → AF retained.

---

## See also

- [README.md](README.md) — Overview + design philosophy
- [docs/architecture.md](docs/architecture.md) — Detailed architecture
- [docs/evidence_summary.md](docs/evidence_summary.md) — A/B measurement + per-Phase evidence
- [docs/troubleshooting.md](docs/troubleshooting.md) — Known issues + countermeasures
- [CONTRIBUTING.md](CONTRIBUTING.md) — Adding violation samples / TDD growth
