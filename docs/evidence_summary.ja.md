# Evidence Summary — algebraic-filter 検証結果集約

AF の各 Phase で取得した evidence + A/B 計測結果を articulate。 Phase 1 撤退判定ポイント 1 (= pass@1 +5% / サイクル -10% 両方未達なら撤退) との照合まで。

---

## 1. A/B 計測結果 (= in-vivo AF 効果)

> **訂正 (2026-05-22)** — 旧「+80% / +8.3% pass@1」 は **信頼できないため撤回**。
> 実際に走らせて判明した三重欠陥:
> 1. **測定場所**: `scratch/` に書いていたが、 `pyproject.toml` の
>    `[tool.ruff.lint.per-file-ignores] "scratch/*.py" = ["ALL"]` が `--select`
>    明示でも全 ruff ルールを無効化 → hook の ruff 層が発火せず `ruff_check_final`
>    も常に 0 (実証: scratch の PERF401 は block されず、 同じファイルが root では
>    block される)。
> 2. **answer-leak**: プロンプトが欠陥名を明示 (「PERF401 を修正して」) → hook OFF
>    でも修正してしまう。
> 3. **内部矛盾**: 公開していた 5-task 表 (OFF 1/5) が automation log (OFF 5/5) と
>    不一致 = 再現不能。
>
> 下記のクリーン再計測で置換する。

### 1-1. クリーン protocol (v3、 2026-05-22)

`scripts/ab_automation.py` (nested `claude --print`、 5 task × OFF/ON):
- **場所 `_ab_live/`** (scratch でない) → hook の ruff 層が実発火。
- **機能プロンプトのみ** — 各 task は振る舞いの目的だけ述べ、 欠陥名もコードも固定
  しない → モデルは自由に書き、 hook feedback を取り込める。
- 残存違反は **hook と同じ full select** (PERF,SIM,FURB,ANN,F,RUF013 + Phase 3
  AST) で計測。

### 1-2. 結果

| Round | clean ファイル | 残存違反 | 平均 edits/task |
|---|---|---|---|
| OFF (hook 無効) | **0/5** | **11** | 0.0 |
| ON (hook 有効) | **5/5** | **0** | 1.0 |

task 別 (OFF→ON 残存): perf401 2→0、 sim103 2→0、 sim300 2→0、 ann001 3→0、
intermediate 2→0。

### 1-3. honest な読み (= 効果の実態)

- 機能プロンプトだとモデルは **機能的に綺麗なコード**を書く (PERF401 なし・ yoda
  なし・ 中間 list なし) → AF の PERF/SIM/データ移動 **差別化軸は発火せず**。 有能な
  モデルはこれらを自分で避ける。
- だが **全 OFF 関数が型注釈欠落** (ANN001/ANN201) を出荷 — モデルは型注釈を自発
  追加しない。 hook (ON) がこれを捕捉 → モデルが各 1 edit で自己修正 → 0 違反。
- よって今回の in-vivo 効果は **0/5 → 5/5 clean (11→0)、 ほぼ ANN (型注釈) 軸が主**。
  ANN を除けば OFF も ON もほぼ clean。 単純 lint では効果は実在するが narrow、 AF の
  より大きな潜在価値は **モデルが自分で避けない欠陥クラス** (代数法則・データ移動)
  にあり、 今回の task ではそれが発生しなかった。

> **「% 改善」でなく「保証」として読む。** ガードレールの価値は enforce する
> *不変条件* であって percentage ではない。 hook ON (= モデルが修正に応じる前提)
> では **AF 検出可能な構造違反を1件も出荷しない** — 「hook が発火しない」 こと自体が
> その関数を AF の軸 (lint + データ移動 + 認識名の代数法則) で clean と *認証* する。
> ON 5/5 clean はこの不変条件の成立。 有能なモデルが元々綺麗に書く ⇒ AF は
> **低摩擦で clean を確認 + 取りこぼし捕捉** (今回は型注釈) = ガードレールの理想挙動。
> 保証範囲は AF の *検出可能* 軸 (意図/logic は対象外)、 かつモデルが修正に応じる
> 前提 (hook は助言、 §1-4)。

### 1-4. もう一つの honest な発見 — hook は強制でなく助言

中間 run (「このコードを exactly に書け」と固定したプロンプト) では ON = OFF = 7
残存だった: モデルは **hook を無視してコードを verbatim 維持**し、 ユーザー明示指示が
hook の `exit 2` feedback を上書きすると判断した。 つまり hook は **ユーザー意図と
weigh される助言 feedback** であり hard gate ではない。 指示に余地がある時 (機能
プロンプト、 §1-2) は効くが、 ユーザーがコードを固定すると効かない。

### 1-5. Phase 1 撤退判定ポイント 1 照合

pass@1 (= 違反 0 率): OFF **0%** → ON **100%** (この corpus) → +5% 基準クリア。
留保: 小 n (5 task)・単一実行・AF 自前 task・**ANN 主導** = 一般保証ではない。

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

