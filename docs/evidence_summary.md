# Evidence Summary — algebraic-filter 検証結果集約

AF の各 Phase で取得した evidence + A/B 計測結果を articulate。 Phase 1 撤退判定ポイント 1 (= pass@1 +5% / サイクル -10% 両方未達なら撤退) との照合まで。

---

## 1. A/B 計測結果 (= 真の AF 効果 evidence)

### 1-1. 計測 protocol (詳細: [docs/_ab_measurement/protocol.md](_ab_measurement/protocol.md))

- Round 1 (hook OFF): `.claude/settings.local.json` を rename して AF hook 無効化
- Round 2 (hook ON): hook 有効化
- 各 Round で違反コード書き込み + 修正依頼 task を実行
- Claude の Edit 回数 + 最終 ruff 違反数 (全 layer) を計測

### 1-2. 5 task 版 (= AI 生成 raw コード niche)

scratch/_ab_*.py に bare 違反コード (= 型注釈なし) を書かせて修正依頼。

| task | OFF Edit数 | OFF 残違反 (全 layer) | ON Edit数 | ON 残違反 (全 layer) |
|---|---|---|---|---|
| perf401 | 1 | 2 残置 | 2 | 0 |
| sim103 | 1 | 2 残置 | 2 | 0 |
| sim300 | 1 | 2 残置 | 2 | 0 |
| ann001 | 1 | 0 | 1 | 0 |
| intermediate | 1 | 2 残置 | 2 | 0 |

集計:
- 全 layer 修正成功率: OFF **1/5 = 20%** vs ON **5/5 = 100%** → **+80%**
- 平均 Edit 回数: OFF 1.0 vs ON 1.8 → +80% (= trade-off、 完成度に投資)

### 1-3. 12 sample wide 版 (= 整理済みコード niche)

manifest 駆動 で ruff-target PASS sample 12 件 (= 型注釈完備の整理済違反 sample) を使用。

| 指標 | OFF | ON | delta |
|---|---|---|---|
| 全 layer 修正成功率 | 11/12 = 91.7% | 12/12 = 100% | **+8.3%** |
| 平均 Edit 回数 | 1.0 | 1.08 | +8% (= 1 sample のみ +1) |

失敗 1 件 (= b007_unused_loop_variable hook OFF) は元 sample に型注釈なしのため、 5 task 版と同 pattern で連鎖違反残置。

### 1-4. Phase 1 撤退判定ポイント 1 照合

| 基準 | 5 task 版 | wide 版 | 判定 |
|---|---|---|---|
| pass@1 +5% 改善 | +80% | +8.3% | **両 niche でクリア** |
| 修正サイクル -10% 改善 | +80% 増加 | +8% 増加 | 未達 (= 完成度に投資する trade-off) |
| 両方未達なら撤退 (AND) | pass@1 クリア | pass@1 クリア | **撤退基準該当せず = AF 有効性立証** |

### 1-5. 適用 niche 差の articulate

| niche | AI 生成 raw コード | 整理済みコード |
|---|---|---|
| 想定環境 | Claude が新規生成する type-bare な関数定義 | 既存 sample の単 layer 違反のみ含む整理済コード |
| hook OFF 動作 | 元 violation のみ修正、 ANN001/ANN201 等の連鎖違反は task scope 外として残置 | 元 violation を修正、 連鎖違反は元から少なく完成度高 |
| hook ON 動作 | 多 layer 連鎖検出 → 全違反を 2 cycle で解消 | 単 layer 違反を 1 cycle で解消、 追加違反は元から少ない |
| AF 効果 | **+80% pass@1** (= 大 impact) | **+8.3% pass@1** (= 補助 cleanup) |

→ AF は **AI 生成 raw コードでこそ真価**、 整理済コードでも +8.3% で 撤退基準クリア。

---

## 2. Phase 0 H1-H4 仮説検証結果

詳細: [docs/algebraic_filter_phase0_pre_reg.md](algebraic_filter_phase0_pre_reg.md) §10

