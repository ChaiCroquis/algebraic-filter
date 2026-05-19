# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current status

**Documentation-only repository. No code, no build system, no tests yet.** The project is at **Phase 0 pre-registration (draft, unapproved)** — implementation is gated on Phase 0 approval per the Pre-registration Protocol described below. Do not start Phase 1 work or scaffold an implementation skeleton until [docs/algebraic_filter_phase0_pre_reg.md](docs/algebraic_filter_phase0_pre_reg.md) is approved and Phase 0 success criteria S0-1〜S0-5 are recorded as met.

## What this project is

Algebraic Filter (`af-skill`) is a Claude Code **skill + PostToolUse hook** that performs **algebraic-law-level machine verification of AI-generated code**. It is the physical-verification arm of the chai's two-layer AI delegation guardrail:

- **philosophy filter** (policy layer, established 2026-05-05): decides "machine-verifiable → AI executes / not verifiable → reject"
- **algebraic filter** (this repo, physical layer): enforces that decision at code-write time via hook exit code 2 feedback into Claude

The design choice is hook-based post-hoc verification (not constrained decoding) because CRANE (2025) showed strong decoding constraints degrade LLM reasoning. Verification deterministic → hallucination-free; LLM autonomy preserved.

## Architecture (planned)

Three-layer verification pipeline, fired by PostToolUse hook on Write/Edit:

```
Layer 1: 静的検証 (tens of ms)    — ruff PERF/SIM/FURB + custom rules
                                    purity, intermediate-data detection, classical-skeleton enforcement
Layer 2: 代数法則 PBT (seconds)   — hypothesis (auto-generated from type signatures)
                                    associativity, identity, idempotence, commutativity, Functor/Monoid laws
Layer 3: 実測 (tens of seconds)   — memray + pytest-benchmark, selective
                                    memory access, cache-miss, intermediate-object counts
```

Energy efficiency principle: cheap layer rejects first; each layer gates the next. Violations are formatted as `{違反箇所, 違反法則名, 代替骨格名, 修正例}` and injected back to Claude via `exit code 2`.

## Differentiation axes (do not blur these)

The three claims that distinguish this from existing lint/formatter/TDD-enforcement hooks — every design decision must preserve them:

1. **Algebraic-law-level PBT auto-generation** from function signatures (Monoid/Functor/Foldable laws)
2. **Data-movement empirical feedback** (memray/pytest-benchmark) — breaks the static-analysis ceiling, holds the energy axis at the operational level
3. **LLM-optimized feedback shape** — structured `{location, law, alternative skeleton, fix example}` payload that directly raises Claude's self-correction success rate

If a proposed change weakens any of these axes, flag it.

## Pre-registration Protocol (binding for Phase 0)

Phase 0 hypotheses (H1–H4), success criteria (S0-1〜S0-5), and withdrawal criteria (W0-1〜W0-5) are **frozen** in [docs/algebraic_filter_phase0_pre_reg.md](docs/algebraic_filter_phase0_pre_reg.md). The following are structurally prohibited during Phase 0:

1. Lowering numerical success thresholds
2. Raising withdrawal thresholds
3. Extending the 5-business-day Phase 0 timeline because "we're almost there"
4. Adding hypotheses H5+ inside Phase 0 (open a new pre-reg afterward)
5. Expanding tool-investigation scope beyond the listed primary tools (CrossHair / ruff / hypothesis / memray / VeCoGen)

Withdrawal is recorded as **hypothesis-verification completion**, not failure. Outcomes are binary.

Target baseline-measurement project is one of Hanga / CYBELE / LayerForge, chosen during Phase 0 Day 1.

## Phase roadmap (do not skip ahead)

| Phase | Scope | Gate |
|---|---|---|
| 0 | Pre-reg, baseline measurement, existing-tool coverage survey | This phase right now |
| 1 | Minimal hook: ruff PERF/SIM/FURB + existing hypothesis templates, A/B vs baseline | S0 all pass |
| 2 | Auto-generated algebraic-law PBT templates from type hints | Phase 1 hit success criteria |
| 3 | Data-movement static + empirical feedback | Phase 2 coverage ≥70% |
| 4 | LLM-optimized feedback formatter + anti-pattern auto-accumulation | Phase 3 success |
| 5 | OSS packaging (optional) | Phase 4 success |

