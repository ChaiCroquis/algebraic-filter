---
name: 💡 Feature request
about: Suggest a new check / law template / Phase extension / integration
title: "[FEAT] "
labels: enhancement
assignees: ''
---

<!-- English / 日本語 のどちらか / 両方で記述してください -->

## Motivation

Why is this needed? / なぜ必要ですか?

What problem does it solve in AI-generated code detection / verification? / AI 生成コードの検出 / 検証で何が解決されますか?

## Proposed solution

What would the feature look like? / 機能はどう articulate されますか?

If applicable, which layer would it land in?

- [ ] Phase 1 (PostToolUse hook / ruff rule selection)
- [ ] Phase 2 (algebraic-law PBT template — Functor / Monad / Traversable / etc.)
- [ ] Phase 3 (data movement — AST static rule / runtime measurement)
- [ ] Phase 4 (LLM-optimized feedback formatting)
- [ ] Other / その他: <!-- describe -->

## Alternatives considered

What other approaches did you consider? / 他にどんな選択肢を検討しましたか?

## Additional context

- References (papers / OSS / Haskell type-class laws / etc.)
- Example violation sample that this feature would catch:

```python
# example code
```

## Checklist

- [ ] I read [CONTRIBUTING.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/CONTRIBUTING.md) (or [CONTRIBUTING.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/CONTRIBUTING.md)) — extension procedures are documented
- [ ] This feature aligns with one of the 3 differentiation axes: (1) algebraic-law PBT auto-generation / (2) data-movement empirical feedback / (3) LLM-optimized feedback shape
- [ ] If adding a new violation pattern, I'm willing to also add the sample + ground-truth pair (per CONTRIBUTING)