| 仮説 | 目標 | 実測 | 判定 |
|---|---|---|---|
| H1 既存ツールカバレッジ ≥70% | 78.6% | mini-prototype 5 ruff target + 2 hypothesis/tracemalloc target で 5.5/7 detect | **✓ PASS** |
| H2 差別化軸の独立性 | VeCoGen 等が Python skill 層未カバー | VeCoGen は C 対象、 Python + Claude Code skill+hook は独立 niche | **✓ PASS** |
| H3 baseline 計測 ≥10 件 | LayerForge で 59 件 | ruff PERF+SIM+FURB 12件 + ANN+F 47件 = 59 件 | **✓ PASS** (sense gap 注記) |
| H4 AET-OS 整合 | 構造対応 + 矛盾なし | Verified Orchestrator Pattern Layer 3 mapping landed | **✓ PASS (full 昇格)** |

S0-1〜S0-5 全達成 → Phase 1 着手承認 (chai Sovereign 判断 2026-05-19)

---

## 3. Phase 2 法則自動生成 coverage

詳細: [samples/violations/tests/test_af_phase2_coverage.py](../samples/violations/tests/test_af_phase2_coverage.py)

### 3-1. Single function API (= `auto_test()`)

| sample | 期待法則 | 検出 |
|---|---|---|
| monoid_associativity_violation | monoid_identity | ✓ FAIL |
| monoid_identity_violation | monoid_identity | ✓ FAIL |
| functor_id_violation | functor_identity | ✓ FAIL |
| fmap_compose_violation | functor_compose | ✓ FAIL |
| fmap_const_violation | functor_identity | ✓ FAIL |
| weighted_average_commutativity | commutativity | ✓ FAIL |
| commutativity_violation_in_named_commutative | commutativity | ✓ FAIL (型 strategy 推論 後) |
| intersect_commutativity_violation | commutativity | ✓ FAIL (型 strategy 推論 後) |

**8/8 = 100% 検出**

### 3-2. Monad pair API (= `auto_test_monad_pair()`)

| sample | 期待法則 | 検出 |
|---|---|---|
| monad_left_identity_violation | monad_left_identity | ✓ FAIL |
| monad_right_identity_violation | monad_right_identity | ✓ FAIL |
| monad_associativity_violation | monad_associativity | ✓ FAIL |

**3/3 = 100% 検出**

### 3-3. Class-based API (= `auto_test_class_idempotence()`)

| sample | 期待検出 | strict 結果 | flexible 結果 |
|---|---|---|---|
| idempotence_violation_in_named_set_add | FakeSet.add 冪等性 | FAIL ✓ | FAIL ✓ |
| idempotence_of_set_remove | FakeSet.remove 冪等性 | ERROR (= 空 instance で ValueError) | 違反 evidence ✓ |
| idempotence_of_dict_update | Counter.update 冪等性 | FAIL ✓ | FAIL ✓ |

**strict 2/3 + flexible 3/3 = 100% 検出**

### 3-4. 全 hypothesis-target subset coverage

合計: **single 8 + monad 3 + class 3 = 14/14 = 100%**

加えて manifest 全 46 sample に対する wide 実測:
- detected (FAIL): 10/46 = 21.7%
- inferred but passed (= 法則適用するが違反なし): 1/46
- no-law-inferred (= 関数名 keyword 非 match): 30/46 (= ruff/tracemalloc/DEFERRED 系の別 layer responsibility)
- errored (= 引数数 mismatch 等): 5/46

→ hypothesis-target subset では 100% detect、 wide では 21.7% (= AF Phase 2 の適用 niche は関数名駆動の代数法則系に特化)

---

## 4. Phase 3 静的 + 実測 coverage

詳細: [samples/violations/tests/test_af_phase3_data_movement.py](../samples/violations/tests/test_af_phase3_data_movement.py)

### 4-1. 静的 AST checker (4 rule)

| sample | 検出 rule | 結果 |
|---|---|---|
| intermediate_list_chain.py | intermediate-list-chain | ✓ |
| multi_step_intermediate_chain.py | intermediate-list-chain | ✓ |
| dict_keys_list_for_iter.py | dict-keys-list | ✓ |
| unnecessary_copy_chain.py | explicit-copy | ✓ |
| string_concat_in_loop.py | string-concat-in-loop | ✓ |
| fixed/intermediate_list_chain.py | 0 件 (ground truth check) | ✓ |

**5/5 = 100% 検出** (= data-movement target subset)

