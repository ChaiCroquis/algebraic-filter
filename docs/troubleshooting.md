# Troubleshooting — algebraic-filter known issues + countermeasures

[日本語版 troubleshooting](troubleshooting.ja.md)

Five defects / limitations + countermeasures discovered during development:

1. [Windows path mangling (hook command backslash escape)](#1-windows-path-mangling-hook-command-backslash-escape)
2. [Scalpel (python-scalpel) Python 3.13 build failure](#2-scalpel-python-scalpel-python-313-build-failure)
3. [memray Windows-native non-support](#3-memray-windows-native-non-support)
4. [Hook session-reload not supported](#4-hook-session-reload-not-supported)
5. [auto-mode classifier blocks nested sessions](#5-auto-mode-classifier-blocks-nested-sessions)

---

## 1. Windows path mangling (hook command backslash escape)

### Symptom

If the hook command in `.claude/settings.local.json` uses backslashes, hook startup fails:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "python -X utf8 C:\\work\\algebraic-filter\\hooks\\posttool_af_check.py"
      }]
    }]
  }
}
```

Error message (verbatim):
```
can't open file 'C:\\work\\algebraic-filter\\workalgebraic-filterhooksposttool_af_check.py'
```

= `\w \a \h \p` are escape-stripped → `workalgebraic-filterhooksposttool_af_check.py` (mangled path)

### Cause

In Claude Code's hook-command invocation path:
- After JSON decoding: `C:\work\algebraic-filter\hooks\posttool_af_check.py`
- Bash-invoked: `\w`, `\a`, `\h`, `\p` get stripped as escape sequences
- Result: `C:workalgebraic-filterhooksposttool_af_check.py`
- Python interprets `C:` as a drive-relative path → concatenated with cwd `C:\work\algebraic-filter`
- Final path: `C:\work\algebraic-filter\workalgebraic-filterhooksposttool_af_check.py` (does not exist)

### Countermeasure: use forward slashes

In `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "python -X utf8 C:/work/algebraic-filter/hooks/posttool_af_check.py"
      }]
    }]
  }
}
```

Python (both Windows and Unix) accepts forward slashes, avoiding the bash escape issue.

### Reproducibility test

```bash
# Backslash version (broken)
bash -c 'python -X utf8 C:\\work\\algebraic-filter\\hooks\\posttool_af_check.py < /dev/null'
# → "can't open file '...workalgebraic-filterhooksposttool_af_check.py'"

# Forward-slash version (working)
bash -c 'python -X utf8 C:/work/algebraic-filter/hooks/posttool_af_check.py < /dev/null'
# → EXIT=0
```

### Lesson learned

My subprocess tests (direct python invocation) did not trigger path mangling, leading me to articulate "hook operation verified PASS." The mangling only emerged when the hook was invoked via Claude Code session shell. The gap was first exposed by chai's end-to-end attempt. Articulation reflection: a shell-invocation reproducibility test was missing throughout the AF project period.

---

## 2. Scalpel (python-scalpel) Python 3.13 build failure

### Symptom

```bash
pip install python-scalpel
# → error: failed-wheel-build-for-install
# → typed-ast wheel build failure
```

### Cause

The `typed-ast` package was needed for Python ≤3.8 as a separate AST. In Python ≥3.9, the built-in `ast` module provides equivalent functionality → `typed-ast` is obsolete (maintenance halted).
python-scalpel pins this old typed-ast → cannot build on Python 3.13.

### Countermeasure: Isolated env via Docker (Python 3.10)

[Dockerfile.scalpel](../Dockerfile.scalpel):

```dockerfile
FROM python:3.10-slim
WORKDIR /workspace
RUN pip install --no-cache-dir python-scalpel
COPY af_phase3_scalpel /workspace/af_phase3_scalpel
CMD ["python", "-c", "from scalpel.cfg import CFGBuilder; print('OK')"]
```

Build:
```bash
docker build -t af-scalpel -f Dockerfile.scalpel .
```

Bridge from main env (Python 3.13) via [af_phase3/scalpel_bridge.py](../af_phase3/scalpel_bridge.py):

```python
from af_phase3.scalpel_bridge import analyze_cfg
result = analyze_cfg("samples/violations/intermediate_list_chain.py")
# → {function_count: 1, function_cfgs: [{function_name: [1, 'transform'], ...}], ...}
```

### Alternative path (in-house AST extension)

Without Scalpel integration, an alternative is to extend [af_phase3/static_checker.py](../af_phase3/static_checker.py) with AF-original AST visitor. The cross-function data-flow / alias-analysis niche can be pursued through in-house implementation.

---

## 3. memray Windows-native non-support

### Symptom

```bash
pip install memray
# → Successfully installed memray-X.Y.Z
python -m memray --version
# → ModuleNotFoundError: No module named 'memray'
```

### Cause

memray is implemented as a C extension (native binding) and officially supports only Linux/macOS (per Bloomberg's README). On Windows, `pip install` succeeds but the native portion isn't built, so import fails.

### Countermeasure: tracemalloc (stdlib) alternative

[af_phase3/runtime_checker.py](../af_phase3/runtime_checker.py) uses tracemalloc:

```python
import tracemalloc

