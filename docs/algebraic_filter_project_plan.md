# Algebraic Filter — プロジェクト計画書

| 項目 | 内容 |
|---|---|
| プロジェクト名 | Algebraic Filter (`af-skill`) |
| 一行説明 | AIコード生成に対する代数法則レベルの機械検証ガードレール |
| 位置づけ | philosophy filter の代数層実装。物理層フィルタとして稼働 |
| 作成日 | 2026-05-19 |
| Status | Draft (pre-reg未承認) |

---

## 1. なぜこれをやるのか

### 一行サマリ
受託 80% を Claude Code に委譲している環境で、AI生成コードの代数構造レベルの欠陥が認知負荷の主要発生源になっている。これを hook 層に物理実装して自動却下する仕組みを作る。副産物として商品候補が一つ増える。

### 個人運用文脈
- Claude Code への 80〜90% 委譲環境では、AI生成コードの欠陥がそのまま判断層への割り込み要因になる。自分がレビュー・修正に引き戻されるたびに最上位動機（楽して最大効果）から乖離する
- philosophy filter で方針層（「機械検証可能 → AI実行 / 不可 → 却下」）は2026-05-05 に確立済み、しかし**コード生成時の物理検証アームが欠けている**
- 防御先払い主義に従えば、検証 hook を1回設定するコスト ≪ 違反コードを毎回手で潰すコスト。時間軸逆転コスト構造が成立する典型ケース
- 結果として、原資装置である受託の生産性そのものを底上げできる

### 戦略的文脈
- 現在「原資拡大フェーズ」、商品開発は「余裕の中での実験」として開始可能な段階
- 商品候補プール（5製品 + philosophy filter + secretary skill）への自然な追加候補
- 受託環境の副産物として自然に蓄積される設計のため、**専用工数を最小化したまま商品化導線を確保できる**

### なぜ今か
- Claude Code の hook 機構（PostToolUse, exit code 2 によるフィードバック注入）が2026年初頭に成熟
- ruff / hypothesis / memray 等の既存ツールが組み合わせ可能な粒度に発展
- LLM コード生成への constrained decoding の限界が学術的に明確化（CRANE 2025）→ **hook 方式の優位性が論証された**
- 統合パッケージ（代数制約 × 古典部品 × skill層実装）は調査範囲で未実装 = open space

---

## 2. 解決する問題

### 一次問題: AI生成コードの構造的欠陥
- 失敗の **33.6% が型エラー**（Mündler 2025）
- PBT 評価で **18〜23% が完全失敗、30〜32% が部分失敗**（From Prompts to Properties 2025）
- pass@k 評価では見えない代数構造レベルの欠陥が大量に潜在
- 結果として「動くが脆い・遅い・非効率」なコードが本番に紛れ込み、後段の認知負荷を膨張させる

### 二次問題: 既存検証ツールの検証深度不足
- ruff / formatter / TDD enforcement hook は**表層品質**（構文・スタイル・型）に留まる
- 代数法則レベル（純粋性、結合律、Functor 則、Monoid 則等）の検証が手薄
- データ移動量レベル（メモリアクセス、中間オブジェクト生成、キャッシュミス）の検証は事実上皆無
- エラーメッセージは人間向けで、LLM の修正成功率を直接押し上げる構造化がされていない

### 三次問題: 既存制約方式のトレードオフ
- **constrained decoding は LLM の推論能力を低下させる**（CRANE 2025）
- 単純な post-hoc lint だけでは生成側の自由度が縛れず、繰り返し違反が発生
- **「代数制約 × 古典部品庫 × skill+hook 層実装」の統合パッケージは未実装**

---

## 3. 解決アプローチ

### 基本戦略: hook 方式による物理層検証
constrained decoding（生成中の制約）ではなく、**Claude Code の PostToolUse hook で生成後検証**を行う。

これにより：
- LLM の推論能力を一切損なわない（CRANE 問題の回避）
- 検証は決定論的に実行される（hallucination ゼロ）
- 違反は exit code 2 経由で additionalContext として Claude に注入され、**自己修正ループが自動で回る**
- hook の設定コストは1回、効果は以降の全書き込みに永続適用される（防御先払い構造）

### 検証深度の段階化
3層検証パイプライン（静的 → PBT → 実測）で、軽い層で弾けるものは軽い層で弾く。エネルギー効率と検証深度を両立。詳細は §5 アーキテクチャ参照。

