# Algebraic Filter — Related Work & Design Rationale

| 項目 | 内容 |
|---|---|
| ドキュメント種別 | Related Work & Design Rationale |
| 関連プロジェクト | Algebraic Filter (`af-skill`) |
| 作成日 | 2026-05-19 |
| 目的 | 方式選択の根拠を反証可能な形で記録し、後段公開時の参照基盤として保存 |

---

## 1. 調査の目的

Algebraic Filter は「AI生成コードに対する代数法則レベルの機械検証ガードレールを Claude Code の skill+hook 層に実装する」プロジェクト。この設計選択が「先行研究で詰められていない領域」を実際に突いているかを反証可能な形で記録する。

具体的に検証する命題：
1. 隣接領域の研究は (a) どこまで進んでいて (b) どこが詰められていないか
2. なぜ constrained decoding ではなく hook 方式を選んだか
3. なぜ代数法則レベルまで降りるのか
4. なぜデータ移動量を含めるのか
5. 既存の Claude Code skill/hook エコシステムとどう差別化されるか

---

## 2. 隣接研究領域の地図

Algebraic Filter は以下5領域の交差点に位置する。

```
                  ┌─────────────────────────────┐
                  │ A. Constrained Decoding     │
                  │   (生成中の制約)             │
                  └─────────────────────────────┘
                              │
┌──────────────────┐    ╔═══════════════╗    ┌──────────────────┐
│ E. Skill/Hook    │────║  Algebraic    ║────│ B. Post-hoc      │
│   エコシステム    │    ║  Filter       ║    │   検証 (PBT/型)  │
└──────────────────┘    ╚═══════════════╝    └──────────────────┘
                              │
                  ┌─────────────────────────────┐
                  │ C. 古典代数プログラム合成    │
                  │ D. LLM × コンパイラ協調     │
                  └─────────────────────────────┘
```

---

## 3. 領域別: 現状と限界

### 3.1 Constrained Decoding 系（生成中の制約）

| 研究 | 内容 | 効果 |
|---|---|---|
| Type-Constrained Decoding (Mündler et al., PLDI 2025) | TypeScript の型を prefix automaton に変換、decoding時に well-typed 制約 | コンパイルエラー 74.8%/56.0% 削減 (HumanEval/MBPP)、構文制約のみだと 9.0%/4.8% |
| CRANE (Banerjee et al., 2025) | 制約付きデコーディングの理論分析 | **制約が強すぎると推論能力が低下することを理論的・実証的に示した** |
| AdapTrack (2025) | 分布歪み補正で推論能力を温存 | pass@1 +7.84%/+6.42% (HumanEval/MBPP) |
| DOMINO (Beurer-Kellner et al., 2024) | サブワード整合のある制約 | 無補正比 ~2倍速 |
| GUARD (2024) | gold分布最小逸脱の制約満足 | 制約満足100% |
| TreeCoder (Princis et al., 2025) | 構文・実行制約をfirst-classでツリー探索 | 構文・実行・スタイル統合 |
| Function-Constrained Synthesis (Hajali, 2023) | 関数セットへの制約＋失敗時サブ関数生成 | 再利用ライブラリの自動蓄積 |

**限界**：
- **CRANE が示す通り、強い制約は推論能力を落とす**（致命的トレードオフ）
- 実装複雑度が高い（prefix automaton 構築、token整合管理）
- モデルごとに re-implementation が必要、運用コストが高い
- 構文・型レベルに留まり、**代数法則レベルの制約は未対応**
- データ移動量・エネルギー軸は完全に scope 外

### 3.2 Post-hoc 検証系（生成後の検証）

| 研究 | 内容 | 効果 |
|---|---|---|
| PGS (He et al., 2025) | PBT を LLM の Generator/Tester 二エージェントで反復精錬 | pass@1 +23.1〜37.3%、Wrong Answer 25.3%→10.5% |
| Agentic PBT (Maaz et al., 2025) | LLM+PBT で 100 Python パッケージを自動テスト | NumPy 等にバグ報告、56% が valid bugs |
| From Prompts to Properties (2025) | LLM 生成コードを PBT 評価 | **18〜23% が完全失敗、30〜32% が部分失敗** |
| LLM-Generated PBT vs EBT (2025) | PBT と Example-based testing の比較 | 単独 68.75%、組合せ 81.25% のバグ検出率 |
| Type-Constrained Synthesis Survey | 各種 PBT/型検証フレームワーク | hypothesis/QuickCheck/proptest 等が普及 |

**限界**：
- 個別研究は揃っているが、**Claude Code skill+hook 統合パッケージとしては未実装**
- 検証深度は性質定義に依存（自動法則テンプレ生成は未整備）
- 人間向けエラーメッセージのまま、**LLM 最適化されたフィードバック整形は未着手**
- データ移動量フィードバックは PBT の scope 外

