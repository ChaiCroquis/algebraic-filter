# algebraic-filter

**AI生成コードに対する代数法則レベルの機械検証ガードレール** — Claude Code skill + PostToolUse hook で AI が書いた Python コードを **書き込み時点で自動検証 → 違反時に自己修正サイクルを起動**。

[English README](README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ChaiCroquis/algebraic-filter/actions/workflows/ci.yml/badge.svg)](https://github.com/ChaiCroquis/algebraic-filter/actions/workflows/ci.yml)

## 概要

AI 生成コードには `pass@1` 評価では見えない代数構造レベルの欠陥 (= 純粋性違反 / 結合律破綻 / データ移動量過剰 / etc.) が大量に潜在する。 algebraic-filter (AF) は Claude Code の **PostToolUse hook** で Write/Edit を後段検証し、 違反時に `exit code 2 + 構造化 feedback` で Claude に **自己修正サイクル** を起動する。

### 設計哲学

- **constrained decoding ではなく hook 方式**: CRANE (2025) が示した「強い decoding 制約 = LLM 推論能力低下」 trade-off を回避。 生成後検証で LLM の自由度を維持しつつ、 検証は決定論 (= hallucination ゼロ)。
- **二層構造**: philosophy filter (= 方針層、 「機械検証可能 → AI実行 / 不可 → 却下」) + algebraic-filter (= 物理層、 hook 経由で違反コードを block + feedback) の補完設計。
- **AET-OS Verified Orchestrator Pattern Layer 3** の Python skill+hook 層 具体実装 (= 検証層が実行層から独立 + 拒否権を持つ)。

### 3 層検証パイプライン

```
Claude Code が Write/Edit
        ↓
PostToolUse hook 発火
        ↓
Layer 1 静的 (数十 ms): ruff PERF/SIM/FURB/ANN/F + AF 独自 AST rule
Layer 2 代数法則 PBT (数秒): hypothesis @given (関数シグネチャから自動生成)
Layer 3 データ移動 (数十秒): tracemalloc / memray + 閾値判定
        ↓
違反検出 → exit code 2 + 構造化 feedback → Claude 自己修正
```

## 動作 evidence (= Phase 1 撤退判定 ポイント 1 クリア)

A/B 計測自動実走 (= `claude --print` nested session 経由) で取得した evidence:

| 評価 niche | hook OFF 完成度 | hook ON 完成度 | delta |
|---|---|---|---|
| **AI 生成 raw コード** (= 型注釈なし、 5 sample) | 20% | 100% | **+80%** |
| **整理済みコード** (= 型注釈完備、 12 sample) | 91.7% | 100% | +8.3% |

Phase 1 撤退判定基準 (pass@1 +5% 改善) を両 niche でクリア = AF 有効性立証。

## このツールはあなたの状況に合うか? (適用域マトリクス)

AF は Claude Code hook 生態系の中で specialized niche を占めます。 honest scope articulate で、 利用者状況に応じた選択肢を提示します:

| 利用者の状況 | 推奨ツール |
|---|---|
| Layer 1 (ruff PERF/SIM/FURB/ANN/F lint hook) だけ欲しい、 多言語 (Python / JS / TS / Go / Rust) 対応 | [claude-code-quality-hook](https://github.com/dhofheinz/claude-code-quality-hook) — Layer 1 専業 + 3 段 auto-fix pipeline |
| Layer 1 **+ 代数法則 PBT 自動生成 (Layer 2) + データ移動量 feedback (Layer 3)** を Python で統合運用したい | **algebraic-filter** (= 本 repo) |
| 汎用 auto-format / test-runner / traceback 圧縮 hook | [claude-tools](https://github.com/tarekziade/claude-tools)、 [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery)、 または公式 [hooks guide](https://code.claude.com/docs/en/hooks-guide) |
| C / Frama-C ACSL spec が対象 | [VeCoGen](https://github.com/VeCoGen/VeCoGen) (= 独立 niche、 Python 非対象) |

AF の差別化軸は **Layer 2 (= 13 代数法則 + 関数 signature 駆動 auto-generation) + Layer 3 (= tracemalloc data-movement) + Claude Code hook 統合の combination** で、 本稿執筆時点で 公開 hook 生態系では unique。 Layer 1 のみで足りる場合は、 上記 alternative が より simple + battle-tested。

## install

```bash
pip install -e .

# Optional: Phase 3 contract demo
pip install -e ".[phase3]"

# Optional: Phase 4 strict type-check
pip install -e ".[phase4]"

# Dev (pytest)
pip install -e ".[dev]"
```

### Claude Code hook 登録

`.claude/settings.local.json` を AF プロジェクトに作成:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python -X utf8 /absolute/path/to/algebraic-filter/hooks/posttool_af_check.py"
          }
        ]
      }
    ]
  }
}
```

> **Windows ユーザー注意**: command path は **forward slash** (`/`) を使用する。 backslash (`\`) は bash 経由で escape 剥がれて path mangling を起こす。

## Quick Start

### 1. 手動 violation 検出

```bash
# Phase 1 (ruff 統合)
python -m ruff check --select=PERF,SIM,FURB,ANN,F samples/violations/perf401_manual_list_comp.py