## Adjacent project paths (c:/work)

All tooling and baseline-candidate projects live under `c:/work/`. Confirmed paths as of 2026-05-19:

- `c:/work/LayerForge/` — baseline candidate (v9 verification ongoing, established benchmarks available)
- `c:/work/hanga-pipeline/` — baseline candidate (Hanga; Excel template ops, high AI-generated code ratio)
- `c:/work/mulmoclaude/` — design reference (see global `design-ref` skill)
- `c:/work/anthropic-refs/`, `c:/work/anthropic-sandbox/`, `c:/work/claude-code/`, `c:/work/claude-code-best-practices/` — Anthropic-side reference material
- **CYBELE** — listed in [docs/tool_landscape.md](docs/tool_landscape.md) and [docs/algebraic_filter_phase0_pre_reg.md](docs/algebraic_filter_phase0_pre_reg.md) §5 as a baseline candidate, **but no matching directory exists under c:/work/ as of this scan**. Either the name has changed, the path is elsewhere, or the candidate has been retired. Confirm with chai before treating CYBELE as available.

## Phase 0 execution sequence (gated on pre-reg approval)

Do not run this until [docs/algebraic_filter_phase0_pre_reg.md](docs/algebraic_filter_phase0_pre_reg.md) is explicitly approved by chai (承認者欄が記入された状態).

| Day | Action | PASS evidence |
|---|---|---|
| 1 | Select baseline project from confirmed candidates (LayerForge / hanga-pipeline). Record selection in pre-reg §10 「対象モジュール」欄. | Day 1 verification block (下記) を実走、「対象モジュール」 行が空欄でないこと + 候補名 (LayerForge / hanga-pipeline) を含むこと |
| 2 | Baseline measurement: pass@1 (pytest), avg-edit-cycles (Claude Code session log), type-error rate (mypy), violation classification (manual). | Pre-reg §10 baseline result table fully populated |
| 3 | Primary-tool survey 1/2: CrossHair + ruff. Per-tool: (a) covered items vs assumed-checklist, (b) hook-integration feasibility via exit code 2, (c) overhead (time/mem), (d) license. | Pre-reg §10 ツール調査表に 2 行記入 |
| 4 | Primary-tool survey 2/2: hypothesis + memray + VeCoGen. Same 4-axis schema. | Pre-reg §10 ツール調査表に残 3 行記入 |
| 5 | Aggregate → binary judgement on H1–H4 → S0-1〜S0-5 check → Phase 1 着手 or 撤退 record. | Pre-reg §10 「最終判定」欄に成功 or 撤退理由が記入 |

W0-5 hard stop: if Day 5 has not closed, withdraw per pre-reg §4. Do not extend.

### Day 1 baseline-project 確定確認 — verification block (copy-pasteable)

```powershell
# Step 1: pre-reg §10 「対象モジュール」 行が空欄でないこと
Select-String -Path "C:\work\algebraic-filter\docs\algebraic_filter_phase0_pre_reg.md" `
  -Pattern "対象モジュール"
# 期待値: 1 行以上 hit、 かつ "LayerForge" or "hanga-pipeline" を含む行が存在する

# Step 2: 承認欄が記入済 (Phase 0 binding 承認の証跡)
Select-String -Path "C:\work\algebraic-filter\docs\algebraic_filter_phase0_pre_reg.md" `
  -Pattern "承認日"
# 期待値: "2026-MM-DD" 形式の日付 + "chai 明示承認" 文字列を含む
```

最終実行記録 2026-05-19: Step 1 hit "LayerForge (`C:\work\LayerForge\`...)" 行確認、 Step 2 hit "承認日: 2026-05-19 (chai 明示承認 — Phase 0 着手 + baseline = LayerForge を Sovereign 判断として確定)" 行確認、 Day 1 PASS。

### Day 2 baseline measurement — LayerForge verification block (copy-pasteable)