### 差別化軸（既存 lint hook との明確な違い）
1. **代数法則レベルの PBT 自動生成** — 関数シグネチャから Monoid / Functor / Foldable 等の法則テストを自動生成し、表層テストでは見えない構造的欠陥を検出
2. **データ移動量の実測フィードバック** — 静的解析の上限を memray / pytest-benchmark で突破、省エネ軸を運用ベースで担保
3. **LLM最適化されたフィードバック整形** — `{違反箇所, 違反法則名, 代替骨格名, 修正例}` の構造化により Claude の修正成功率を直接押し上げる

### 上位原理との整合
| 原理 | 実装での具現化 |
|---|---|
| 防御先払い主義 | hook 設定1回 → 以後の全書き込みで自動検証。撤回コスト先払い |
| 機械検証可能 → AI実行 / 不可 → 却下 | hook exit code が委任決定木の物理実装 |
| 最小コンテキスト × ハルシネーション最小化 | 構造化フィードバックでClaude側コンテキスト消費を最小化 |
| 楽して最大効果 | 既存ツール組み合わせで7割カバー、自作部分は差別化軸に集中 |

philosophy filter（方針層） + algebraic filter（物理検証層）の二層構造で、**AI委任における自動却下機構を完成させる**。

---

## 4. スコープ

### IN
- PostToolUse hook 経由の検証パイプライン（ruff / hypothesis / pytest-benchmark / memray の組み合わせ）
- 関数シグネチャからの代数法則 PBT テンプレ自動生成（Monoid / Functor / Foldable 等）
- データ移動量の静的検出＋実測フィードバック
- LLM最適化されたエラーメッセージ整形（違反法則名・代替骨格・修正例を構造化）
- 違反パターンの自己蓄積機構（`anti_patterns.md` 自動追記）

### OUT（初期スコープ外）
- 新規LLMモデル学習・fine-tuning
- constrained decoding の独自実装
- Python / TypeScript / Rust 以外の言語サポート
- IDE プラグイン化（hook 経由で十分なため）

---

## 5. アーキテクチャ

### 3層検証パイプライン

```
Claude Code が Write/Edit
        ↓
PostToolUse hook 発火
        ↓
┌─────────────────────────────────┐
│ Layer 1: 静的検証 (数十ms)        │  ruff PERF/SIM/FURB + custom rules
│   - 純粋性チェック               │
│   - 中間データ構造検出           │
│   - 古典骨格使用の強制           │
└─────────────────────────────────┘
        ↓ (合格時のみ)
┌─────────────────────────────────┐
│ Layer 2: 代数法則 PBT (数秒)     │  hypothesis (auto-generated)
│   - 結合律 / 単位律              │
│   - 冪等性 / 可換律              │
│   - Functor 則 / Monoid 則       │
└─────────────────────────────────┘
        ↓ (合格時のみ)
┌─────────────────────────────────┐
│ Layer 3: 実測 (数十秒、選択的)    │  memray / pytest-benchmark
│   - メモリアクセス回数           │
│   - キャッシュミス率             │
│   - 中間オブジェクト生成数       │
└─────────────────────────────────┘
        ↓ (違反時)
LLM最適化フォーマッタ → exit code 2 → Claude 自己修正
```

### 検証深度のエネルギー効率

軽い層で弾けるものは軽い層で弾く設計。Layer 1 は数十ms / Layer 2 は数秒 / Layer 3 は数十秒。後段ほどコスト高なので、段階的に通過させる。

---

## 6. 実装フェーズ

### Phase 0: Pre-registration (1日)
- 仮説・成功基準・撤退基準を `af_phase0_pre_reg.md` に記載
- 既存ツール調査（ruff / hypothesis / memray のカバレッジ実測）
- baseline 取得対象プロジェクトの選定（Hanga or CYBELEの一部）

