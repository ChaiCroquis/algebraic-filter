# Contributing to algebraic-filter

[日本語版 CONTRIBUTING](CONTRIBUTING.md)

Three primary contribution axes: violation sample addition / law template extension / hook improvement.

## Quick principles

1. **Violation samples are an invariant**: Files under `samples/violations/*.py` are an audit trail paired with ground-truth fixes. They are not edited as "fix targets" — the design is "add new ones, don't touch existing ones."
2. **Manifest-driven TDD growth**: Adding an entry to `samples/violations/manifest.json` auto-grows the pytest parametrize test count.
3. **Three-layer complementarity**: Phase 1 (ruff) / Phase 2 (algebraic-law PBT) / Phase 3 (data movement) / Phase 4 (feedback formatting) each occupy independent contribution niches, designed to leverage each other's outputs.

---

## 1. Adding violation samples (most common contribution)

### Steps (3 + 1 test partition)

1. **Write the violating code in `samples/violations/<id>.py`**:
   ```python
   """
   violation: <rule_id> (<rule_name>)
   expected_detection: ruff --select=<category>
   expected_skeleton: <fix skeleton>
   expected_fix:
       <fix code example>
   """
   
   def buggy_function(x):
       # violating code
       ...
   ```

2. **Write the ground-truth fix in `samples/violations/fixed/<id>.py`**:
   ```python
   """ground truth (fixed) for <id>"""
   
   def buggy_function(x: int) -> int:
       # corrected code (ruff PASS)
       ...
   ```

3. **Add an entry to `samples/violations/manifest.json`** (copy an existing entry and substitute values):
   ```json
   {
     "id": "<id>",
     "file": "<id>.py",
     "category": "Layer 1 static (ruff <category>)",
     "violation": {
       "type": "<violation type slug>",
       "name": "<short name>",
       "rule_source": "ruff <rule_id>"
     },
     "expected_detection": {
       "tool": "ruff",
       "rule_id": "<rule_id>",
       "command": "python -m ruff check --select=<category> samples/violations/<id>.py",
       "expected_exit_code": 1,
       "expected_output_marker": "<rule_id>"
     },
     "what_to_verify": "<what is being verified>",
     "what_is_the_problem": "<what is wrong, including secondary effects>",
     "expected_fix": {
       "skeleton": "<fix skeleton>",
       "code_example": "<fix code one-liner>",
       "feedback_payload_template": {
         "violation_law": "<rule_id>",
         "alternative_skeleton": "<skeleton>",
         "fix_example": "<fix one-liner>"
       }
     },
     "verification_result": {
       "phase_0_actual_detection": "PASS",
       "phase_0_evidence": "ruff <rule_id> detected (EXECUTED <date>)"
     }
   }
   ```

4. **Verify auto-grown tests**:
   ```bash
   python -m pytest samples/violations/tests/test_manifest_driven.py -v
   # → ruff_detects_unfixed[<id>] PASSED
   # → ruff_no_violation_in_fixed[<id>] PASSED
   ```

### Per-violation-type addition path

| Violation type | Where to add | Required articulation |
|---|---|---|
| ruff-detectable (PERF/SIM/FURB/ANN/F/B/UP/RUF/C) | Manifest entry only | `expected_detection.tool = "ruff"` |
| hypothesis (algebraic-law) | Manifest + `tests/test_<id>.py` (`@given` test) + update conftest `collect_ignore_glob` | `tool = "hypothesis"`, articulate test file path in command |
| tracemalloc (data movement) | Manifest + `tests/measure_<id>.py` (driver) | `tool = "tracemalloc"`, articulate driver path in command |
| Custom rule (Phase 1+) | Manifest with `verification_result.phase_0_actual_detection = "DEFERRED"` | Detection tool not yet implemented, articulate only |

---

## 2. Phase 2 law template extension

### Add a new law

1. **Add a law factory in `af_phase2/law_templates.py`**:
   ```python
   def my_law(target_func: Callable, element_strategy: Any = None) -> Callable:
       """description (reference Haskell QuickCheck-classes etc.)"""
       strategy = element_strategy if element_strategy is not None else st.integers(...)
       
       @given(strategy)
       def prop(a: Any) -> None:
           # law articulation
           assert ..., f"my_law failed: ..."
       
       return prop
   ```