Baseline confirmed 2026-05-19: `C:\work\LayerForge\` (pytest + ruff + hypothesis available per pyproject.toml dev extras; **mypy not present** — type-check baseline substitutes ruff lint rules).

```powershell
# Step 1: install dev extras (idempotent)
cd C:\work\LayerForge
python -m pip install -e ".[dev]"
# 期待値: "Successfully installed" or "Requirement already satisfied"

# Step 2: pass@1 baseline (record N passed / N failed)
python -m pytest --tb=short -q 2>&1 | Select-Object -Last 20
# 期待値: "N passed" 行を Pre-reg §10 baseline 表「pass@1」欄に EXECUTED marker (= 実行直後の exit code + 件数) 付きで記入

# Step 3: ruff baseline violation count (PERF + SIM + FURB)
python -m ruff check --select=PERF,SIM,FURB --statistics layerforge tests
# 期待値: violation 件数を Pre-reg §10「違反インスタンス数」欄に記入。≥10 で H3 成立、<5 で W0-3 撤退

# Step 4: hypothesis-driven test count (PBT 既存カバレッジの目安)
python -m pytest --collect-only -q | Select-String "hypothesis" | Measure-Object -Line
# 期待値: hypothesis 利用 test 数。0 でも構わない (Phase 2 で自動生成テンプレ追加が前提)

# Step 5: type-check substitute (mypy 未導入のため ruff の ANN/F ルール)
python -m ruff check --select=ANN,F layerforge --statistics
# 期待値: annotation/未定義参照系の件数を「コンパイル/型エラー率」欄に substitute 記入 + 「mypy substitute」注記
```

判定基準 (Pre-reg §3 連動):
- Step 3 で違反 ≥10 件 → H3 成立 (S0-3 PASS 候補)
- Step 3 で違反 <5 件 → W0-3 (撤退) 即時 trigger、Day 5 を待たない

### Day 3-4 primary-tool survey — schema (copy-pasteable per-tool)

各ツール (CrossHair / ruff / hypothesis / memray / VeCoGen) について Pre-reg §10 ツール調査表に以下スキーマで記入。

共通 4 軸: (a) version pin / (b) カバレッジ算定の分母 (rule 数 / check 種類数) / (c) hook 統合可能性 (exit code 2 経由のフィードバック) / (d) overhead 実測 + license。

```powershell
# === ruff (Day 3) ===
python -m ruff --version
# 期待値: バージョン文字列。Pre-reg 行末に version pin

python -m ruff rule --all 2>&1 | Measure-Object -Line
# 期待値: 全ルール件数 (カバレッジ算定の分母)

# hook 統合可能性: ruff は exit code 1 を non-zero で返す → exit code 2 へ shim 必要
# overhead: ((1..10 | %{Measure-Command { python -m ruff check layerforge }}) | Measure-Object -Property TotalMilliseconds -Average).Average
# license: MIT (公式 README、要確認)
```

```powershell
# === CrossHair (Day 3) ===
python -m pip install crosshair-tool
# 期待値: Successfully installed crosshair-tool-X.Y.Z

python -m crosshair --version
# 期待値: バージョン文字列。Pre-reg に version pin

python -m crosshair check --help 2>&1 | Select-Object -First 30
# 期待値: check / watch / diffbehavior 等のサブコマンド一覧。カバレッジ算定の分母 = サポート contract 種類

# サンプル動作確認: LayerForge の pure 関数 1 つに対し
cd C:\work\LayerForge
python -m crosshair check layerforge/inference --analysis-kind=PEP316 2>&1 | Select-Object -First 50
# 期待値: counter-example 検出 or "Counterexample not found" を articulate。 hook 統合可能性 = exit code が違反時 non-zero か確認

# overhead: Measure-Command { python -m crosshair check layerforge/inference --per-condition-timeout=5 }
# license: MIT (PyPI ページ、要確認)
```

```powershell
# === hypothesis (Day 4) ===
# 既に LayerForge dev extras 経由で installed
python -c "import hypothesis; print(hypothesis.__version__)"
# 期待値: バージョン文字列

