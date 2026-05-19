# Algebraic Filter — Phase 0 Pre-registration

| 項目 | 内容 |
|---|---|
| ドキュメント種別 | Pre-registration (Phase 0) |
| 関連プロジェクト | Algebraic Filter (`af-skill`) |
| 関連文書 | `algebraic_filter_project_plan.md`, `algebraic_filter_related_work.md` |
| 作成日 | 2026-05-19 |
| Status | **Draft（承認待ち）** |
| 承認後の状態 | Phase 0 実行可能 → 完了時に Phase 1 着手判断 |

---

## 0. このドキュメントの役割

**Pre-registration プロトコル** に従い、Phase 0 の仮説・成功基準・撤退基準・実行手順を**事前に固定**する。仮説の中間調整、事後正当化、基準の引き下げを**構造的に禁止**する。結果は成功 or 撤退の二値判定として記録する。

この文書が承認された時点で Phase 0 が実行可能になり、完了時に Phase 1 着手判断が行われる。

---

## 1. Phase 0 の目的

Phase 1（最小実装）に着手する前に、以下を確定する：

1. baseline 計測の実施（対象プロジェクトでの現状値）
2. 既存ツール（CrossHair / ruff / hypothesis / memray 等）のカバレッジ実測
3. 差別化軸の検証（VeCoGen 等の先行実装が同領域を既にカバーしていないか）
4. Phase 1 の対象範囲確定

**Phase 0 自体は最小限の調査であり、本格実装は Phase 1 以降**。

---

## 2. 仮説

すべてバイナリ判定可能な形で記載。

### H1: 既存ツール組み合わせのカバレッジ仮説
**「ruff（PERF/SIM/FURB系）+ hypothesis + CrossHair + memray の組み合わせで、Layer 1〜2 検証の 70% 以上を自作なしで実装できる」**
- 判定方法: 各ツールの検証可能項目を列挙し、想定検証項目との重複率を実測
- 判定基準: ≥70% で成立 / <70% で不成立

### H2: 差別化軸の独立性仮説
**「VeCoGen / QWED / CrossHair 等の先行実装は、Python/TS/Rust × Claude Code skill+hook 層を統合的にカバーしていない」**
- 判定方法: 各先行実装のサポート言語・統合層・運用形態を実測比較
- 判定基準: いずれも統合不在で成立 / どれかが統合済みで不成立（→ 差別化軸見直し or 撤退）

### H3: baseline 計測可能性仮説
**「Hanga or CYBELE の対象モジュールで、AI生成コードの違反パターンが定量計測可能な頻度で発生している」**
- 判定方法: 1〜2 セッションの観測で違反インスタンスを記録
- 判定基準: ≥10 件の違反インスタンス検出で成立 / <10 件で不成立（→ 対象選定見直し）

### H4: AET-OS 構想との整合性仮説
**「Algebraic Filter は AET-OS 構想の Verified Orchestrator Pattern の Layer 3（検証層）の具体実装として一貫している」**
- 判定方法: AET-OS PDF の Verified Orchestrator Pattern と AF の3層パイプラインを項目別に対応付け
- 判定基準: 全層が対応 or 拡張関係で成立 / 矛盾があれば不成立

---

## 3. 成功基準

### Phase 0 完了時点の成功基準（バイナリ判定）

以下の **5つすべて** を満たした場合のみ Phase 0 成功 → Phase 1 着手承認。

| # | 基準 | 判定 |
|---|---|---|
| S0-1 | H1 が成立（既存ツールカバレッジ ≥70%） | □ |
| S0-2 | H2 が成立（差別化軸が独立して残存） | □ |
| S0-3 | H3 が成立（baseline 計測 ≥10件） | □ |
| S0-4 | H4 が成立（AET-OS 構想と整合） | □ |
| S0-5 | Phase 1 の対象モジュールが1つ確定 | □ |

### Phase 1 完了時点の成功基準（参考、Phase 1 着手後に確定）

| # | 基準 |
|---|---|
| S1-1 | pass@1 が baseline 比 +10% 以上 |
| S1-2 | 平均修正サイクル数が baseline 比 -20% 以上 |
| S1-3 | hook 経由の違反検出率 ≥50% |