2. **Register in `LAW_REGISTRY`**:
   ```python
   LAW_REGISTRY: dict[str, Callable] = {
       ...,
       "my_law": my_law,
   }
   ```

3. **Add keyword to `_NAME_TO_LAWS` in `af_phase2/inferrer.py`**:
   ```python
   _NAME_TO_LAWS: dict[str, list[str]] = {
       ...,
       "my_keyword": ["my_law"],
   }
   ```

4. **Add dispatch in `af_phase2/generator.py` `auto_test()`** (extend the `if` chain):
   ```python
   elif law_id == "my_law":
       prop = template(func, element_strategy)
   ```

### Law-design references

- Haskell [`quickcheck-classes`](https://hackage.haskell.org/package/quickcheck-classes) — Eq / Semigroup / Monoid / Functor / Foldable / Traversable / Monad
- Haskell [`checkers`](https://hackage.haskell.org/package/checkers) — morphism properties + standard type classes
- [`Agentic Property-Based Testing` (arXiv 2510.09907)](https://arxiv.org/abs/2510.09907) — LLM-agent-driven property discovery

---

## 3. Phase 3 static rule addition

### Steps

1. **Add a check method to `_DataMovementVisitor` in `af_phase3/static_checker.py`**:
   ```python
   def _check_my_rule(self, node: ast.Call) -> None:
       if # condition:
           self.violations.append(
               StaticViolation(
                   "my-rule-id",
                   node.lineno,
                   f"line {node.lineno}: <message>"
               )
           )
   ```

2. **Call from a visitor entry point** (e.g. `visit_Call`):
   ```python
   def visit_Call(self, node: ast.Call) -> None:
       self._check_my_rule(node)
       # ... existing checks
       self.generic_visit(node)
   ```

3. **Add to Phase 4 lookup tables** (`af_phase4/feedback_formatter.py`):
   ```python
   _PHASE3_SKELETON["my-rule-id"] = "<skeleton>"
   _PHASE3_FIX["my-rule-id"] = "<fix one-liner>"
   ```

4. **Add `samples/violations/<id>.py` + `fixed/<id>.py` + manifest entry** (as in §1 above).

---

## 4. Running tests

### Full suite

```bash
python -m pytest samples/violations/tests/ -v
```

### Per-phase

```bash
# Phase 2 coverage
python -m pytest samples/violations/tests/test_af_phase2_coverage.py -v -s

# Phase 3 data movement
python -m pytest samples/violations/tests/test_af_phase3_data_movement.py -v

# Phase 4 feedback
python -m pytest samples/violations/tests/test_af_phase4_feedback.py -v
```

### Hook smoke test (subprocess dry-run)

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"samples/violations/perf401_manual_list_comp.py"}}' \
  | python -X utf8 hooks/posttool_af_check.py
echo "EXIT=$?"
# → exit 2 + JSON feedback
```

### Scalpel Docker bridge

```bash
docker build -t af-scalpel -f Dockerfile.scalpel .
python -m pytest samples/violations/tests/test_af_phase3_scalpel_bridge.py -v
```

---

## 5. PR submission

### Checklist

- [ ] New violation samples added as pairs under `samples/violations/` + `fixed/`
- [ ] `manifest.json` entry added with all 9 fields articulated
- [ ] `pytest samples/violations/tests/` fully green (existing tests included → no regression)
- [ ] For hypothesis-target samples: test file added + conftest `collect_ignore_glob` updated
- [ ] For tracemalloc-target samples: driver script added + manifest command consistent
- [ ] Commit message articulates change summary + scope of impact

### Issue examples

- "Add violation samples for new ruff rules (e.g. PERF402 / SIM209)"
- "Add Traversable law template (Phase 2 extension)"
- "Static detection for numpy vectorization opportunities (Phase 3 further extension)"
- "Scalene + Ollama integration demo (Phase 4 LLM proposals evaluation)"

---

## See also

- [README.en.md](README.en.md) — Overview
- [USAGE.en.md](USAGE.en.md) — Usage guide
- [docs/architecture.en.md](docs/architecture.en.md) — Detailed architecture
- [samples/violations/manifest.json](samples/violations/manifest.json) — Specification layer (46 sample metadata)
- [docs/troubleshooting.en.md](docs/troubleshooting.en.md) — Known issues + countermeasures
