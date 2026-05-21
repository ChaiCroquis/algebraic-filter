# Hybrid starter setup (Windows / PowerShell)
# Clones the base (claude-code-quality-hook), installs deps, and wires
# .claude/settings.json so the base hook fires. The +alpha (algebraic-filter)
# is installed separately as a plugin inside a Claude Code session.
#
# Run from inside your copied starter project:  .\setup_hybrid.ps1

$ErrorActionPreference = "Stop"
$proj = (Get-Location).Path

Write-Host "== 1/4 clone base (claude-code-quality-hook) =="
if (-not (Test-Path "$proj\claude-code-quality-hook")) {
    git clone --depth 1 https://github.com/dhofheinz/claude-code-quality-hook
} else {
    Write-Host "  already present, skipping"
}

Write-Host "== 2/4 install deps (ruff / hypothesis / pyright) =="
python -m pip install ruff hypothesis
npm install -g pyright

Write-Host "== 3/4 base config: detection + block only (AI-fix off) =="
$qcfg = @{
    type_checking = @{ enabled = $true }
    auto_fix      = @{ enabled = $true }
    claude_code   = @{ enabled = $false }   # off: avoids nested-agent AI stage (not Windows-ready)
    logging       = @{ enabled = $true; level = "WARNING" }
}
$qcfg | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 "$proj\.quality-hook.json"

Write-Host "== 4/4 wire base hook into .claude/settings.json =="
New-Item -ItemType Directory -Force "$proj\.claude" | Out-Null
# Forward slashes in the hook command (Windows: backslash gets escape-stripped by bash)
$hookPath = ("$proj\claude-code-quality-hook\quality-hook.py") -replace '\\','/'
$settings = @{
    hooks = @{
        PostToolUse = @(
            @{
                matcher = "Write|Edit|MultiEdit"
                hooks   = @(
                    @{ type = "command"; command = "python -X utf8 `"$hookPath`"" }
                )
            }
        )
    }
}
$settings | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 "$proj\.claude\settings.json"

Write-Host ""
Write-Host "Base wired. Next (inside a Claude Code session in this folder):" -ForegroundColor Green
Write-Host "  1. claude"
Write-Host "  2. /plugin marketplace add ChaiCroquis/algebraic-filter"
Write-Host "  3. /plugin install algebraic-filter@algebraic-filter-marketplace --scope local"
Write-Host "  4. exit, then restart 'claude' (hooks register at session start)"
Write-Host "  5. ask Claude to fix scratch/try_me.py -> both hooks fire"
Write-Host ""
Write-Host "Tip: keep PYTHONUTF8=1 set (the base crashes on cp932 otherwise):"
Write-Host "  setx PYTHONUTF8 1   (new shells); or `$env:PYTHONUTF8='1' for this shell"