### 3-5. 証明の深さ: 決定論 (CrossHair) vs サンプリング (hypothesis)

上の検出は大半が **hypothesis サンプリング** (確率的確信)。 **決定論的に証明された**
核はもっと狭い: **14 法則テンプレ中 7 個**が binary 関数で CrossHair SMT 証明可能
(結合・semigroup 結合・可換・additive identity・binary 冪等・eq 反射律・eq 対称律 —
2026-05-22/24 に 3→5→7)。 残り 7 (functor / monad / foldable) は sampling のみ。
`test_af_phase2_proof_coverage.py` で固定。 これが honest な「証明された深い核」の数値
([limitations.ja.md](limitations.ja.md) 「決定論の島」参照)。

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

### 6-1. nested `claude --print` で自動 A/B (= scripts/ab_automation.py)

クリーン再計測 2026-05-22 (v3): 5 task × OFF/ON = 10 nested session、 `_ab_live/`、
機能プロンプト、 full-select 計測 → §1-2 (OFF 0/5 → ON 5/5、 11→0 残存)。 ON round
で hook 発火 + モデル自己修正 (1 edit/task) を確認。

> 旧 scratch ベース run (5×2、 12×2) は **撤回**: `scratch/` に書いており (ruff
> per-file-ignores ALL で ruff 層死) answer-leak プロンプトだった。 JSON log
> (`log_auto_*.json`) は記録として local 保持するが有効 evidence ではない。

### 6-2. 検証済み hook 発火挙動 (= 場所が効く、 2026-05-22 実測)

| 書込先 | ruff 層 (PERF/SIM/FURB/ANN) | Phase 3 AST |
|---|---|---|
| `scratch/*.py` | **発火せず** (`per-file-ignores = ["ALL"]`) | 発火 |
| `_ab_live/` or repo root (非 ignore) | **発火** (exit 2 + feedback) | 発火 |

直接実証: `scratch/` の PERF401 は block されず、 同じファイルが `_ab_live/` / root で
は `exit 2` で block。 intermediate-list-chain はどこでも block (Phase 3 は ruff 設定
非依存)。 v3 ON round でモデルは hook feedback を受け自己修正 (例: `add(x, y)` →
`add(x: int, y: int) -> int`)。

> 訂正: 旧記録は「`scratch/test_target.py` で hook 発火」と書いていたが、 検証済み
> `per-file-ignores` 挙動と矛盾するため削除。

---

## 7. 競合比較 (claude-code-quality-hook) — 2026-05-20 実測

46 sample violation corpus での head-to-head 比較。 competitor の **実際の**
Python stack (= source `quality-hook.py` から確認) は **`ruff check` で
`--select` なし (= ruff デフォルト E/F) + pyright** で、 AF の rule selection
ではない。 AF stack = **ruff(PERF/SIM/FURB/ANN/F/RUF013) + Phase 3 AST + Phase 2
runtime PBT**。

> ⚠️ **corpus bias 開示 (最初に読むこと)**: この 46 sample は *AF が自分の
> target defect (代数法則 / perf / データ移動量) を showcase するため設計* した。
> **AF の home field であって中立 benchmark ではない**。 型エラー主体の corpus
> なら competitor の pyright が勝つ。 以下の数値は *どちらの tool がどの defect
> class を狙うか* を示すもので、 一般的優劣ランキングではない。

### 7-1. 検出 — competitor の実構成で訂正

| stack | 検出 | カバレッジ |
|---|---|---|
| competitor ruff (デフォルト E/F) | **0**/46 | 0% |
| competitor pyright | 7/46 | 15% |
| **competitor full (ruff default + pyright)** | **7**/46 | **15%** |
| AF ruff (PERF/SIM/FURB/ANN/F/RUF013) | 12/46 | 26% |
| **AF full (ruff + Phase 3 + Phase 2 runtime)** | **28**/46 | **61%** |

**訂正注記**: 本 section の旧 draft は competitor に *AF の* ruff selection を
与えて 18/46 としていた = 過大評価。 competitor の ruff はデフォルト動作で、
この corpus の perf/algebraic sample を **0 件** しか検出しない — 7 件は全て
pyright 型検査由来。

- **AF-only 検出 (25)**: 代数法則 (monoid / commutativity / functor /
  foldable) + perf/データ移動量 (intermediate-list-chain / string-concat /
  unnecessary-copy) + AF の ruff selection (PERF/SIM/FURB/ANN) — いずれも
  competitor のデフォルト ruff は対象外。
- **competitor-only 検出 (4)**: `missing_optional_handling`,
  `fmap_unit_violation`, `monad_associativity_violation`,
  `monad_right_identity_violation` — pyright が **型エラー** として捕捉
  (= AF の代数法則 check とは別 defect class)。

### 7-2. 修正 outcome モデル — competitor の AI 修正は未測定

competitor の目玉「3 段 AI 自動修正」 pipeline は protected 環境で **発動せず**:

- standalone 起動で `Claude Code not available` を log → competitor は
  `subprocess.run(['claude', ...])` を hard-code、 Windows `CreateProcess` が
  `.cmd` を解決できず AI stage skip。
