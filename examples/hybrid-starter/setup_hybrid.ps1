# Hybrid starter setup (Windows / PowerShell)
#
# Auto-selects the mode (chai's "Docker if available, else normal"):
#   - Docker present  -> Docker mode: builds the af-hybrid image (AF +alpha +
#     pyright base, all in-container) and wires .claude/settings.json to it.
#     ZERO host deps (no python/node/pip on host); no plugin install needed.
#   - No Docker       -> venv mode: creates .venv, installs ruff/hypothesis/
#     pyright into it (no global install), clones the base, wires the base hook.
#     The +alpha (algebraic-filter) is added as a plugin inside the session.
#
# Force venv even when Docker exists:  .\setup_hybrid.ps1 -Venv
# Run from inside your copied starter project.
param([switch]$Venv)

$ErrorActionPreference = "Stop"
$proj = (Get-Location).Path

$hasDocker = $false
if (-not $Venv) {
    try { docker --version *> $null; $hasDocker = ($LASTEXITCODE -eq 0) } catch { $hasDocker = $false }
}

if ($hasDocker) {
    Write-Host "== Docker detected -> Docker mode (zero host deps) ==" -ForegroundColor Cyan

    Write-Host "== 1/2 build af-hybrid image (AF +alpha + pyright base) =="
    docker build -t af-hybrid "$proj\docker"

    Write-Host "== 2/2 wire container hook into .claude/settings.json =="
    New-Item -ItemType Directory -Force "$proj\.claude" | Out-Null
    # -v needs a Windows path; AF_HOST_PROJECT lets the container map host->/work
    $cmd = "docker run -i --rm -v `"$proj`:/work`" -e AF_HOST_PROJECT=`"$proj`" -e AF_HOOK_PHASE2_PBT=1 af-hybrid"
    $settings = @{
        hooks = @{
            PostToolUse = @(
                @{ matcher = "Write|Edit|MultiEdit"; hooks = @(@{ type = "command"; command = $cmd }) }
            )
        }
    }
    $settings | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 "$proj\.claude\settings.json"

    Write-Host ""
    Write-Host "Docker hybrid wired. Next:" -ForegroundColor Green
    Write-Host "  1. claude        (the container hook runs AF +alpha + pyright on each .py edit)"
    Write-Host "  2. ask Claude to fix scratch/try_me.py -> both layers fire from the container"
    Write-Host ""
    Write-Host "No venv / plugin install needed in Docker mode — everything is in the image."
    return
}

Write-Host "== No Docker -> venv mode (no global install) ==" -ForegroundColor Cyan

Write-Host "== 1/4 clone base (claude-code-quality-hook) =="
if (-not (Test-Path "$proj\claude-code-quality-hook")) {
    git clone --depth 1 https://github.com/dhofheinz/claude-code-quality-hook
} else {
    Write-Host "  already present, skipping"
}

Write-Host "== 2/4 venv + deps (ruff / hypothesis / pyright) — no global install =="
if (-not (Test-Path "$proj\.venv")) { python -m venv .venv }
& "$proj\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$proj\.venv\Scripts\python.exe" -m pip install ruff hypothesis pyright

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
Write-Host "Base wired (venv mode). Next:" -ForegroundColor Green
Write-Host "  1. Activate the venv IN THIS SHELL (so hooks inherit its python/ruff/pyright):"
Write-Host "       .\.venv\Scripts\Activate.ps1"
Write-Host "  2. Launch Claude Code FROM the activated shell:"
Write-Host "       claude"
Write-Host "  3. /plugin marketplace add ChaiCroquis/algebraic-filter"
Write-Host "  4. /plugin install algebraic-filter@algebraic-filter-marketplace --scope local"
Write-Host "  5. exit, then re-launch 'claude' from the activated venv (hooks register at start)"
Write-Host "  6. ask Claude to fix scratch/try_me.py -> both hooks fire"
Write-Host ""
Write-Host "Why activate first: both hooks call bare 'python' — running claude from the"
Write-Host "activated venv makes them use the venv deps (no global install needed)."
Write-Host ""
Write-Host "Tip: keep PYTHONUTF8=1 set (the base crashes on cp932 otherwise):"
Write-Host "  setx PYTHONUTF8 1   (new shells); or `$env:PYTHONUTF8='1' for this shell"
