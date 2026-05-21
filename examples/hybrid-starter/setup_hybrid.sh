#!/usr/bin/env bash
# Hybrid starter setup (macOS / Linux)
# Clones the base (claude-code-quality-hook), installs deps, and wires
# .claude/settings.json so the base hook fires. The +alpha (algebraic-filter)
# is installed separately as a plugin inside a Claude Code session.
#
# Run from inside your copied starter project:  ./setup_hybrid.sh
set -euo pipefail
proj="$(pwd)"

echo "== 1/4 clone base (claude-code-quality-hook) =="
if [ ! -d "$proj/claude-code-quality-hook" ]; then
    git clone --depth 1 https://github.com/dhofheinz/claude-code-quality-hook
else
    echo "  already present, skipping"
fi

echo "== 2/4 venv + deps (ruff / hypothesis / pyright) — no global install =="
[ -d "$proj/.venv" ] || python -m venv .venv
# install into the venv directly (pyright via pip = no global npm pollution)
"$proj/.venv/bin/python" -m pip install --upgrade pip
"$proj/.venv/bin/python" -m pip install ruff hypothesis pyright

echo "== 3/4 base config: detection + block only (AI-fix off) =="
cat > "$proj/.quality-hook.json" <<'JSON'
{
  "type_checking": { "enabled": true },
  "auto_fix": { "enabled": true },
  "claude_code": { "enabled": false },
  "logging": { "enabled": true, "level": "WARNING" }
}
JSON

echo "== 4/4 wire base hook into .claude/settings.json =="
mkdir -p "$proj/.claude"
cat > "$proj/.claude/settings.json" <<JSON
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          { "type": "command", "command": "python -X utf8 \"$proj/claude-code-quality-hook/quality-hook.py\"" }
        ]
      }
    ]
  }
}
JSON

cat <<'NEXT'

Base wired. Next:
  1. Activate the venv IN THIS SHELL (so hooks inherit its python/ruff/pyright):
       source .venv/bin/activate
  2. Launch Claude Code FROM the activated shell:
       claude
  3. /plugin marketplace add ChaiCroquis/algebraic-filter
  4. /plugin install algebraic-filter@algebraic-filter-marketplace --scope local
  5. exit, then re-launch 'claude' from the activated venv (hooks register at start)
  6. ask Claude to fix scratch/try_me.py -> both hooks fire

Why activate first: both hooks call bare 'python' — running claude from the
activated venv makes them use the venv deps (no global install needed).
NEXT