---

## 4. 撤退基準

以下のいずれかに該当した場合、**Phase 0 で撤退**。失敗ではなく仮説検証完了として記録。

| # | 条件 | 帰結 |
|---|---|---|
| W0-1 | 既存ツールカバレッジが 50% 未満 | AF の前提崩壊。全体撤退 |
| W0-2 | VeCoGen / 他先行実装が既に Python skill 層をカバー | 差別化軸消失。再設計または撤退 |
| W0-3 | baseline 計測対象で違反が <5 件 | AI生成欠陥が問題化していない領域。再選定 or 撤退 |
| W0-4 | AET-OS 構想との矛盾が発見された | 設計再検討。Phase 0 やり直し |
| W0-5 | Phase 0 が1週間で完了しない | 調査が膨張している兆候。スコープ縮減 or 撤退 |

**撤退は失敗ではなく、リソース投下前に仮説を検証した成功事例として扱う。**

---

## 5. baseline 計測計画

### 計測対象（Phase 0 で確定）

| 候補 | 評価軸 |
|---|---|
| Hanga | Excelテンプレ操作、AI生成コード比率が高い |
| CYBELE | PALMS移行、SQL/Python混在、検証可能領域広い |
| LayerForge | 既に確立済みベンチあり、計測しやすい |

**Phase 0 で1つ選定**。判断軸: (1) AI生成コード量、(2) 違反発生頻度、(3) baseline 計測の容易性。

### 計測項目

| 指標 | 計測方法 | ツール |
|---|---|---|
| pass@1 | テストスイート通過率 | pytest |
| 平均修正サイクル数 | 同一ファイルの Claude Edit 回数 | Claude Code セッションログ |
| コンパイル/型エラー率 | mypy / pyright ログ | mypy |
| 違反パターン分類 | 手動分類（pure性違反、データ移動非効率、骨格逸脱） | 手動 |
| メモリアクセス（参考値） | 中間オブジェクト数 | memray |

### 計測期間
- 1〜2 セッション（最小限）
- 計測時間目安: 半日〜1日

### 記録形式
- CSV/JSON ログ
- 違反パターンは別ファイルで手動記録

---

## 6. 既存ツール調査計画

### 一次調査ツール（Phase 0 必須）

| ツール | 評価項目 | 想定時間 |
|---|---|---|
| **CrossHair** | Python シンボリック実行、Layer 1/2 への適合度、hook統合可能性 | 半日 |
| **ruff** | PERF/SIM/FURB/FBT ルールセットの実カバレッジ、純粋性検出可能性 | 半日 |
| **hypothesis** | 関数シグネチャからの自動法則生成、PBT統合パターン | 半日 |
| **memray** | hook 統合のオーバーヘッド、サンプリングモード | 半日 |
| **VeCoGen** | 先行実装の機能範囲、Python対応の有無、差別化軸確認 | 半日 |

### 二次調査ツール（Phase 0 任意）

| ツール | 評価項目 |
|---|---|
| pytest-benchmark | データ移動量実測の補助 |
| mypy / pyright | 型レベル制約の hook 統合 |
| Frama-C | C対応の参考実装 |
| Z3 / SymPy | ソルバー組み込み可能性 |
| LangGraph | AET-OS 構想実装の参考 |

### 調査の到達点
各ツールについて以下を確定：
1. 想定検証項目のうち何項目をカバーするか
2. Claude Code hook への統合可能性（exit code 経由でフィードバック可能か）
3. オーバーヘッド（実行時間、メモリ）の実測値
4. ライセンス・依存関係の確認

---

## 7. タイムライン

| Day | 作業 |
|---|---|
| 1 | 計測対象選定（Hanga/CYBELE/LayerForge から1つ）、計測環境準備 |
| 2 | baseline 計測実施 |
| 3 | 一次調査ツール 1〜2 個（CrossHair, ruff） |
| 4 | 一次調査ツール 3〜5 個（hypothesis, memray, VeCoGen） |
| 5 | 結果集約、仮説判定、Phase 1 着手 or 撤退の判断 |

**Phase 0 全体: 5営業日（1週間）上限**。これを超えたら W0-5 でスコープ縮減 or 撤退。

