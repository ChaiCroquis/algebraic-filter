---
name: 🧪 New violation sample request
about: Propose a new violating pattern to add to samples/violations/ (manifest-driven TDD growth)
title: "[SAMPLE] "
labels: sample, good first issue
assignees: ''
---

<!-- 違反サンプル追加のための提案 issue。 既存 46 sample に重複しない pattern を articulate してください。 -->
<!-- A proposal to add a new violating pattern. Avoid duplicating any of the existing 46 samples. -->

## Sample ID

<!-- snake_case + 衝突しないよう既存 manifest.json を確認 / Check manifest.json to avoid ID collision -->
<!-- 例: my_new_violation_id -->

## Violation category

<!-- どの Layer / どの rule_source か / Which Layer + rule_source -->

- [ ] Layer 1 (ruff PERF / SIM / FURB / ANN / F / B / UP / RUF / C / etc.)
- [ ] Layer 2 (algebraic-law: Monoid / Functor / Monad / Foldable / Eq / Commutativity / Idempotence)
- [ ] Layer 3 (data movement: intermediate list / dict.keys() list / copy chain / string concat in loop / etc.)
- [ ] Other AF-original

## Violating code (what to land in `samples/violations/<id>.py`)

```python
"""
violation: <rule_id> (<rule_name>)
expected_detection: <tool> --select=<category>
"""

def buggy_function(...):
    # 違反コード / violating code
    ...
```

## Ground-truth fix (what to land in `samples/violations/fixed/<id>.py`)

```python
"""ground truth (fixed) for <id>"""

def buggy_function(...) -> ...:
    # 修正後コード (ruff PASS expected) / fixed code (ruff PASS expected)
    ...
```

## What to verify (= AF が検証する内容)

What aspect of the violating code does the AF hook need to detect?

## What is the problem (= 何が問題か、 副次影響まで)

Why is the violating code problematic? Include secondary effects (testability / cache / performance / memoization / etc.)

## Detection tool + command

```bash
# 例 / Example:
python -m ruff check --select=<category> samples/violations/<id>.py
# Expected exit code: 1
# Expected output marker: <rule_id>
```

## Checklist

- [ ] I read [CONTRIBUTING.en.md §1](https://github.com/ChaiCroquis/algebraic-filter/blob/main/CONTRIBUTING.en.md#1-adding-violation-samples-most-common-contribution) — the 3-step + 1 test partition procedure
- [ ] ID does not collide with existing 46 samples in [manifest.json](https://github.com/ChaiCroquis/algebraic-filter/blob/main/samples/violations/manifest.json)
- [ ] I'm willing to submit a PR with sample + ground truth + manifest entry (3 file pair)
