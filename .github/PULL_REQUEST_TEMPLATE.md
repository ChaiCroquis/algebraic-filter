<!-- English / 日本語 のどちらか / 両方で記述してください -->

## Summary

What does this PR do? / この PR は何をしますか?

## Type of change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 🧪 New violation sample (manifest-driven TDD growth, see [CONTRIBUTING §1](../CONTRIBUTING.md#1-adding-violation-samples-most-common-contribution))
- [ ] 📐 New law template / detection rule (see [CONTRIBUTING §2-3](../CONTRIBUTING.md))
- [ ] 📚 Documentation update
- [ ] 🏗️ Refactor / chore (non-breaking, internal)
- [ ] 💥 Breaking change (would cause existing functionality to not work as expected)

## Changes

What was changed?  / 何が変更されましたか?

- ...
- ...

## Affected Phases / 影響範囲

- [ ] Phase 1 (PostToolUse hook / `hooks/posttool_af_check.py`)
- [ ] Phase 2 (algebraic-law PBT / `af_phase2/`)
- [ ] Phase 3 (data movement / `af_phase3/`)
- [ ] Phase 4 (feedback formatting / `af_phase4/`)
- [ ] Samples / `samples/violations/`
- [ ] Tests / `samples/violations/tests/`
- [ ] Documentation / `README` / `USAGE` / `docs/`
- [ ] CI / `.github/workflows/`

## Verification

How was this tested? / どう検証しましたか?

- [ ] `python -m ruff check af_phase2 af_phase3 af_phase4 hooks scripts` — All checks passed
- [ ] `python -m pytest samples/violations/tests/ --ignore=samples/violations/tests/test_af_phase3_scalpel_bridge.py` — All tests passed
- [ ] (If hypothesis-target sample added) conftest `collect_ignore_glob` updated
- [ ] (If tracemalloc-target sample added) driver script + manifest command consistent
- [ ] CI on the PR branch is green (will be checked automatically)

## Evidence (if applicable)

For violation samples / law templates: paste the detection evidence (e.g. ruff output, hypothesis Falsifying example, tracemalloc allocation).

```
<evidence here>
```

## Checklist

- [ ] I read [CONTRIBUTING.md](../CONTRIBUTING.md) (or [CONTRIBUTING.md](../CONTRIBUTING.md))
- [ ] My code follows the project's style (ruff E/F/W on CI target packages)
- [ ] I added tests where applicable (= manifest entry auto-grows test count for sample additions)
- [ ] I updated documentation where relevant
- [ ] Commit messages follow the project pattern (one-line summary + optional body + Co-Authored footer if AI-assisted)

## Related issues

Closes #<issue-number>