### 3.3 古典代数プログラム合成

| 研究 | 内容 | 統合状況 |
|---|---|---|
| Bird-Meertens formalism | リスト処理の代数法則による導出 | 古典、教育文脈で残存 |
| Origami (de Souza et al., 2024) | recursion schemes (cata/ana/hylo) テンプレで合成 | 遺伝的プログラミング、**LLM 未統合** |
| Stream Fusion (Coutts et al., ICFP 2007) | 中間データ消去の代数変換 | Haskell List ライブラリで実装、時間・空間改善実証 |
| Programming LLMs with Algebraic Effect Handlers (2025) | LLM 呼び出し制御に代数を使う | **LLM への制約ではなく、LLM 利用側の代数** |
| Equality Saturation (egg/egglog) | e-graph による等価変換飽和 | 局所最適化、LLM 未統合 |

**限界**：
- 古典側の道具は揃っているが、**LLM コード生成への適用は未着手**
- Origami は GP ベース、LLM 生成への接続が空欄
- skill/hook 層への落とし込み事例なし

### 3.4 LLM × コンパイラ協調・最適化

| 研究 | 内容 | 効果 |
|---|---|---|
| Compiler Feedback for LLMs (Grubisic et al., 2024) | LLVM IR レベルのフィードバック | -Oz 比 +0.53%（**サンプリングのほうが効果大**というネガティブ寄り） |
| Meta LLM Compiler (Cummins et al., 2024) | Code Llama ベースのコンパイラ最適化 LLM | 専用モデル方向 |
| Agentic Code Optimization (2026) | 抽象化レベル別 LLM × コンパイラ協調 | 1.25x speedup |
| Halide auto-scheduler | DSL内の自動スケジュール探索 | 手書きC比5倍、手動スケジュール比1.81倍 |
| TVM AutoTVM / Exo | 領域特化の自動チューニング | ベンダー最適化を上回るケース |
| DeCOS (ICS 2025) | RL+LLM での最適化選択 | データ効率な選択 |

**限界**：
- **LLVM IR / コンパイラ層**の話で、**アプリケーションソースコード × skill層 統合**ではない
- 領域特化（Halide/TVM）は強力だが、汎用コード生成への適用は別問題
- データ移動量フィードバックは内部最適化として閉じており、**hook 層に外出しされた事例はない**

### 3.5 Claude Code skill / hook エコシステム