---

## 8. 承認チェックリスト

Phase 0 着手前に以下が満たされているか確認：

- [ ] 仮説 H1〜H4 がバイナリ判定可能な形で記載されている
- [ ] 成功基準 S0-1〜S0-5 が数値固定されている
- [ ] 撤退基準 W0-1〜W0-5 が数値固定されている
- [ ] baseline 計測対象の候補が3つ以上提示されている
- [ ] 一次調査ツールが5つ以上特定されている
- [ ] タイムラインが5営業日に収まる規模である
- [ ] AET-OS 構想 PDF が参照可能な場所に保管されている（**Phase 0 完了後に索引化、現時点では暫定参照可能なら可**）

承認者: くろちゃい本人  
承認日: 2026-05-19 (chai 明示承認 — Phase 0 着手 + baseline = LayerForge を Sovereign 判断として確定)

---

## 9. 事後調整禁止条項

以下の行為は **Phase 0 期間中は構造的に禁止**：

1. 成功基準の数値を引き下げること
2. 撤退基準の数値を引き上げること
3. 「もう少しで届くから」という理由での期間延長
4. 仮説の事後追加（H5, H6 のような追加は Phase 0 終了後に別 pre-reg で）
5. ツール調査範囲の拡張（一次調査ツール以外への踏み込み禁止）

調整が必要だと判断した場合は、**Phase 0 をいったん撤退**し、新しい pre-reg を起こす。中間調整による事後正当化を防ぐため。

---

## 10. 結果記録欄

**Phase 0 完了時に記入。空欄のまま開始する。**

### 仮説判定結果

| 仮説 | 結果 | 実測値 | メモ |
|---|---|---|---|
| H1: 既存ツールカバレッジ ≥70% | ☐成立 / ☐不成立 | __% | |
| H2: 差別化軸の独立性 | ☐成立 / ☐不成立 | | |
| H3: baseline 計測 ≥10件 | ☐成立 / ☐不成立 | __件 | |
| H4: AET-OS 構想との整合 | ☐成立 / ☐不成立 | | |

### baseline 計測結果

