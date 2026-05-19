# AET-OS PDF 索引 + AF 対応 mapping

| 項目 | 内容 |
|---|---|
| 対象 PDF | [`docs/AIエージェントアーキテクチャ調査報告.pdf`](../AIエージェントアーキテクチャ調査報告.pdf) |
| 副題 | 2025 年版 AET-OS 構築に向けた技術調査および戦略的実装レポート |
| 索引化日 | 2026-05-19 (Phase 0 S0-4 部分 PASS の close 作業、 Phase 1 着手と並行) |
| Status | Phase 0 索引化完了 — Phase 1 着手後の参照基盤として landed |

---

## PDF 構造 (§ 単位)

| § | タイトル | AF 関連度 |
|---|---|---|
| 1 | エグゼクティブサマリー: 不確実性の克服と「証明可能な自律性」 への転換 | 中 (AF の動機と整合) |
| 2 | 動的オーケストレーションのパラダイムシフト | 低 (AET-OS の戦略+実行層、 AF は検証層に focus) |
| 2.1 | ADAS: コードによるエージェントの自動発明と自己増殖 | 低 |
| 2.2 | Puppeteer と AgentOrchestra: 動的リソース配分と階層化 | 低 |
| 2.3 | Microsoft AutoGen v0.4: イベント駆動型アーキテクチャ | 低 |
| 3 | 自己修正とリフレクションの最先端メカニズム | **高 (AF hook の exit code 2 = 自己修正 trigger 設計に直結)** |
| 3.1 | SCoRe: 自己生成データを用いた強化学習による修正能力 | 中 (Phase 4 LLM最適化フィードバック整形に参照) |
| 3.2 | SETS: 推論時のスケーリングと統合的検証 | **高 (AF 設計の独立検証層思想と整合)** |
| 3.3 | Ralph Loop: 持続性と終了条件の工学的制御 | 中 (Phase 1 撤退基準 / W0-5 timeout 設計に参照) |
| 4 | 形式検証 (Formal Verification) の統合: AET-OS の核心技術 | **最高 (AF の core)** |
| 4.1 | VeCoGen: LLM による形式仕様の自動生成 | 中 (C 対象、 AF Python scope 外、 H2 独立 niche 確認) |
| 4.2 | **QWED プロトコルと CrossHair: Python コードの数学的検証** | **最高 (AF Phase 1 統合の direct target)** |
| 4.3 | Lean 4 + DeepSeek-Prover-V2 | 低 (将来検討、 Phase 5+) |
| 5 | AET-OS 実装に向けた設計パターンとツール選定 | **最高 (AF 位置づけの根拠)** |
| 5.1 | **設計パターン: Verified Orchestrator Pattern** | **最高 (AF 3 層パイプライン = この検証層の具体実装)** |
| 5.2 | 実装ツールとフレームワーク選定 | 中 (CrossHair 採用根拠) |
| 5.3 | 無限ループと Halt Problem への対策: Consensus と Aegean-Serve | 低 (将来検討) |

---

## AET-OS Verified Orchestrator Pattern と AF 3 層パイプラインの mapping

PDF §5.1 (p.9) で articulate された 3 層構造:

| AET-OS 層 | 役割 | 推奨技術 | AF 対応 |
|---|---|---|---|
| **戦略層 (Strategic)** | Meta-Architect (タスク分解、 リソース配分、 サブエージェント生成) | ADAS / AgentOrchestra | AF scope 外 (Claude Code 本体が担当) |
| **実行層 (Execution)** | Worker / Specialist (コード生成、 リファクタリング) | Puppeteer Pattern | AF scope 外 (Claude Code 本体が担当) |
| **検証層 (Verification)** | Verifier / Auditor (形式仕様生成、 ソルバー実行、 安全性チェック)、 **拒否権 (Veto Power) を持つ** | **VeCoGen / QWED / CrossHair** | **AF が直接担当 = この層の Python skill+hook 実装** |

AF 3 層パイプライン (project_plan §5 articulate) は AET-OS 検証層を 3 つの sub-layer に分解した実装:

| AF Layer | AET-OS 検証層内の位置 | 採用ツール |
|---|---|---|
| Layer 1 静的 | 軽量 sanity check (PDF §3.2 SETS の 軽量検証相当) | ruff PERF/SIM/FURB/ANN/F (Phase 1 統合済) |
| Layer 2 代数法則 PBT | PDF §4.2 「CrossHair で型ヒント + assert 検証」 と native 整合 | hypothesis @given + CrossHair @icontract (Phase 1 着手後拡張) |
| Layer 3 データ移動量 | AET-OS 検証層補助 (performance / efficiency check) | tracemalloc (Windows) / memray (Linux/macOS) |

