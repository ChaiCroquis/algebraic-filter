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

echo "== 2/4 install deps (ruff / hypothesis / pyright) =="
python -m pip install ruff hypothesis
npm install -g pyright

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

Base wired. Next (inside a Claude Code session in this folder):
  1. claude
  2. /plugin marketplace add ChaiCroquis/algebraic-filter
  3. /plugin install algebraic-filter@algebraic-filter-marketplace --scope local
  4. exit, then restart 'claude' (hooks register at session start)
  5. ask Claude to fix scratch/try_me.py -> both hooks fire
NEXT