python -c "from hypothesis import strategies as st; print([n for n in dir(st) if not n.startswith('_')][:20])"
# 期待値: strategy 関数一覧 (integers, lists, text, ...)。カバレッジ算定の分母 = strategy 種類数

# hook 統合可能性: hypothesis 自体は pytest plugin として動作 → hook では pytest 経由で起動
# サンプル動作: 一時的 PBT を作成して @given で実行
python -c "from hypothesis import given, strategies as st; from hypothesis.errors import HypothesisException; given(st.lists(st.integers()))(lambda xs: sum(xs) == sum(reversed(xs)))()"
# 期待値: AssertionError 等を起こさず通過 (= 結合律相当の sanity check)

# overhead: pytest の hypothesis 利用 test 1 件あたりの実行時間を Day 2 pytest 結果から逆算
# license: MPL-2.0 (公式 README、要確認)
```

```powershell
# === memray (Day 4) ===
python -m pip install memray
# 期待値: Successfully installed memray-X.Y.Z (注: Windows ネイティブ非対応の可能性、 WSL/Linux 環境 fallback の articulate)

python -m memray --version
# 期待値: バージョン文字列、 または Windows で動作不可なら articulate

# Windows 不可の場合の代替: tracemalloc (stdlib) で中間オブジェクト計測の articulate
python -c "import tracemalloc; print('tracemalloc available')"
# 期待値: "tracemalloc available" (stdlib なので必ず PASS)

# hook 統合可能性: memray run <script> → memray stats output → exit code 2 shim
# overhead: サンプリングモード (--native でなければ) で 10-30% target
# license: Apache-2.0 (公式 README、要確認)
```

```powershell
# === VeCoGen (Day 4) ===
# VeCoGen は LLM + Frama-C 統合の **参考実装** (C 対象、 Python 直接適用なし)
# Day 4 では install せず、 リポジトリ README + paper を読んで 4 軸を文献調査として埋める