**AF hook の exit code 2 = AET-OS 検証層の「拒否権 (Veto Power)」 の具体実装**。 hook が違反検出時に Claude を block + additionalContext 注入 = AET-OS §5.1 「検証層が実行層に対して独立 + 強い権限」 と一致。

---

## PDF §3.2 SETS の核心知見 (= AF 設計思想の根拠)

PDF §3.2 (p.5) verbatim 抜粋:

> 「SETS の重要な知見は、 検証器 (Verifier) の役割である。 AET-OS への適用において特に重要なのは、 SETS が示唆する『検証器の独立性』 である。 コードを生成したのと同じプロンプトやモデルで検証を行うと、 生成時のバイアスが検証時にも影響し、 ミスを見逃す可能性が高い。 したがって、 検証フェーズには、 生成とは異なる視点 (例えば、 異なるプロンプト戦略、 あるいは後述する形式手法のような外部ツール) を持つ独立したプロセスを割り当てる設計パターンが有効である。」

AF 対応:
- AF hook は Claude Code とは **独立プロセス** (PostToolUse hook、 subprocess 経由)
- AF の検証ツール (ruff / hypothesis / tracemalloc) は **決定論的外部ツール** = SETS 提唱「生成と異なる視点」
- AF の structured feedback は **decision="block" + additionalContext** で Claude に投げる = 「拒否権」 行使

→ AF は AET-OS Verified Orchestrator Pattern の Layer 3 を Python skill+hook 層で具体実装した独自 contribution。

---

## Phase 1 統合方針 (Phase 1 着手と並行で active 化する適用 niche)

| AET-OS 概念 | Phase 1 着手後の AF 対応 |
|---|---|
| QWED の二値判定 (証明済み / 検証不能) | AF hook exit code 0 (PASS) / 2 (Veto + feedback) = 二値判定の具体実装 |
| CrossHair @icontract + assert 駆動 | Phase 1 後半で `samples/violations/` の Layer 2 sample に `@icontract` 追加 + CrossHair sample run |
| SETS 独立検証器 | AF hook の subprocess 起動 = 独立プロセス、 ruff/hypothesis/tracemalloc = 独立ツール (LLM 非依存) |
| Ralph Loop 終了条件 | AF Phase 1 後半 A/B 計測の `修正サイクル数` 集計 = Ralph Loop の Persistence Loop counter と native 整合 |
| SCoRe 自己修正 | AF hook の `additionalContext` JSON = SCoRe Stage 2 (失敗からの復旧) を trigger する input |
| 拒否権 (Veto Power) | AF hook exit code 2 = decision="block" で実装済 (Phase 1 後半-1 landed 2026-05-19) |

---

## S0-4 (H4 AET-OS 整合) closing 根拠

Pre-reg §3 H4 「Algebraic Filter は AET-OS 構想の Verified Orchestrator Pattern の Layer 3 (検証層) の具体実装として一貫している」 の判定根拠:

- ✓ AET-OS §5.1 (PDF p.9) 検証層 = VeCoGen / QWED / CrossHair の Python 統合層 → AF が担当
- ✓ AF Layer 1/2/3 がそれぞれ AET-OS 検証層の sub-layer (sanity / formal / performance) に対応
- ✓ AF hook exit code 2 = AET-OS 拒否権 (Veto Power) の具体実装
- ✓ SETS 独立検証器思想と AF の subprocess hook 設計が native 整合
- ✓ CrossHair / QWED は AET-OS で推奨ツール、 AF Phase 1 で統合 target

**H4 = 部分 PASS から full PASS へ昇格** (本索引化 close で構造対応の articulate landed)。 索引化作業は Phase 0 closing の最終条件として完了。

---

## 関連参照

- [project_plan.md §5 アーキテクチャ](../algebraic_filter_project_plan.md) — AF 3 層パイプライン
- [phase0_pre_reg.md §3 H4](../algebraic_filter_phase0_pre_reg.md) — AET-OS 整合性 仮説
- [CLAUDE.md](../../CLAUDE.md) — AET-OS Layer 3 implementation orientation
- [related_work.md](../algebraic_filter_related_work.md) — VeCoGen / CrossHair 先行研究 articulate