### 4-2. tracemalloc runtime

unnecessary_copy_chain.process() で 760 bytes allocation > 100 bytes threshold → `excessive-data-movement` violation 検出 ✓
fixed/intermediate_list_chain.transform() で allocation < threshold → PASS ✓

### 4-3. 全 46 sample wide coverage (= AST checker)

- detected (≥1 rule fire): 5/46 = 10.9%
- データ-movement target sample subset では **100% 検出** (= 5/5)
- 他 41 sample は別 layer (= 代数法則 / 型注釈 / ruff 標準) の独自 contribution 領域

### 4-4. Scalpel Docker bridge

[af_phase3/scalpel_bridge.py](../af_phase3/scalpel_bridge.py) — Python 3.10 container で typed-ast 互換問題回避、 main env (Python 3.13) から `docker run --rm -v` 経由で CFG 解析:
- intermediate_list_chain.py → transform 関数 CFG 取得 ✓
- multi_step_intermediate_chain.py → transform_3_steps 関数 CFG 取得 ✓
- monoid_associativity_violation.py → my_sum 関数 CFG 取得 ✓ (= Phase 2 sample も対応)

---

## 5. Phase 4 構造化 payload + anti-pattern

詳細: [samples/violations/tests/test_af_phase4_feedback.py](../samples/violations/tests/test_af_phase4_feedback.py)

### 5-1. 統一 schema (5 fields)

Phase 1 ruff output + Phase 3 StaticViolation を `{layer, violation_location, violation_law, alternative_skeleton, fix_example}` の 5 fields に統一。

例:
```json
{
  "layer": "Phase 1 ruff",
  "violation_location": "samples/violations/perf401_manual_list_comp.py:15",
  "violation_law": "PERF401",
  "alternative_skeleton": "list comprehension",
  "fix_example": "[x * 2 for x in data if x > 0]"
}
```

### 5-2. anti-pattern tracker + pre-emptive hint

JSON history persistent (= `hooks/af_violation_history.json`):
- record_violations(rule_ids, file_path) で 履歴追加
- get_preemptive_hints(rule_ids, threshold=3) で 累計 3 回以上の rule に対し warning hint message

例 hint:
```
WARNING: rule `PERF401` has been triggered 3 times across sessions.
Pre-emptive hint: review the alternative skeleton before re-writing.
```

### 5-3. hook 統合

[hooks/posttool_af_check.py](../hooks/posttool_af_check.py) で Phase 1 + Phase 3 + Phase 4 の 3 layer 統合:
- Phase 4 structured section (= skeleton + fix_example で Claude が parse しやすい構造)
- Phase 1 raw ruff output (= 詳細 context)
- Phase 3 raw AST violation list
- Action section (= 修正手順 articulate)
- Pre-emptive hint section (= history 経由)

---

## 6. End-to-end 動作 evidence (= 実 Claude session)

### 6-1. nested `claude --print` で自動 A/B (= scripts/ab_automation*.py)

- 5 task × 2 round = 10 nested session
- 12 sample × 2 round = 24 nested session
- 全 session で hook 発火 + structured feedback 注入 + Claude 自己修正サイクル動作確認

### 6-2. chai 手動 session で end-to-end

[2026-05-20 chai 試行] scratch/test_target.py に append loop 違反コード書き込み → hook 発火 → PERF401 検出 → Claude が list comprehension に修正 → 再 hook で ANN001/ANN201 検出 → Claude が型注釈追加 → hook PASS。

**多 step feedback chain (= PERF401 → ANN201 → ANN001 → PASS) の連鎖動作 evidence 取得**。

---

## 関連参照

- [docs/architecture.md](architecture.md) — 詳細アーキテクチャ
- [docs/algebraic_filter_phase0_pre_reg.md](algebraic_filter_phase0_pre_reg.md) — Phase 0 仮説 + 撤退基準
- [docs/algebraic_filter_project_plan.md](algebraic_filter_project_plan.md) — Phase roadmap
- [docs/_ab_measurement/](_ab_measurement/) — A/B 計測 protocol + log template + 結果
- [samples/violations/manifest.json](../samples/violations/manifest.json) — 仕様層 (= 46 sample のメタデータ)