# 公式リポジトリ: https://github.com/VeCoGen/VeCoGen (要確認、 URL 検証必須)
# カバレッジ: Frama-C ACSL 注釈に対する LLM 補完 (C のみ)
# hook 統合可能性: AF とは独立、 設計参考としての articulate のみ
# overhead: N/A (Python skill 層に直接組み込まない)
# license: 公開リポジトリ確認時に articulate
# 差別化軸への影響: H2 検証 (= Python + Claude Code skill+hook の統合 niche が独立か) の input
```

H1 判定 (S0-1): 全 5 ツールの「想定検証項目との重複率」を集計し ≥70% で H1 成立。<50% で W0-1 全体撤退。

H2 判定 (S0-2): VeCoGen を含む先行実装が Python skill+hook 層を統合カバーしていれば不成立 → 差別化軸見直し / 撤退。 Python + Claude Code skill 統合は独立 niche として残存する見込み (要 Day 4 確認)。

### Day 2 完了状態 (2026-05-19) + Phase 1 scope 解像度 (chai 整理反映)

Day 2 snapshot baseline は **「チェッカー本体が機能している」 目的達成 evidence** として完了 marker landed:
- pass@1 = 158/193 = 81.9% / ruff PERF+SIM+FURB = 12 件 / ruff ANN+F (mypy substitute) = 47 件 / hypothesis 利用 = 0 件
- 適用 niche: H1 既存ツールカバレッジ調査の入力 / Phase 1 サンプル違反 pattern 選定根拠 / Phase 2 PBT 自動生成の open space 確認

**自動修正サイクルの目的達成 evidence は Day 2 では取得せず、 Phase 1 サンプル A/B プロトコルが独自 contribution として取得する**:

| 計測対象 | 取得 Phase | 使える場面 |
|---|---|---|
| 既存ツールが違反を検出できる事実 (snapshot) | Day 2 完了 | チェッカー機能 baseline |
| 自動修正サイクルの効果差分 (hook OFF vs hook ON) | Phase 1 サンプル A/B | AF 自動修正機能の効果立証 |
| 実プロジェクト一般化 | Phase 5 OSS 公開 | 他プロジェクト試適用 |
| 偽陽性率の完全検証 | Phase 4 と連動 | LLM最適化フィードバック整形 |

Phase 1 着手時の scope (project_plan §6 解像度上げ反映 + 整合完全化 2026-05-19):
- **前半 3 日 (両軸併記)**:
  - 軸 1: Phase 0 mini-prototype 7 pattern (`samples/violations/` 配下、 #1 perf401 / #2 sim103 / #3 sim300 / #4 ann001 / #5 monoid_associativity / #6 intermediate_list_chain / #7 purity) を各 3〜5 variation で拡張
  - 軸 2: [manifest.json](samples/violations/manifest.json) `planned_additions_phase_1` 7 カテゴリ (Functor 則 / Foldable / Monad 則 / 可換律 / 冪等性 / Stream Fusion / 純粋性 variants / 型注釈 variants) を各 3〜5 variation で追加
  - 合計目標: 30〜50 件 (chai 指示「大量に用意していい」 反映)
  - 各 sample に対応する `samples/violations/fixed/<id>.py` = 期待修正後コード (ground truth) を併設
- **後半 4 日**: PostToolUse hook 実装 (ruff PERF/SIM/FURB/ANN/F + hypothesis + tracemalloc) + hook OFF/ON A/B 計測 → 修正サイクル数 / 最終生存違反数 / 修正成功率 (= ground truth との diff 一致率) / 副作用検出

### TDD 3 層 articulate (chai 指示「テスト先に大量に用意して TDD として使用」 2026-05-19 反映)

AF プロジェクトは仕様 → テスト → 実装の TDD 3 層構造で運用:

| 層 | 配置 | 役割 |
|---|---|---|
| **仕様層** | [samples/violations/manifest.json](samples/violations/manifest.json) | 各 sample の `expected_detection` (tool / rule / command / exit / marker) + `what_to_verify` + `what_is_the_problem` + `expected_fix` (skeleton / code / feedback_payload_template) |
| **テスト層** | [samples/violations/tests/test_manifest_driven.py](samples/violations/tests/test_manifest_driven.py) | manifest 駆動 pytest parametrize で test-first (Phase 0 で 12 tests PASS landed) |
| **Ground truth 層** | `samples/violations/fixed/` | 各 sample の修正後コード = AF hook 経由の Claude 自己修正が到達すべき形 |
| **実装層** | AF hook (Phase 1) | PostToolUse で違反検出 → exit code 2 → Claude フィードバック、 Phase 1 planned tests を GREEN 化 |

実行: `cd algebraic-filter && python -m pytest samples/violations/tests/test_manifest_driven.py -v`

**TDD growth property**: manifest.json `samples` array に新 entry を追加 → pytest parametrize で自動的にテスト増加 = chai 指示「大量」 への継続的拡張 path。 Phase 1 着手で 30〜50 件まで拡充時、 テストも自動的に 60〜100 tests 規模に増加 (各 sample に対し ruff_detects_unfixed + ruff_no_violation_fixed の 2 tests parametrize)。

## Key documents

- [docs/algebraic_filter_project_plan.md](docs/algebraic_filter_project_plan.md) — full plan, scope IN/OUT, withdrawal criteria per phase
- [docs/algebraic_filter_phase0_pre_reg.md](docs/algebraic_filter_phase0_pre_reg.md) — binding Phase 0 pre-registration
- [docs/algebraic_filter_related_work.md](docs/algebraic_filter_related_work.md) — adjacent-research map + reason for hook-over-decoding
- [docs/tool_landscape.md](docs/tool_landscape.md) — tool catalog and project×tool matrix (draft, may contain errors per its own disclaimer)
- `docs/AIエージェントアーキテクチャ調査報告.pdf` — AET-OS architecture reference (Verified Orchestrator Pattern; AF is its Layer 3 / Verification Layer)

## Scope guardrails (from project plan §4)

OUT of initial scope — do not propose these as additions:
- New LLM training / fine-tuning
- Custom constrained-decoding implementation
- Languages other than Python / TypeScript / Rust
- IDE plugin packaging (hook layer is sufficient)
