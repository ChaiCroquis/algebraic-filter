---
name: 🐛 Bug report
about: Report a defect (hook not firing / wrong detection / unexpected behavior)
title: "[BUG] "
labels: bug
assignees: ''
---

<!-- English / 日本語 のどちらか / 両方で記述してください -->

## Summary

What is wrong? / 何が起きていますか?

## Environment

- OS: <!-- e.g. Windows 11 / macOS 14.5 / Ubuntu 24.04 -->
- Python: <!-- python --version -->
- algebraic-filter version: <!-- v0.1.0 等、 git rev-parse HEAD でもよい -->
- Claude Code CLI: <!-- claude --version -->

## Steps to reproduce

1. ...
2. ...

## Expected behavior

What did you expect? / 何を期待していましたか?

## Actual behavior

What actually happened? / 実際に何が起きましたか?

エラーメッセージ / log がある場合は articulate してください:

```
<error log here>
```

## Checklist

- [ ] I read [docs/troubleshooting.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/docs/troubleshooting.md) or [docs/troubleshooting.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/docs/troubleshooting.md) — common defects (Windows path mangling / Scalpel typed-ast / memray Windows / session reload / auto-mode classifier) are covered there
- [ ] I verified locally with `pytest samples/violations/tests/` before reporting
- [ ] I attached relevant logs / stack traces