tracemalloc.start()
snap_before = tracemalloc.take_snapshot()
func(*args)
snap_after = tracemalloc.take_snapshot()
diff = snap_after.compare_to(snap_before, "lineno")
```

tracemalloc is in Python stdlib = works on both Windows and Unix. However, memray-class native sampling is not available; only simple line-level allocation tracking.

### Using memray on Linux/macOS

There is room to switch `af_phase3/runtime_checker.py` to memray (separate module or extension flag). Reserved as a Phase 3 further-extension niche.

---

## 4. Hook session-reload not supported

### Symptom

Even if you edit and save `.claude/settings.local.json` during a Claude Code session, the **active session's hook configuration is the one loaded at session start**.

### Cause

Claude Code loads settings at session start → keeps them thereafter. No API exists to reload settings within a session (as of 2026-05).

### Countermeasure: Start a new session

```powershell
# Terminate existing session (chai exits Claude Code)
# Open a new terminal and start a new session
cd /path/to/project
claude
```

This loads the forward-slash-fixed settings.

### When switching hook OFF/ON for A/B measurement

Each round requires a separate session start:
- Round 1 (OFF): Rename settings → new session
- Round 2 (ON): Restore settings → new session

Details: [docs/_ab_measurement/protocol.md](_ab_measurement/protocol.md)

---

## 5. auto-mode classifier blocks nested sessions

### Symptom

When an AI agent (parent Claude session) tries to start a nested session with `claude --print --permission-mode bypassPermissions`:

```
Permission for this action was denied by the Claude Code auto mode classifier.
Reason: Spawning a nested Claude Code session with --permission-mode bypassPermissions
creates an unsupervised autonomous agent loop; the user said "OK" to running a sub-session
but did not explicitly authorize bypassing permission gates.
```

### Cause

The auto-mode classifier identifies an **autonomous loop** (nested session bypassing all permission gates) as a high-risk action and blocks it without explicit user authorization (legitimate guardrail).

### Countermeasure 1: Explicit chai authorization

Have chai articulate "OK to bypass permissions in nested sessions" → retry passes the classifier.

### Countermeasure 2: Safer path with `--allowedTools`

Instead of permission bypass, explicitly allow only required tools:

```bash
claude --print --allowedTools "Write,Edit,Read"  # Bash excluded
```

But including Bash gets blocked again:
> Spawning a nested non-interactive Claude session with --allowedTools including Bash creates an autonomous agent loop

→ Write/Edit/Read only works (hook startup uses Claude Code's internal subprocess, not the Bash tool).

### Countermeasure 3: Pass prompt via stdin

argparse parser variadic-argument quirk: the prompt after `--allowedTools "tool1,tool2"` is consumed as an argument:

```bash
# Fails ("Input must be provided either through stdin or as a prompt argument")
claude --print --allowedTools "Write,Edit,Read" "prompt content"

# Works (via stdin)
echo "prompt content" | claude --print --allowedTools "Write,Edit,Read"
```

### Nested-session use case

[scripts/ab_automation.py](../scripts/ab_automation.py) + [scripts/ab_automation_wide.py](../scripts/ab_automation_wide.py) start nested sessions multiple times via `--allowedTools "Write,Edit,Read"` + stdin prompts, automating A/B measurement.

---

## Other minor issues

### cp932 encoding (Windows Console default)

When a Python script's print() emits Unicode characters (`✓` / `⊘` / `≥`):
```
UnicodeEncodeError: 'cp932' codec can't encode character '✓'
```

Countermeasures:
- Force UTF-8 with `python -X utf8 script.py`
- Replace with ASCII (`[OK]` / `[NG]` / `[SKIP]`)
- Explicitly pass `encoding="utf-8", errors="replace"` to subprocess.run()

### CLAUDE_CMD path (calling claude CLI from scripts)

`subprocess.run(["claude", ...])` fails to resolve `.cmd` extension on Windows:
```
FileNotFoundError: [WinError 2] The system cannot find the file specified
```

Countermeasure: Specify absolute path (landed in [scripts/ab_automation*.py](../scripts/)):
```python
CLAUDE_CMD = r"C:\Users\user\AppData\Roaming\npm\claude.cmd"
subprocess.run([CLAUDE_CMD, "--print", ...])
```

---

## See also

- [USAGE.md](../USAGE.md) — Usage guide
- [docs/architecture.md](architecture.md) — Detailed architecture
- [docs/evidence_summary.md](evidence_summary.md) — A/B measurement + Phase evidence