# Phase 3 (AF 独自 AST rule)
python -c "from af_phase3.static_checker import check_file; print(check_file('samples/violations/intermediate_list_chain.py'))"

# Phase 2 (代数法則 PBT 自動生成)
python -c "
import sys; sys.path.insert(0, 'samples/violations')
from monoid_associativity_violation import my_sum
from af_phase2.generator import auto_test
print(auto_test(my_sum))
"
```

### 2. AF hook の自動連動 (= Claude Code session 内で)

Claude Code session 内で `samples/violations/_test/test_target.py` 等に違反コードを書かせると、 PostToolUse hook が:
1. Phase 1 ruff PERF/SIM/FURB/ANN/F 検出
2. Phase 3 AST 独自 rule 検出 (= intermediate list chain / dict.keys() list / etc.)
3. Phase 4 構造化 feedback (= `{violation_law, alternative_skeleton, fix_example}`) を `additionalContext` で注入
4. anti-pattern 蓄積 (= 同一違反 3 回で pre-emptive hint)

Claude が hook の structured feedback を parse して **自己修正サイクル** に入る。

### 3. A/B 計測 (= 自動実走)

```bash
# 5 task × 2 round (= 約 5 分)
python scripts/ab_automation.py

# 12 sample × 2 round (= 約 10 分、 manifest 駆動)
python scripts/ab_automation_wide.py
```

結果は `docs/_ab_measurement/log_auto_*.json` に landing。

## Architecture

### Phase 1: PostToolUse hook (= 統合 layer)
- [hooks/posttool_af_check.py](hooks/posttool_af_check.py) — Phase 1 ruff + Phase 3 AST + Phase 4 structured feedback の 3 layer 統合

### Phase 2: 代数法則 PBT 自動生成 ([af_phase2/](af_phase2/))
- `inferrer.py` — 関数シグネチャ → 法則 ID 推論 (12 keyword + 型 strategy 自動選択)
- `law_templates.py` — 13 法則テンプレ (Monoid / Functor / Foldable / Monad / Semigroup / Eq / Commutativity / Idempotence)
- `generator.py` — `auto_test()` / `auto_test_monad_pair()` / `auto_test_class_idempotence()` API

### Phase 3: データ移動量フィードバック ([af_phase3/](af_phase3/))
- `static_checker.py` — AST visitor で AF 独自 4 rule (intermediate-list-chain / dict-keys-list / explicit-copy / string-concat-in-loop)
- `runtime_checker.py` — tracemalloc 計測 + 閾値判定 + `RuntimeViolation` 構造化 payload
- `scalpel_bridge.py` — Python 3.10 Docker container 経由で Scalpel CFG 解析 (= Python 3.13 typed-ast 互換問題回避)

### Phase 4: LLM 最適化フィードバック整形 ([af_phase4/](af_phase4/))
- `feedback_formatter.py` — Phase 1 + Phase 3 violation を統一 schema (5 fields: layer / location / law / skeleton / fix_example) に整形
- `anti_pattern_tracker.py` — JSON history persistent + 同一違反 3 回で pre-emptive hint

### Sample / Test 集 ([samples/violations/](samples/violations/))
- 46 違反サンプル + 46 ground truth + [manifest.json](samples/violations/manifest.json) (= 仕様層、 各 sample の expected_detection / what_to_verify / what_is_the_problem / expected_fix を articulate)
- TDD growth: manifest entry 追加 → pytest parametrize で test 自動増加 (= 触らず増やす設計)

## Phase 0 〜 Phase 4 達成状況

| Phase | 状態 | 主成果 |
|---|---|---|
| 0 Pre-reg + baseline | ✓ closing (2026-05-19) | H1-H4 / S0-1〜S0-5 全達成、 LayerForge baseline 確定 |
| 1 PostToolUse hook | ✓ end-to-end 動作確認済 | 46 sample + 5 hook test + 4 A/B test |
| 2 代数法則 PBT 自動生成 | ✓ 深掘り完成 | 13 法則 + hypothesis-target subset 100% coverage |
| 3 データ移動量 | ✓ 拡張完成 | 4 rule AST + tracemalloc + Scalpel Docker bridge |
| 4 LLM 最適化フィードバック | ✓ integrated + A/B verified | 統一 schema (Phase 1+2+3) + history + per-rule threshold + pre-emptive hint |

## ドキュメント索引

### root 配下

| 文書 | 内容 |
|---|---|
| [USAGE.ja.md](USAGE.ja.md) | 使い方ガイド (= hook 有効化 / 手動 CLI / Phase 2 API / A/B 計測 の 4 use case) |
| [CONTRIBUTING.ja.md](CONTRIBUTING.ja.md) | 貢献ガイド (= 違反 sample 追加 3 step / 法則テンプレ拡張 / Phase 3 静的 rule 追加 / PR submission) |
| [LICENSE](LICENSE) | MIT License |

### docs/ 配下

| 文書 | 内容 |
|---|---|
| [docs/architecture.ja.md](docs/architecture.ja.md) | 詳細アーキテクチャ (= 二層構造 / 3 層検証パイプライン / AET-OS Verified Orchestrator Pattern Layer 3 mapping / Phase 0-5 構成) |
| [docs/evidence_summary.ja.md](docs/evidence_summary.ja.md) | 検証結果集約 (= A/B 計測 +80%/+8.3% / Phase 0 H1-H4 / Phase 2 hypothesis-target 100% / Phase 3 data-movement 100% / Phase 4 統一 schema / end-to-end Claude 自己修正サイクル動作 evidence) |
| [docs/troubleshooting.ja.md](docs/troubleshooting.ja.md) | 既知の問題 + 対策 (= Windows path mangling / Scalpel typed-ast Python 3.13 build 失敗 / memray Windows 不可 / session reload 不可 / auto-mode classifier nested block) |
| [docs/algebraic_filter_project_plan.md](docs/algebraic_filter_project_plan.md) | プロジェクト計画書 (= 1〜13 章: 動機 / 問題 / アプローチ / scope / 5 Phase roadmap / 撤退基準 / 成功基準 / 差別化軸) |
| [docs/algebraic_filter_phase0_pre_reg.md](docs/algebraic_filter_phase0_pre_reg.md) | Phase 0 Pre-registration (= 仮説 H1-H4 / 成功基準 S0-1〜S0-5 / 撤退基準 W0-1〜W0-5 / baseline 計測結果 / ツール調査結果) |
| [docs/algebraic_filter_related_work.md](docs/algebraic_filter_related_work.md) | 先行研究 + 設計根拠 (= CRANE 2025 constrained decoding 限界 / Mündler PLDI 2025 型制約 / PGS 2025 PBT × LLM / Origami 2024 recursion schemes / Stream Fusion ICFP 2007) |
| [docs/tool_landscape.md](docs/tool_landscape.md) | ツール選定 + プロジェクト × ツールマトリクス (= AET-OS 3 層に対する 14 ツールの位置づけ) |
| [docs/_index/aet_os_reference.md](docs/_index/aet_os_reference.md) | AET-OS PDF 索引 + AF 対応 mapping (= Verified Orchestrator Pattern Layer 3 連動表) |
| [docs/_ab_measurement/protocol.md](docs/_ab_measurement/protocol.md) | A/B 計測 protocol (= chai 別 session 実行手順、 settings rename / hook OFF/ON 切替 / 5 task 投入手順) |
| [docs/_ab_measurement/log_template.md](docs/_ab_measurement/log_template.md) | A/B 計測 log template (= 各 task の修正サイクル数 / 残違反数 / 副作用記録欄) |
| [docs/AIエージェントアーキテクチャ調査報告.pdf](docs/AIエージェントアーキテクチャ調査報告.pdf) | AET-OS 構想 PDF (= 5 章構成、 AF が Layer 3 検証実装として整合する設計 reference) |

### samples/violations/ 配下

| 文書 | 内容 |
|---|---|
| [samples/violations/README.md](samples/violations/README.md) | 違反サンプル集の構造 + manifest 仕様 + TDD 3 層 articulate |
| [samples/violations/manifest.json](samples/violations/manifest.json) | 46 sample 仕様層 (= id / file / category / expected_detection / what_to_verify / what_is_the_problem / expected_fix / verification_result の 9 fields × 46 entries + planned_additions_phase_1 + test_coverage) |

---

## 関連プロジェクト

- **philosophy filter** (= 方針層): 「機械検証可能 → AI実行 / 不可 → 却下」 判断、 AF はこの物理実装アーム
- **AET-OS** (= Agentic Evolutionary Technology - Operating System): Verified Orchestrator Pattern、 AF はその Layer 3 (Verification Layer) 実装

## 参照論文 / 先行研究

- Banerjee et al. *CRANE: Reasoning with constrained LLM generation*, 2025 — constrained decoding の trade-off
- Mündler et al. *Type-Constrained Code Generation with Language Models*, PLDI 2025 — 型制約の効果
- He et al. *Use Property-Based Testing to Bridge LLM Code Generation and Validation*, 2025 — PBT × LLM
- Maaz et al. *Agentic Property-Based Testing: Finding Bugs Across the Python Ecosystem*, [arXiv:2510.09907](https://arxiv.org/abs/2510.09907) — AF Phase 4 と相補的方向性
- VeCoGen (Sevenhuijsen et al., 2025 FormaliSE) — C 対象、 AF は Python skill 層 独立 niche

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues / PR welcome. 違反サンプル追加は [samples/violations/manifest.json](samples/violations/manifest.json) + [samples/violations/](samples/violations/) + [samples/violations/fixed/](samples/violations/fixed/) の 3 つに対で追加。 manifest 駆動 TDD growth で test 自動増加。