### Phase 1: 最小実装 (1週間)
- **前半 (3 日): 違反サンプルコード集の拡充 + TDD 3 層 articulate** (2026-05-19 chai 整理 + 整合完全化で landing)
  - 配置: `C:\work\algebraic-filter\samples\violations\` (AF プロジェクト内自家管理、 read-only ではない)
  - **拡充 pattern (両軸併記)**:
    - **軸 1: Phase 0 mini-prototype 7 pattern の variation 拡張** (#1 perf401, #2 sim103, #3 sim300, #4 ann001, #5 monoid_associativity, #6 intermediate_list_chain, #7 purity) を各 3〜5 variation
    - **軸 2: manifest.json planned_additions_phase_1 の 7 カテゴリ追加**: Functor 則 / Foldable / Monad 則 / 可換律 / 冪等性 / Stream Fusion 系 / 純粋性 variants / 型注釈 variants 各 3〜5 variation
    - 合計目標: 30〜50 件 (chai 指示「大量に用意していい」 反映)
  - 各 pattern につき 1 ファイル = 1 違反 isolating + `samples/violations/fixed/<id>.py` に期待修正後コード (ground truth)
  - **TDD 3 層 articulate** (chai 指示「テスト先に大量に用意して TDD として使用」 2026-05-19 反映):
    - 仕様層: [samples/violations/manifest.json](../samples/violations/manifest.json) (各 sample の expected_detection / what_to_verify / what_is_the_problem / expected_fix)
    - テスト層: [samples/violations/tests/test_manifest_driven.py](../samples/violations/tests/test_manifest_driven.py) (manifest 駆動 pytest parametrize で test-first)
    - Ground truth 層: `samples/violations/fixed/` (期待修正後コード)
    - 実装層: AF hook (Phase 1 後半で landing、 Phase 1 planned tests を GREEN 化)
  - TDD growth property: manifest.json samples 追加 → pytest parametrize 自動的にテスト増加 = chai 指示「大量」 への継続的 path
- **後半 (4 日): PostToolUse hook + A/B 計測プロトコル**
  - hook 実装: PostToolUse で ruff PERF/SIM/FURB/ANN/F + 既存 hypothesis テンプレ + tracemalloc 簡易、 違反検出時 exit code 2 で additionalContext 注入
  - hook OFF run: サンプル違反コードを Claude Code に修正依頼、 修正サイクル数を log 集計
  - hook ON run: 同じサンプルに hook を有効化、 自己修正サイクル数を log 集計
  - Phase 1 planned tests (manifest test_coverage section articulate 済): `test_af_hook_emits_exit_2_on_violation` / `test_af_hook_provides_structured_feedback` / `test_crosshair_with_icontract_detects_violation` / `test_purity_custom_rule_detects_print` / `test_af_hook_a_b_modification_cycles_reduce`
- 計測指標 (Day 2 で取得していない自動修正サイクル側の目的達成 evidence):
  - 修正サイクル数 (Claude Edit 回数)
  - 最終生存違反数 (hook OFF 取りこぼし vs hook ON 改善幅)
  - 修正成功率 (期待修正後コードとの diff 一致率 = ground truth 層との比較)
  - 副作用検出 (元違反以外の悪化がないか)
- **撤退判定ポイント1**: pass@1 改善 +5% 未満 **かつ** 修正サイクル数改善 -10% 未満 → ガードレール方式の有効性反証として全体撤退

### Phase 2: 代数法則 PBT テンプレ自動生成 (2週間)
- 関数シグネチャ → 期待される法則の推論
- Monoid / Functor / Foldable / Traversable の標準法則テンプレ
- 型ヒント駆動で hypothesis テストを自動生成
- カバレッジ実測

### Phase 3: データ移動量フィードバック (2週間)
- 静的: 中間 list / 不要 copy / 連鎖 comprehension の検出（ruff PERF 系拡張）
- 実測: memray サンプリング + pytest-benchmark
- 閾値判定 → Claude向け構造化フィードバック
- **撤退判定ポイント2**

### Phase 4: LLM最適化フィードバック整形 (1週間)
- ruff / hypothesis のエラー → `{違反箇所, 違反法則, 代替骨格, 修正例}` の構造化
- anti-patterns の自動蓄積機構
- 同一違反3回 → 事前ヒント注入

### Phase 5: パッケージ化・OSS公開 (任意、2週間)
- skill+hook セットとして配布形式整備
- ドキュメント・サンプル・ベンチ結果公開
- philosophy filter からの導線設計

### 合計タイムライン目安: 約6週間（並行プロジェクトとの折り合いで延長余地あり）

---

## 7. 検証戦略

### Golden Master Testing 採用
- Phase 1 で対象プロジェクトの baseline 計測（hook なし）
- 各 Phase 完了時に同じ計測を再実行
- 改善量を pre-reg した基準と照合

### 計測指標
| 指標 | 計測ツール | Phase |
|---|---|---|
| pass@1 | テストスイート実行 | 1〜 |
| 平均修正サイクル数 | Claude Code セッションログ | 1〜 |
| コンパイル/型エラー率 | ruff / mypy ログ集計 | 1〜 |
| PBT 失敗率 | hypothesis 統計 | 2〜 |
| メモリアクセス削減 | memray | 3〜 |
| 中間オブジェクト生成数 | memray | 3〜 |

### Pre-reg → バイナリ実行プロトコル
従来運用と同じ。仮説と判定基準を先に固定、結果は成功 or 撤退の二値で記録。中間調整による事後正当化を構造的に禁止する。

---

## 8. 撤退基準

| Phase | 条件 | アクション |
|---|---|---|
| 1 | pass@1 改善が +5% 未満 **かつ** 修正サイクル数の改善が -10% 未満 | ガードレール方式そのものの有効性反証 → 全体撤退 |
| 2 | 代数法則 PBT 自動生成のカバレッジが 50% 未満 | Phase 2 を手書きテンプレ運用に縮退 |
| 3 | データ移動量フィードバックが修正改善に繋がらない | データ移動軸を OUT 化、Phase 4 へ |
| 全般 | 既存ツール組み合わせで7割効果が出ない | 自作部分の価値仮説反証 → 縮退 or 撤退 |

撤退は失敗ではなく仮説の検証完了として扱う。

---

## 9. 成功基準

| Phase | 基準 |
|---|---|
| 1 | pass@1 +10% 以上、修正サイクル数 -20% 以上 |
| 2 | 代数法則 PBT 自動生成カバレッジ 70% 以上 |
| 3 | 対象ベンチでメモリアクセス -30% 以上 |
| 4 | 違反フィードバック適用後の修正成功率 +15% |
| 5 | OSS 公開、philosophy filter からの導線として機能 |

---

## 10. リスクと対策

| リスク | 影響度 | 対策 |
|---|---|---|
| 既存ツールで7割カバーできない | 高 | Phase 0 で網羅調査、必要なら scope 縮退 |
| フィードバックがコンテキスト膨張要因に | 中 | 出力長キャップ (10,000 chars)、構造化最小化 |
| Phase 3 の実測オーバーヘッドが過大 | 中 | サンプリング化、開発時のみ起動、CI 分離 |
| ruff カスタムルールの保守コスト | 中 | 標準ルール優先、自作は最小化 |
| Claude Code の hook API 変更 | 低 | Anthropic 公式ドキュメント追従、バージョン pin |

---

## 11. 差別化軸（商品候補としての価値）

既存の lint / formatter / TDD enforcement hook と明確に異なる3点：

1. **代数法則レベルの検証** — hypothesis を法則テンプレで自動生成、表層テストでは見えない欠陥を検出
2. **データ移動量の実測フィードバック** — 静的解析の上限を実測で突破、省エネ軸を運用ベースで担保
3. **LLM最適化フィードバック整形** — 違反法則・代替骨格・修正例を構造化、Claudeの修正成功率を直接押し上げる

商品候補プールへの追加: 既存5製品 + philosophy filter + secretary skill + **algebraic filter**

想定導線: philosophy filter（方針層）→ algebraic filter（物理層）の二層パッケージとして OSS 公開。受託 80% Claude Code 委譲環境の副産物として自然に蓄積される、原資拡大フェーズと整合する商品開発ルート。

---

## 12. 参照資料

### 外部
- Mündler et al. *Type-Constrained Code Generation with Language Models*, PLDI 2025
- He et al. *Use Property-Based Testing to Bridge LLM Code Generation and Validation*, 2025
- Banerjee et al. *CRANE: Reasoning with constrained LLM generation*, 2025
- de Souza et al. *Origami: (un)folding the abstraction of recursion schemes for program synthesis*, 2024
- Bird & Meertens. *Bird-Meertens formalism*（古典）
- Coutts et al. *Stream Fusion: From Lists to Streams to Nothing at All*, ICFP 2007
- Anthropic. *Claude Code Hooks Reference*, 2026

### 内部
- philosophy filter ADR (2026-05-05)
- 防御先払い主義 運用原理メモ

---

## 13. 次のアクション

1. Phase 0 pre-reg ドキュメント作成
2. 既存ツール調査（ruff / hypothesis / memray のカバレッジ実測）
3. baseline 取得対象プロジェクトの選定と合意
4. Phase 1 着手判断（pre-reg 承認後）

---

*このドキュメントは pre-registration の対象であり、Phase 0 承認をもって実行段階に移行する。仮説の中間調整は禁止、撤退基準への到達は成功 or 撤退の二値判定として処理する。*
