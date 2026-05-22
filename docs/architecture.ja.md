# Architecture — algebraic-filter 詳細

AF の設計を 4 軸で articulate:

1. [二層構造: philosophy filter + algebraic-filter](#1-二層構造-philosophy-filter--algebraic-filter)
2. [3 層検証パイプライン](#2-3-層検証パイプライン)
3. [AET-OS Verified Orchestrator Pattern Layer 3 として](#3-aet-os-verified-orchestrator-pattern-layer-3-として)
4. [Phase 0 〜 Phase 5 の構成 mapping](#4-phase-0--phase-5-の構成-mapping)

---

## 1. 二層構造: philosophy filter + algebraic-filter

```
┌────────────────────────────────────────────┐
│ philosophy filter (= 方針層、 2026-05-05)     │
│   判断: 「機械検証可能 → AI実行 / 不可 → 却下」  │
└────────────────────────────────────────────┘
                  ↓
┌────────────────────────────────────────────┐
│ algebraic-filter (= 物理層、 本リポジトリ)      │
│   PostToolUse hook で                       │
│   違反コードを exit 2 + feedback で block    │
│   → Claude が自己修正サイクル を起動           │
└────────────────────────────────────────────┘
```

### 役割分担

| 層 | 責務 | 実装 |
|---|---|---|
| philosophy filter | task が機械検証可能か判断 (= 委任決定) | 方針層、 chai の運用原理 |
| algebraic-filter | 機械検証可能 task の実行時に違反検出 + feedback | Phase 0-5、 本リポジトリ |

### 補完関係

- philosophy filter が「AI 実行 OK」 と判断した task に対し、 AF が **書き込み時点で違反を block + 自己修正サイクル起動**
- philosophy filter は 概念判断、 AF は 物理執行 = 二層で AI 委任の guardrail を完成

---

## 2. 3 層検証パイプライン

```
Claude Code が Write/Edit
        ↓
PostToolUse hook 発火 (= hooks/posttool_af_check.py)
        ↓
┌─────────────────────────────────────┐
│ Layer 1: 静的検証 (数十 ms)            │
│   ruff PERF/SIM/FURB/ANN/F + AF AST   │
│   - 純粋性 / 中間データ / 型注釈         │
└─────────────────────────────────────┘
        ↓ (違反あり)
┌─────────────────────────────────────┐
│ Layer 2: 代数法則 PBT (数秒)           │
│   hypothesis (auto-generated)         │
│   - Monoid / Functor / Monad 則       │
│   - 結合律 / 単位律 / 冪等性 / 可換律    │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ Layer 3: 実測 (数十秒、 選択的)         │
│   tracemalloc / memray (Linux/macOS)  │
│   - メモリアクセス回数                  │
│   - 中間オブジェクト生成数              │
└─────────────────────────────────────┘
        ↓
Phase 4: LLM 最適化フィードバック整形
  {layer, location, law, skeleton, fix_example}
        ↓
exit code 2 + JSON additionalContext
        ↓
Claude 自己修正サイクル
```

### Layer 別の検出能力

| Layer | 検出対象 | 実装 | カバレッジ |
|---|---|---|---|
| 1 静的 (ruff) | PERF / SIM / FURB / ANN / F / B / UP / RUF / C | ruff CLI | ~966 rule (= Python lint 標準) |
| 1 静的 (AF AST) | intermediate-list-chain / dict-keys-list / explicit-copy / string-concat-in-loop | `af_phase3/static_checker.py` | 4 rule (= AF 独自 contribution) |
| 2 代数法則 PBT | Monoid (2) / Functor (2) / Monad (3) / Semigroup (1) / Foldable (1) / Eq (2) / Commutativity / Idempotence (2) | `af_phase2/law_templates.py` | 13 法則 |
| 3 データ移動量 | allocation byte / 中間 list 数 / 閾値判定 | `af_phase3/runtime_checker.py` | tracemalloc (Windows + Unix) |

### エネルギー / コストモデル (= 実装の実態)

hook は層間で **short-circuit しない** (= 全 *enabled* 層を走らせて集約 = Claude が
全違反を一度に受け取る feedback 完全性を、 compute 節約より優先)。 コストは代わりに
**opt-in gating + 関数別 pre-gate** で制御:

- **Layer 1 静的** (ruff ~16ms (binary 経由) + AST ~ms): `.py` なら常時 (= 安価な常設 base)
- **Layer 2 代数法則** (hypothesis 数秒 / CrossHair **int は ~0.3s だが
  str/dict/複雑型は ~8s** = 2026-05-21 stress test 実測、 型依存): **opt-in**
  (`AF_HOOK_PHASE2_PBT` / `AF_CROSSHAIR`、 default OFF)。 ON でも関数別 pre-gate
  (法則推論あり? binary? crosshair 利用可?) で無関係関数の重い処理を skip。
- **Layer 3 データ移動量** (tracemalloc 数十秒): 選択的。

→ 重い処理は層間 short-circuit でなく **関係関数への pre-gate で最小化**。

---

## 3. AET-OS Verified Orchestrator Pattern Layer 3 として

[docs/AIエージェントアーキテクチャ調査報告.pdf](AIエージェントアーキテクチャ調査報告.pdf) §5.1 で articulate された 3 層構造に対する AF の位置:

| AET-OS 層 | 役割 | AF 対応 |
|---|---|---|
| 1 戦略層 (Strategic) | Meta-Architect (= タスク分解 / リソース配分) | AF scope 外 (= Claude Code 本体 + chai の方針判断) |
| 2 実行層 (Execution) | Worker / Specialist (= コード生成) | AF scope 外 (= Claude Code が担当) |
| **3 検証層 (Verification)** | **Verifier / Auditor (= 形式仕様生成 + ソルバー + 安全性チェック)、 拒否権 (Veto Power) を持つ** | **AF が直接担当 = 検証層の Python skill+hook 実装** |

### Veto Power の具体実装

AF hook の `exit code 2` = AET-OS 検証層の **拒否権** の物理実装:
- hook が違反検出時 → exit 2 + `decision: "block"` + structured feedback
- Claude (= 実行層) は block を受けて修正サイクルに入る (= 検証層が実行層に対し独立 + 強い権限)

### SETS 独立検証器思想との整合

AET-OS PDF §3.2 verbatim:
> 検証フェーズには、 生成とは異なる視点 (例えば、 異なるプロンプト戦略、 あるいは後述する形式手法のような外部ツール) を持つ独立したプロセスを割り当てる設計パターンが有効である。

AF の対応:
- hook は subprocess で起動 (= Claude session とは独立プロセス)
- 検証 tool は ruff / hypothesis / tracemalloc (= LLM 非依存の決定論ツール)
- structured feedback で Claude に拒否権行使 (= 独立視点からの修正要求)

### CrossHair / QWED との関係

AET-OS PDF §4.2 で推奨される CrossHair + QWED は Python 形式検証の standard。 AF は:
- **CrossHair = `af_phase2/crosshair_bridge.py`** — opt-in (`AF_CROSSHAIR`) で binary 関数の結合/可換律を SMT **証明** (= 推論法則から契約自動生成)。 決定論、 sampling が見逃す稀値違反を捕捉 (2026-05-21 検証、 FP ゼロ)。 適用範囲: binary + 結合/可換、 default OFF。 (`af_phase3/scalpel_bridge.py` は別物の **Scalpel** CFG bridge であり CrossHair ではない)
- QWED 「LLM は信頼できない翻訳者」 哲学 = AF 全体の設計思想 (= LLM 生成を決定論ツールで検証)

---

## 4. Phase 0 〜 Phase 5 の構成 mapping

| Phase | 役割 | 主要 file | 状態 |
|---|---|---|---|
| 0 Pre-reg | 仮説 H1-H4 + 撤退基準 + baseline 計測 | [docs/algebraic_filter_phase0_pre_reg.md](algebraic_filter_phase0_pre_reg.md) | ✓ closing (2026-05-19) |
| 1 PostToolUse hook | hook script + 違反 sample 46 件 + manifest 駆動 TDD | [hooks/posttool_af_check.py](../hooks/posttool_af_check.py) + [samples/violations/](../samples/violations/) | ✓ end-to-end 動作確認 |
| 2 代数法則 PBT 自動生成 | inferrer + law_templates + generator | [af_phase2/](../af_phase2/) | ✓ 13 法則 + 100% subset coverage |
| 3 データ移動量 | static_checker + runtime_checker + Scalpel Docker | [af_phase3/](../af_phase3/) + [af_phase3_scalpel/](../af_phase3_scalpel/) | ✓ 拡張完成 |
| 4 LLM 最適化フィードバック | feedback_formatter (Phase 1+2+3 統合 schema) + anti_pattern_tracker (per-rule threshold) | [af_phase4/](../af_phase4/) | ✓ integrated + A/B verified |
| 5 OSS 公開 | README + LICENSE + pyproject + GitHub push | この repository | ✓ initial push |

### Phase 0 binding 契約 達成

- H1 既存ツールカバレッジ ≥70% → mini-prototype で 78.6% PASS
- H2 差別化軸の独立性 → VeCoGen は C 対象、 AF は Python skill 層独立 niche PASS
- H3 baseline 計測 ≥10 件 → LayerForge で 59 件 PASS (sense gap 注記)
- H4 AET-OS 整合 → Verified Orchestrator Pattern Layer 3 mapping landed (full PASS 昇格)
- S0-1〜S0-5 全達成 → Phase 1 着手承認

### Phase 1 撤退判定 ポイント 1 クリア

A/B 計測 evidence (= クリーン再計測 2026-05-22、 [docs/evidence_summary.ja.md](evidence_summary.ja.md) §1):
- `_ab_live/` (hook 発火) で機能プロンプト・full-select 計測: OFF 0/5 clean (違反 11) → ON 5/5 (0)
- 撤退判定基準 (+5%) を **この corpus で** クリア (= 小 n / 単一実行 / AF 自前 task / ANN 主導、 一般保証ではない)
- 旧「+80%/+8.3%」 は **撤回** (= scratch で ruff 無効 + answer-leak プロンプトのため)

---

## 関連参照

- [docs/algebraic_filter_project_plan.md](algebraic_filter_project_plan.md) — Phase roadmap 詳細
- [docs/algebraic_filter_related_work.md](algebraic_filter_related_work.md) — 先行研究比較
- [docs/_index/aet_os_reference.md](_index/aet_os_reference.md) — AET-OS PDF 索引 + mapping
- [docs/tool_landscape.md](tool_landscape.md) — ツール選定の根拠