- AI stage は `claude -p ... --dangerously-skip-permissions` で nested 自律
  agent を spawn する。 これは別リスク class (= permission-bypass された agent
  spawn) で chai の明示承認が必要、 **未実行**。
- **AI stage 不在時、 competitor は `exit 2 + feedback` で 呼び出し元 Claude に
  修正を委任 = AF と同じ outcome model**。

よって competitor の AI pipeline の修正成功率は **未測定** (= honest
limitation)。 AF 自身の修正成功率は §1 で別途実測 (= クリーン再計測 OFF 0/5 →
ON 5/5、 ANN 主導。 旧 20→100%/91.7→100% は撤回 — §1 訂正注記参照)。

### 7-3. 着手した gap 閉鎖

- **`ruf013_implicit_optional`** → AF の ruff select に `RUF013` 追加で閉鎖
  (= sample 検出確認、 `fixed/` ground-truth で FP ゼロ実測。 `RUF` 全体は
  `RUF002` が docstring の ambiguous Unicode `×` を flag するため不採用)。
- **`missing_optional_handling`** → 真の AF gap。 pyright 型 dataflow 解析が
  必要で ruff では不可。 未閉鎖 (= honest limitation)。
- **monad / fmap_unit 法則** → AF Phase 2 coverage gap: `auto_test()`
  単関数 API が monad-pair 法則を skip (= `auto_test_monad_pair` 要、 runner
  未配線)。 Phase 2 既知 limitation。

### 7-4. honest positioning 結論

- AF と competitor は **異なる defect class を狙う**: AF = 代数法則 / perf /
  データ移動量、 competitor = 型エラー (pyright)。 AF の home-field corpus では
  AF が 28 vs 7 でリードするが、 これは一般的優位を過大表現 (= 上記 corpus bias)。
- competitor のデフォルト ruff は **lint で AF より弱い** (= この corpus で 0
  検出) が、 pyright は **AF が持たない型検査の edge** (= AF が見逃す型エラー 4
  件を捕捉、 `missing_optional_handling` は真の gap)。
- AF の **defensible value は Layer 2/3** (= 代数法則 + データ移動量)、
  competitor に counterpart 不在。 ただし立証は *hook-off baseline* 比であって、
  代替 law-checking 手法との比較ではない。
- competitor は **Windows 非対応** (= claude `.cmd` 解決 + cp932 encoding crash)、
  AF は両方 handle 済。
- [README.ja.md](../README.ja.md) の適用域マトリクスは Layer-1-型検査 利用者を
  competitor に正しく振り分けている。

---

## 8. 「任意 base への +α plugin」 — live 合成検証 (2026-05-21)

additive-layer モデル (= AF を Claude Code plugin として任意 base の上に乗せる) を
2 層で検証:

### 8-1. deterministic 合成 (5 tests、 [test_plugin_packaging.py](../samples/violations/tests/test_plugin_packaging.py))
- plugin.json / hooks.json 妥当 + PostToolUse + `${CLAUDE_PLUGIN_ROOT}`
- hook command 解決 + clean file で exit 0
- read-only install 模擬下で history path writable
- **additive 合成**: mock "base" 型検査 hook + AF hook が同一 file (型エラー +
  monoid 違反) で各々別 defect を衝突なく検出。

### 8-2. live plugin load (実 `claude --plugin-dir` session)
`claude --plugin-dir <AF> --print` で違反関数を書かせた。 evidence
([_plugin_verification/live_plugin_load_hook_fire_2026-05-21.json](_plugin_verification/live_plugin_load_hook_fire_2026-05-21.json)):
- session が **AF を plugin として load**、 PostToolUse hook が **live Write で
  発火** — model 自身が *「a PostToolUse plugin hook (algebraic-filter,
  ruff-based) flagged the write with three findings」* と報告。
- anti-pattern history に 3 違反 (PERF401 / ANN001 / ANN201) を実書込 = hook が
  実走した物理証跡。
- **設計哲学も live 実証**: model は PERF401 の修正を user 指示と衝突するとして
  **あえて拒否** = hook は feedback、 LLM 自律は保持 (= constrained decoding でなく
  hook 方式)。

> scope: 単一手動 smoke 実行、 単一 model、 Windows 上。 plugin-load + hook-fire
> + additive-feedback の経路が end-to-end で動くことの実証であり、 統計的主張では
> ない。

---

## 関連参照

- [docs/architecture.ja.md](architecture.ja.md) — 詳細アーキテクチャ
- [docs/algebraic_filter_phase0_pre_reg.md](algebraic_filter_phase0_pre_reg.md) — Phase 0 仮説 + 撤退基準
- [docs/algebraic_filter_project_plan.md](algebraic_filter_project_plan.md) — Phase roadmap
- [docs/_ab_measurement/](_ab_measurement/) — A/B 計測 protocol + log template + 結果
- [samples/violations/manifest.json](../samples/violations/manifest.json) — 仕様層 (= 46 sample のメタデータ)
