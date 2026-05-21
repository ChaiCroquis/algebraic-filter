#!/usr/bin/env bash
# Hybrid starter setup (macOS / Linux)
#
# Auto-selects the mode (chai's "Docker if available, else normal"):
#   - Docker present  -> Docker mode: builds the af-hybrid image (AF +alpha +
#     pyright base, all in-container) and wires .claude/settings.json to it.
#     ZERO host deps; no plugin install needed.
#   - No Docker       -> venv mode: .venv + pip (no global install), clone base,
#     wire base hook; add the +alpha plugin inside the session.
#
# Force venv even when Docker exists:  ./setup_hybrid.sh --venv
set -euo pipefail
proj="$(pwd)"

force_venv=0
[ "${1:-}" = "--venv" ] && force_venv=1

has_docker=0
if [ "$force_venv" -eq 0 ] && command -v docker >/dev/null 2>&1; then
    has_docker=1
fi

if [ "$has_docker" -eq 1 ]; then
    echo "== Docker detected -> Docker mode (zero host deps) =="

    echo "== 1/2 build af-hybrid image (AF +alpha + pyright base) =="
    docker build -t af-hybrid "$proj/docker"

    echo "== 2/2 wire container hook into .claude/settings.json =="
    mkdir -p "$proj/.claude"
    cat > "$proj/.claude/settings.json" <<JSON
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          { "type": "command", "command": "docker run -i --rm -v \"$proj:/work\" -e AF_HOST_PROJECT=\"$proj\" -e AF_HOOK_PHASE2_PBT=1 af-hybrid" }
        ]
      }
    ]
  }
}
JSON

    cat <<'NEXT'

Docker hybrid wired. Next:
  1. claude        (the container hook runs AF +alpha + pyright on each .py edit)
  2. ask Claude to fix scratch/try_me.py -> both layers fire from the container

No venv / plugin install needed in Docker mode — everything is in the image.
NEXT
    exit 0
fi

echo "== No Docker -> venv mode (no global install) =="

echo "== 1/4 clone base (claude-code-quality-hook) =="
if [ ! -d "$proj/claude-code-quality-hook" ]; then
    git clone --depth 1 https://github.com/dhofheinz/claude-code-quality-hook
else
    echo "  already present, skipping"
fi

echo "== 2/4 venv + deps (ruff / hypothesis / pyright) — no global install =="
[ -d "$proj/.venv" ] || python -m venv .venv
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

Base wired (venv mode). Next:
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