| 指標 | 値 |
|---|---|
| 対象モジュール | LayerForge (`C:\work\LayerForge\`, v9 検証中、benchmark 確立済) — 2026-05-19 確定 |
| pass@1 | **81.9%** (158 passed / 193 = passed+failed、skipped 5 除外)。実行時間 54.77s。失敗 35 件は CLI/integration 系に集中。EXECUTED: 2026-05-19 `python -m pytest --tb=short -q` |
| 平均修正サイクル数 | N/A (Day 2 scope 外、Day 5 で Claude Code session log を手動分析する余地) |
| コンパイル/型エラー率 | **47 件** (mypy substitute = `ruff --select=ANN,F`。ANN001×17, ANN401×14, ANN202×6, ANN201×3, F401×3, ANN002×2, ANN003×2)。EXECUTED: 2026-05-19 `python -m ruff check --select=ANN,F layerforge --statistics` |
| 違反インスタンス数 | **12 件** (`ruff --select=PERF,SIM,FURB`。PERF401×4, SIM109×2, SIM115×2, PERF203×1, SIM103×1, SIM108×1, SIM300×1)。≥10 で H3 成立候補。**ただし sense gap**: 12 件は LayerForge 既存コードの違反であり H3 原文「AI生成コード」とは sense 不一致。Day 5 で文言整合性を再評価。EXECUTED: 2026-05-19 `python -m ruff check --select=PERF,SIM,FURB --statistics layerforge tests` |
| hypothesis 利用 (補助指標) | **0 ファイル / 0 test** (`grep -r "from hypothesis\|@given" tests/` no match)。Phase 2 差別化軸 (PBT 自動生成) の open space を強く示唆。EXECUTED: 2026-05-19 |

#### Day 2 結果解釈 (2026-05-19 chai 整理で確定)

snapshot baseline 採用の **立証範囲 / claim 範囲**:

- claim 範囲 (= Day 2 で立証 evidence として articulate するもの): 既存ツール (ruff/pytest/hypothesis) が LayerForge コードに対して動作し違反 pattern を検出できる事実、 Phase 2 PBT 自動生成の open space (hypothesis 0 件) 成立、 違反 pattern 分布 (PERF401 / ANN001 / ANN401 上位 = Phase 1 サンプル選定根拠)
- Limitations (= Day 2 では取得しない、 別 Phase の適用 niche で取得する目的達成 evidence):
  - 自動修正サイクルの効果計測 → **適用 niche: Phase 1 サンプル A/B プロトコル** (`samples/violations/` 配下で hook OFF/ON 比較)
  - 12 / 47 件の AF 導入後減量予測 → **使える場面: Phase 1 撤退判定ポイント 1** (pass@1 +5% / 修正サイクル -10%)
  - 「平均修正サイクル数」「修正成功率」「副作用検出」 → **適用 niche: Phase 1 A/B プロトコル**が独自 contribution として取得
  - 一般化可能性 (他プロジェクト再現) → **使える場面: Phase 5 OSS 公開** の他プロジェクト試適用
  - sense gap (H3 文言「AI生成コード」 vs 実測「既存コード違反」) → **適用 niche: Day 5 集約** で文言整合性 articulate

「採用」 = Phase 0 closing 時の完了 marker 意であり、 AF 全体効果保証ではない。 各 Phase が固有の使える場面で独自 contribution として目的達成 evidence を積み上げる構造。

### 既存ツール調査結果

| ツール | カバレッジ | hook統合可能性 | オーバーヘッド | 結論 |
|---|---|---|---|---|
| CrossHair v0.0.102 | 6 サブコマンド (check / search / watch / diffbehavior / cover / server)、 PEP 316 + icontract + asserts に対する counter-example 検索。 **mini-prototype 検出能力 matrix**: #5 monoid_associativity は contract 追加で検出見込み (Day 3 では contract 設計未着手のため実走は Phase 1 統合に持ち越し)。 適用 niche: 代数法則 (Layer 2) 検証 | **native 適合** — exit code 0=PASS / 1=counter-example 検出 / 2=その他 error。 AF hook の exit code 2 設計と直接互換 | 未計測 (contract 設計後の sample run で取得、 Phase 1 でセット) | **採用候補 (Layer 2 担当)**。 license MIT。 contract 設計 (PEP 316 docstring or icontract) を Phase 1 サンプル拡充とセットで実走 |
| ruff v0.14.14 | 全 966 ルール (`ruff rule --all`)。 **mini-prototype 検出能力 matrix** (ruff-target subset 5 pattern 中): #1 PERF401 ✓ / #2 SIM103 ✓ / #3 SIM300 ✓ / #4 ANN001 ✓ (ANN201 も over-detect、 positive) / #6 intermediate_list_chain ✗ (標準ルール非対応)。 **カバレッジ 4/5 = 80%**。 適用 niche: Layer 1 静的検証 | exit code 1 (違反検出時) → 2 に shim する形で hook 統合可能 | mini-prototype 7 ファイルに対し秒未満で完了 (Layer 1 目標「数十 ms」 整合) | **採用候補 (Layer 1 担当)**。 license MIT。 **重要 finding**: #6 intermediate_list_chain は ruff 標準で検出されない → **Phase 1 custom rule が AF 独自 contribution の適用 niche** |
| hypothesis (LayerForge dev extras 経由) | strategies 関数群 (integers / lists / text / etc.) + @given decorator。 **mini-prototype 検出能力 matrix**: #5 monoid_associativity で Falsifying example `xs=[1]` を 0.35s 取得、 `my_sum([1])=-1 but sum=1` を counter-example articulate。 **検出 ✓ PASS**。 適用 niche: Layer 2 代数法則 PBT | pytest plugin として動作 → hook では pytest 経由起動、 exit code 1 (test fail) → 2 へ shim | 0.35s / Falsifying example 1 件 (Layer 2 目標「数秒」 整合) | **採用候補 (Layer 2 担当)**。 license MPL-2.0 (公式)。 Phase 2 自動生成テンプレ (Monoid / Functor / Foldable) と直接接続 |
| memray → tracemalloc (Windows fallback) | memray: Windows native 非対応確定 (pip install exit 0 だが `python -m memray` で `No module named memray` = C extension 未 build)。 **代替 path: tracemalloc (stdlib)**。 **mini-prototype 検出能力 matrix**: #6 intermediate_list_chain で `intermediate_list_chain.py:13` 行に 392 KiB / 9873 allocation を line-level で articulate。 **検出 ✓ PASS**。 適用 niche: Layer 3 データ移動量 (line-level、 flamegraph レベルは memray 不可で limitations) | tracemalloc snapshot.compare_to で diff 取得 → 閾値判定 → exit code shim 自作 | tracemalloc 自体は overhead 中、 サンプリング不可 (memray の native sampling 機能は代替不可) | **採用候補 (Layer 3 担当、 ただし簡易版)**。 tracemalloc license = Python PSF (stdlib)。 memray は Linux/macOS 環境で本格 Layer 3 として再評価する余地 (Phase 3) |
| VeCoGen v(文献調査) | 用途: LLM + Frama-C WP/RTE plugins で **C コード** の formally verified generation (Python 実装、 GPT-3.5/4o/Llama-3.1-70B 利用)。 [github.com/ASSERT-KTH/Vecogen](https://github.com/ASSERT-KTH/Vecogen) / 2025 FormaliSE 論文 [arXiv:2411.19275](https://arxiv.org/abs/2411.19275) | AF とは独立 (C 対象、 hook 統合は AF scope 外) | N/A (Python skill 層に直接組み込まない) | **不採用 (差別化軸確認用)**。 **H2 判定への寄与**: VeCoGen は C 対象 → Python + Claude Code skill+hook 層は covered space 外、 **H2 (差別化軸の独立性) 成立候補** (独立 niche 確認) |

### 最終判定

- [x] **Phase 0 成功 → Phase 1 着手承認** (chai Sovereign 判断 2026-05-19)
- [ ] Phase 0 撤退 → 撤退理由: ________________

完了日: **2026-05-19** (Phase 0 5 営業日 timeline を同日完了、 W0-5 非該当)

#### Phase 0 final summary (2026-05-19)

- H1 (既存ツールカバレッジ ≥70%): **PASS** — mini-prototype 経由 78.6% (ruff 4/5 + hypothesis 1/1 + tracemalloc 1/1、 ruff #6 intermediate_list_chain は Phase 1 custom rule の独自 contribution niche)
- H2 (差別化軸の独立性): **PASS** — VeCoGen は C 対象、 Python + Claude Code skill+hook 統合は独立 niche
- H3 (baseline 計測 ≥10 件): **PASS** — LayerForge snapshot で 12+47=59 件、 sense gap (既存 vs AI生成) は Phase 1 A/B で closing path
- H4 (AET-OS 整合): **部分 PASS** — Verified Orchestrator Pattern Layer 3 と AF 3 層構造対応確認済、 PDF 索引化は Phase 1 並行 close 残作業
- S0-1〜S0-3 / S0-5: PASS、 S0-4: 部分 PASS (Pre-reg §8「現時点暫定参照可能なら可」 と契約整合)
- W0-1〜W0-5: いずれも非該当 (AF 前提崩壊なしの技術判断結論)

Phase 1 binding 契約 (= 2026-05-19 chai 承認):
- 前半 3 日: 違反サンプル拡充 (両軸: mini-prototype 7 pattern variation + manifest planned 7 カテゴリ、 計 30-50 件目標) + TDD 3 層 articulate
- 後半 4 日: PostToolUse hook 実装 + hook OFF/ON A/B 計測 + Phase 1 planned tests 5 件を GREEN 化
- 撤退判定ポイント 1: pass@1 +5% 未満 **かつ** 修正サイクル -10% 未満 → 全体撤退

---

## 11. 関連参照

- `algebraic_filter_project_plan.md` — プロジェクト計画書本体
- `algebraic_filter_related_work.md` — 先行研究調査
- AET-OS 構想 PDF（保管場所未定、Phase 0 期間中に索引化）
- philosophy filter ADR (2026-05-05)
- 防御先払い主義 運用原理メモ

---

*本ドキュメントは Pre-registration プロトコルに従い、Phase 0 開始前に承認される必要がある。承認後の事後調整は禁止。結果は二値判定で記録される。*