| 製品/パターン | 内容 | 検証深度 |
|---|---|---|
| Superpowers (183k stars) | TDD enforcement, pre-commit 検証 | テスト実行・lint レベル |
| Code Kit (claudefa.st) | FormatterHook + BiomeValidator + quality-engineer agent | 表層品質 |
| Self-Validating Agents パターン | PostToolUse + Stop の三層検証 | リント・型・テスト |
| awesome-claude-code-toolkit (135 agents, 35 skills, 20 hooks) | 多目的ツールキット | セキュリティ・古典書籍ベースレビュー等 |
| Karpathy CLAUDE.md (#1 GitHub trending) | 4 行動制約ルール | プロンプトレベル |

**限界**：
- **代数法則レベルの検証は皆無**（hypothesis テンプレ自動生成と hook 統合はゼロ）
- **データ移動量フィードバックも皆無**（memray/cachegrind を hook に組み込んだ事例なし）
- **LLM 最適化フィードバック整形も未着手**（既存ツールは人間向けエラーメッセージのまま）
- 古典代数部品庫（recursion schemes 等）の skill 化事例なし

---

## 4. ギャップ分析: 未着手領域

3章の分析から、以下が「先行研究で詰められていない領域」として残る：

| # | ギャップ | 説明 |
|---|---|---|
| G1 | **代数法則 PBT の自動生成 + hook 統合** | hypothesis 単独は存在、関数シグネチャから Monoid/Functor 法則を自動生成し hook で強制する統合実装はゼロ |
| G2 | **データ移動量の実測フィードバックを hook 層に外出し** | コンパイラ内部最適化（Halide/TVM）は存在、Claude Code hook として汎用化した実装はゼロ |
| G3 | **古典骨格 (recursion schemes) の skill 化** | Origami は GP 文脈、LLM/skill 層との統合は未開拓 |
| G4 | **LLM 最適化フィードバック整形** | 既存 linter/PBT は人間向けエラー、`{違反法則, 代替骨格, 修正例}` の構造化は未着手 |
| G5 | **constrained decoding vs hook 方式の運用パッケージ比較** | CRANE が理論で示唆、運用ベースの実装比較はゼロ |
| G6 | **philosophy filter 的方針層との二層統合** | 方針層と物理検証層を分離する設計事例は調査範囲で未確認 |

Algebraic Filter は **G1〜G4 を中核、G5〜G6 を副次** として埋める設計。

---

## 5. なぜ hook 方式を選んだか

### 5.1 vs Constrained Decoding

**選ばなかった理由**：
- **CRANE (2025) が推論能力低下を理論・実証両面で確立**。強い制約はモデルの reasoning を確実に削る
- AdapTrack (2025) が分布歪み補正の必要性を示すが、**補正自体が複雑性を追加**
- prefix automaton 構築コストが高く、モデルごとに re-implementation が必要
- 構文・型レベルに留まり、代数法則レベルは現実的に組み込めない

**hook 方式の優位性**：
- LLM の推論能力に**一切影響しない**（生成は自由、検証は事後）
- 既存ツール（ruff/hypothesis/memray）を組み合わせるだけ、実装複雑度が桁違いに低い
- shell script レベルでカスタマイズ可能、運用負荷が低い
- モデル変更で破綻しない（モデル非依存）

### 5.2 vs Post-hoc 検証単独

**Post-hoc 検証単独の限界**：
- 既存 PGS / Agentic PBT は LLM 内部の Tester エージェントに依存、確率的
- linter / type checker は表層品質に閉じる

**Algebraic Filter の補強**：
- **決定論的検証層**（ruff + 自作ルール）を最初に通す → 確率的検証 (PBT) の前で不適合を弾く
- 検証深度を3段階に切り分け、**エネルギー効率と検証深度を両立**
- **代数法則レベルの自動 PBT** で post-hoc 検証の検出力を底上げ

### 5.3 vs LLM × コンパイラ協調

**コンパイラ協調の限界**：
- LLVM IR / コンパイラ層に閉じ、**アプリケーション層の代数構造は見えない**
- Grubisic (2024) は -Oz 比 +0.53% にとどまる（**サンプリングのほうが効果大**）
- 専用モデル（Meta LLM Compiler 等）が必要、汎用 LLM では使えない

**hook 方式の補完性**：
- アプリケーション層の純粋関数性・代数法則・データ移動量を見る
- コンパイラ協調と直交、**併用可能**
- 汎用 LLM (Claude) で動く

### 5.4 vs 既存 Claude Code skill/hook パッケージ

**既存パッケージの位置**：
- Superpowers / Code Kit 等は**表層品質**（lint / format / test）に閉じる
- 検証深度が浅く、代数構造レベルの欠陥を素通しさせる

**Algebraic Filter の差別化**：
- 代数法則レベル + データ移動量レベル + LLM 最適化フィードバック整形の **3軸で深度を一段下げる**
- philosophy filter との二層統合で**方針層と物理検証層を分離**

---

## 6. なぜ代数法則レベルまで降りるか

### 6.1 表層検証の限界
- pass@k 評価では検出できない欠陥が **18〜32%** 残存（From Prompts to Properties 2025）
- linter は構文・スタイル、type checker は型、test は specific examples のみ
- **構造的正しさ（結合律・単位律・冪等性）は表層では見えない**

### 6.2 法則テストのカバレッジ特性
- PBT は無限の入力空間を法則ベースで探索 → **エッジケース検出に強い**
- LLM-Generated PBT 研究で **PBT 単独 68.75%、EBT 併用 81.25%** のバグ検出率
- 法則テンプレが揃えば、関数シグネチャから自動生成可能（手書きコスト最小）

### 6.3 「決定論で削れる部分を先に削る」原理
- 代数法則は**機械検証可能**（PBT 実行は決定論プロセス）
- LLM の確率的判断に委ねる部分を最小化、**hallucination 余地を構造的に縮小**
- 防御先払い主義の典型実装

---

## 7. なぜデータ移動量を含めるか

### 7.1 実機エネルギーの支配構造
- Horowitz の数値: 整数演算 ~1pJ、L1キャッシュ ~数pJ、DRAM ~数百pJ〜nJ
- **演算より2〜3桁、データ移動のほうがエネルギーを支配**
- 「短いコード」より「データ移動の少ないコード」が省エネ

### 7.2 静的解析の限界
- 中間 list 検出、不要 copy 検出は ruff PERF 系で可能、しかし上界推定どまり
- 実機での実際のメモリ・キャッシュ動作は**実測しか取れない**
- memray / pytest-benchmark / valgrind cachegrind の結果を hook に組み込めば突破できる

### 7.3 既存研究との接続点
- Stream Fusion (Coutts 2007) が「中間データ消去」を実証
- Halide/TVM が「データ移動を意識したスケジュール」を自動探索
- これらの**運用版を hook 層に外出し**するのが Algebraic Filter の Layer 3

---

## 8. 結論: Algebraic Filter の差別化ポジション

### 既存研究との関係を一枚で整理

| 軸 | Constrained Decoding | Post-hoc PBT | コンパイラ協調 | 既存 skill/hook | **Algebraic Filter** |
|---|---|---|---|---|---|
| LLM 推論能力への影響 | 低下 | 影響なし | 影響なし | 影響なし | **影響なし** |
| 実装複雑度 | 高 | 中 | 高 | 低 | **低〜中** |
| 検証深度: 構文 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 検証深度: 型 | ✓ | 部分 | ✓ | 部分 | ✓ |
| 検証深度: 代数法則 | ✗ | 部分 | ✗ | ✗ | **✓** |
| 検証深度: データ移動 | ✗ | ✗ | ✓（内部） | ✗ | **✓（hook外出し）** |
| LLM 最適化フィードバック | ✗ | 部分 | ✗ | ✗ | **✓** |
| 古典骨格部品庫 | ✗ | ✗ | ✗ | ✗ | **✓** |
| 方針層との分離 | ✗ | ✗ | ✗ | ✗ | **✓（philosophy filter）** |

### 主張範囲

Algebraic Filter は**「代数法則レベル × データ移動量レベル × LLM 最適化フィードバック」の3軸を統合した Claude Code 用 skill+hook パッケージ**として、調査範囲で既存実装が存在しないポジションを占める。

理論的新規性は限定的（要素技術は揃っている）が、**統合パッケージとしての新規性と実用性**は明確に open space。商品候補・OSS 公開対象として独立に成立する。

### 反証条件

以下が判明したら本ドキュメントの結論は更新される：
- G1〜G4 のいずれかを既に統合実装しているプロジェクトが見つかった場合
- CRANE の結論を覆す研究（constrained decoding が推論能力を温存できる方法）が確立された場合
- hook 方式の致命的弱点（フィードバックループの収束性等）が示された場合

---

## 9. 参照文献

### Constrained Decoding 系
- Mündler, N. et al. *Type-Constrained Code Generation with Language Models*. PLDI 2025.
- Banerjee, D. et al. *CRANE: Reasoning with constrained LLM generation*. 2025. arXiv:2502.09061
- Beurer-Kellner, L. et al. *Guiding LLMs The Right Way: Fast, Non-Invasive Constrained Generation (DOMINO)*. 2024. arXiv:2403.06988
- AdapTrack: *Constrained Decoding without Distorting LLM's Output Intent*. 2025. arXiv:2510.17376
- *Guaranteed Generation from Large Language Models (GUARD)*. 2024. arXiv:2410.06716
- Princis, H. et al. *TreeCoder*. 2025. arXiv:2511.22277
- Hajali, P. & Budvytis, I. *Function-constrained Program Synthesis*. 2023. arXiv:2311.15500

### Post-hoc 検証系
- He, L. et al. *Use Property-Based Testing to Bridge LLM Code Generation and Validation (PGS)*. 2025. arXiv:2506.18315
- Maaz, M. et al. *Agentic Property-Based Testing*. 2025. arXiv:2510.09907
- *From Prompts to Properties: Rethinking LLM Code Generation with Property-Based Testing*. FSE 2025.
- *Understanding the Characteristics of LLM-Generated Property-Based Tests*. 2025. arXiv:2510.25297

### 古典代数プログラム合成
- de Souza, M. et al. *Origami: (un)folding the abstraction of recursion schemes for program synthesis*. 2024. arXiv:2402.13828
- Coutts, D. et al. *Stream Fusion: From Lists to Streams to Nothing at All*. ICFP 2007.
- *Programming Large Language Models with Algebraic Effect Handlers and the Selection Monad*. LMPL 2025.
- Bird & Meertens. *Bird-Meertens formalism*. 古典.

### LLM × コンパイラ協調
- Grubisic, D. et al. *Compiler Generated Feedback for Large Language Models*. 2024. arXiv:2403.14714
- Cummins, C. et al. *Meta LLM Compiler*. 2024.
- *Agentic Code Optimization via Compiler-LLM Cooperation*. 2026. arXiv:2604.04238
- *Halide auto-scheduler*. SIGGRAPH 2019.
- *DeCOS: Data-Efficient RL for Compiler Optimization Selection Ignited by LLM*. ICS 2025.

### Claude Code skill/hook エコシステム
- Anthropic. *Claude Code Hooks Reference*. 2026. https://code.claude.com/docs/en/hooks
- Superpowers plugin (claude-plugins, 183k stars). 2026.
- Code Kit (claudefa.st). 2026.
- awesome-claude-code-toolkit (rohitg00). 2026.
- Karpathy, A. *CLAUDE.md best practices*. 2026.

### 内部参照
- philosophy filter ADR (2026-05-05)
- 防御先払い主義 運用原理メモ
- Algebraic Filter プロジェクト計画書 (本ドキュメントの兄弟文書)

---

*本ドキュメントは Algebraic Filter プロジェクトの設計選択に関する反証可能な記録である。新たな先行研究が発見された場合は §8 反証条件に従って結論を更新する。*
