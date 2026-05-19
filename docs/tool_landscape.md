# Tool & Project Landscape

| 項目 | 内容 |
|---|---|
| 作成日 | 2026-05-19 |
| Status | Draft（後日くろちゃい本人がレビュー・修正） |
| 目的 | ツール位置づけの再発見コストを索引参照コストに置き換える |

**注意**: このドキュメントはClaude側が持つ情報だけで初期作成された。誤りや欠落がある前提で、気が向いたときに修正する。完璧を目指さない。

---

## 1. アーキテクチャ3層（AET-OS構想ベース）

```
┌─────────────────────────────────────────┐
│ Strategic Layer (戦略層)                  │
│   タスク分解・リソース配分・サブエージェント生成 │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Execution Layer (実行層)                  │
│   コード生成・実装・タスク実行              │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Verification Layer (検証層)               │
│   形式検証・代数検証・拒否権発動            │
└─────────────────────────────────────────┘
```

---

## 2. ツールカタログ

### Strategic Layer
| ツール | 概要 | ステータス |
|---|---|---|
| ADAS | メタエージェントが新エージェントをPythonコードとして生成 | 未評価 |
| AgentOrchestra | Conductor/Supervisor/Worker の3層階層フレームワーク | 未評価 |
| Puppeteer | RL訓練のオーケストレータが動的にエージェント剪定 | 未評価 |

### Execution Layer
| ツール | 概要 | ステータス |
|---|---|---|
| Claude Code | くろちゃいの主実行環境、80〜90%委譲先 | 採用済み |
| LangGraph | 循環グラフ対応、チェックポイント機能 | 未評価 |
| AutoGen v0.4 | イベント駆動マルチエージェント、Microsoft | 未評価 |
| CrewAI | 役割ベースエージェント定義 | 未評価 |

### Verification Layer
| ツール | 概要 | ステータス |
|---|---|---|
| Kani | Rust形式検証 | 採用済み（Verification Forge） |
| CrossHair | Pythonシンボリック実行 | 検討中（Algebraic Filter候補） |
| Z3 | SMTソルバー | 未評価 |
| Frama-C / ACSL | C言語形式検証 | 不採用（C対象外） |
| VeCoGen | LLM+Frama-C統合 | 参考実装（差別化軸確認用） |
| QWED | 「LLMは信頼できない翻訳者」プロトコル | 参考思想（philosophy filterに反映済み） |
| Lean 4 + DeepSeek-Prover-V2 | 数学的証明 | 未評価（将来的検討） |
| ruff | Python高速linter | 採用予定（Algebraic Filter Layer 1） |
| hypothesis | Python PBT | 採用予定（Algebraic Filter Layer 2） |
| memray | Pythonメモリプロファイラ | 採用予定（Algebraic Filter Layer 3） |
| pytest-benchmark | 性能ベンチ | 採用予定（Algebraic Filter Layer 3） |
| mypy / pyright | Python型チェック | 採用済み（既存運用） |

### 自己修正・フィードバック系
| ツール/手法 | 概要 | ステータス |
|---|---|---|
| SCoRe | 自己生成データでのRL自己修正 | 参考思想（Algebraic Filterの違反パターン蓄積に反映） |
| SETS | 推論時のサンプリング+検証+修正の統合 | 参考思想（3層パイプライン設計に反映） |
| Ralph Loop | 持続性管理と外部Watchdog | 参考思想（撤退基準設計に反映） |

### 分析・実験系
| ツール | 概要 | ステータス |
|---|---|---|
| BERTopic / LDA / NMF / K-means | トピックモデル系 | 比較対象（LayerForge検証で使用） |
| MeCab | 日本語形態素解析 | 採用済み（LayerForge日本語処理） |

---

## 3. プロジェクト × ツール マトリクス

凡例: ✓=採用済み / ◯=検討中 / △=候補 / -=未評価/対象外

| ツール\プロジェクト | LayerForge | Verification Forge | Hanga | CYBELE | philosophy filter | Algebraic Filter |
|---|---|---|---|---|---|---|
| Claude Code | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Kani | - | ✓ | - | - | - | - |
| ruff | ◯ | - | ◯ | ◯ | - | △ |
| hypothesis | ◯ | - | - | ◯ | - | △ |
| CrossHair | - | - | - | - | - | △ |
| memray | - | - | - | - | - | △ |
| pytest-benchmark | ✓ | - | - | ◯ | - | △ |
| mypy/pyright | ✓ | - | ✓ | ✓ | - | ◯ |
| MeCab | ✓ | - | - | - | - | - |
| BERTopic等 | ✓(比較) | - | - | - | - | - |

---

## 4. プロジェクト位置づけサマリ

| プロジェクト | 役割 | フェーズ | 永続性 |
|---|---|---|---|
| LayerForge | LLM-free×決定論的テキスト分解、長期資産 | v9検証中 | 高（永続） |
| Verification Forge | Rust×Kani形式検証、Core&Shell構造 | 進行中 | 高（永続） |
| Hanga | Excel自動生成、版画philosophy | 進行中 | 中 |
| CYBELE | PALMS→CYBELE移行、SQLer案件 | 進行中 | 中（受託） |
| philosophy filter | 方針層フィルタ、ADR物理実装 | 確立済み（2026-05-05） | 高（運用基盤） |
| secretary skill | 商品候補 | 構想段階 | 中 |
| Algebraic Filter | 物理検証層、AET-OS構想のverification実装 | Phase 0直前 | 中（賞味期限つき商品候補） |

---

## 5. 整理外（明示的に除外）

| 項目 | 理由 |
|---|---|
| KDF (Knowledge Distillation Framework) | くろちゃい指定により除外 |

---

## 6. 更新ルール

- 新規ツール評価時に追記
- ステータス変更時に更新
- 大幅な構造変更があれば Section 1〜2 を改訂
- このドキュメント自体の完璧さは要求しない

---

*このドキュメントは再発見コスト削減のための索引であり、網羅性より参照容易性を優先する。*
