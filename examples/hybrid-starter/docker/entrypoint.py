"""Containerized hybrid PostToolUse hook: AF (+α) + pyright (base type-check).

Runs inside the af-hybrid image. Reads a Claude Code PostToolUse event from
stdin, translates the HOST file path to the mounted container path (/work/...),
runs the AF hook (algebraic-law / data-movement) and pyright (type-check), and
returns a unified PostToolUse response (exit 2 + additionalContext on violation).

Host->container path translation uses AF_HOST_PROJECT (the host project root
that is bind-mounted at /work).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

AF_HOOK = "/af/hooks/posttool_af_check.py"


def _norm(p: str) -> str:
    return p.replace("\\", "/").rstrip("/")


def _to_container_path(host_file: str) -> str:
    """Map a host absolute path to /work/<relative> using AF_HOST_PROJECT."""
    host_proj = _norm(os.environ.get("AF_HOST_PROJECT", ""))
    f = _norm(host_file)
    if host_proj and f.lower().startswith(host_proj.lower()):
        rel = f[len(host_proj):].lstrip("/")
    else:
        rel = os.path.basename(f)
    return "/work/" + rel


def _run_af(container_path: str, tool_name: str) -> str:
    """Run the AF hook in-container; return its additionalContext if it blocked."""
    event = json.dumps(
        {"tool_name": tool_name, "tool_input": {"file_path": container_path}}
    )
    r = subprocess.run(
        [sys.executable, "-X", "utf8", AF_HOOK],
        input=event,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 2 or not r.stdout.strip():
        return ""
    try:
        return json.loads(r.stdout.strip().splitlines()[-1]).get("additionalContext", "")
    except (json.JSONDecodeError, IndexError):
        return r.stdout.strip()


def _run_pyright(container_path: str) -> str:
    """Run pyright (base type-check); return a feedback block if it found issues."""
    r = subprocess.run(
        ["pyright", "--outputjson", container_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        diags = [
            d
            for d in json.loads(r.stdout).get("generalDiagnostics", [])
            if d.get("severity") in ("error", "warning")
        ]
    except json.JSONDecodeError:
        return ""
    if not diags:
        return ""
    lines = ["## base (pyright) type-check"]
    lines.extend(
        f"- {d.get('rule', 'type')} at line "
        f"{d.get('range', {}).get('start', {}).get('line', '?')}: "
        f"{d.get('message', '')[:120]}"
        for d in diags[:10]
    )
    return "\n".join(lines)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    tool_name = event.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return 0
    host_file = event.get("tool_input", {}).get("file_path", "")
    if not host_file.endswith(".py"):
        return 0

    container_path = _to_container_path(host_file)
    if not os.path.exists(container_path):
        return 0

    blocks = [b for b in (_run_af(container_path, tool_name), _run_pyright(container_path)) if b]
    if not blocks:
        return 0

    print(
        json.dumps(
            {
                "decision": "block",
                "reason": "hybrid (AF +α + pyright base) detected violations",
                "additionalContext": "\n\n".join(blocks),
            },
            ensure_ascii=False,
        )
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
