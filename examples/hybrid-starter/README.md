# Hybrid starter — base quality tool + algebraic-filter (+α)

A ready-to-copy project skeleton for trying the **claude-code-quality-hook (base)
+ algebraic-filter (+α)** hybrid. See [docs/hybrid_setup.md](../../docs/hybrid_setup.md)
for the full explanation.

ベース品質ツール + algebraic-filter (+α) の hybrid を試すための雛型。 詳細は
[docs/hybrid_setup.ja.md](../../docs/hybrid_setup.ja.md)。

---

## Quick start (Windows / PowerShell)

```powershell
# 1. Copy this folder somewhere outside the AF repo, then cd into it
Copy-Item -Recurse <path-to>\algebraic-filter\examples\hybrid-starter C:\work\my-hybrid
cd C:\work\my-hybrid

# 2. Run the setup helper (creates .venv, installs ruff/hypothesis/pyright into
#    it — NO global install — clones the base, wires .claude/settings.json)
.\setup_hybrid.ps1

# 3. Activate the venv, then start Claude Code FROM the activated shell
#    (both hooks call bare `python`, so they inherit the venv deps this way)
.\.venv\Scripts\Activate.ps1
claude

# 4. Inside the session, install the +α plugin (this project only):
#    /plugin marketplace add ChaiCroquis/algebraic-filter
#    /plugin install algebraic-filter@algebraic-filter-marketplace --scope local

# 5. Exit and restart `claude` so both hooks register at session start.

# 6. Ask Claude to edit scratch/try_me.py — both hooks fire:
#    base (pyright) catches the type error, AF catches the algebraic-law violation.
```

macOS / Linux: use `setup_hybrid.sh` instead of the `.ps1` (steps 3-6 identical).

---

## What's in here

| File | Role |
|---|---|
| `setup_hybrid.ps1` / `.sh` | Creates `.venv` + installs `ruff`/`hypothesis`/`pyright` into it (**no global install**; pyright via pip), clones claude-code-quality-hook, writes `.claude/settings.json` (base hook, `-X utf8` for Windows) + base `.quality-hook.json` (detection-only) |
| `.algebraic-filter.json` | AF config — safe defaults (`phase2_runtime: false`). Flip to `true` to enable algebraic-law runtime checking (executes the file; trusted dirs only) |
| `scratch/try_me.py` | A sample file with **a type error + a monoid-law violation** so you can see both hooks fire immediately |
| `.gitignore` | Ignores the cloned base + AF history |

## AF-only (skip the base)

Don't need type-checking? Skip `setup_hybrid` and just do steps 3-6 (install the
AF plugin, restart, edit). Add the base later if you want pyright too — staged
adoption works fine.

base が要らなければ `setup_hybrid` を飛ばして step 3-6 だけ (= AF plugin install
→ 再起動 → 編集) で AF 単体を試せます。 後から base を足す段階導入も可。
