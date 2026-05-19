# algebraic-filter

**AI生成コードに対する代数法則レベルの機械検証ガードレール** — Claude Code skill + PostToolUse hook で AI が書いた Python コードを **書き込み時点で自動検証 → 違反時に自己修正サイクルを起動**。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

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
| 4 LLM 最適化フィードバック | ✓ minimal prototype | 統一 schema + history + pre-emptive hint |

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
