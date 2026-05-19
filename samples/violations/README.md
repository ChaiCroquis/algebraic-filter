# mini-prototype 違反サンプル集 (Phase 0 Day 3-4)

## 目的
AF が covered space としたい違反 pattern を isolating したサンプル集。 各ツール (ruff / CrossHair / hypothesis / memray) の検出能力を matrix 化する Phase 0 の入力。

LayerForge は既存コード snapshot であり、 「AF が想定する違反 pattern を検出できるか」 の正しい計測対象ではない。 サンプル集が H1 (既存ツールカバレッジ ≥70%) の正しい分母。

## 配置
`C:\work\algebraic-filter\samples\violations\` (Phase 1 で拡充予定)

## 含む 7 pattern (Phase 0 minimal、 1 pattern につき 1 sample)

| # | ファイル | 違反 | 期待検出ツール |
|---|---|---|---|
| 1 | `perf401_manual_list_comp.py` | manual list comprehension | ruff PERF401 |
| 2 | `sim103_needless_bool.py` | needless bool conversion | ruff SIM103 |
| 3 | `sim300_yoda_conditions.py` | yoda condition | ruff SIM300 |
| 4 | `ann001_missing_type.py` | missing type annotation | ruff ANN001 |
| 5 | `monoid_associativity_violation.py` | non-associative reduce as "sum" | CrossHair (with contract) / hypothesis @given |
| 6 | `intermediate_list_chain.py` | intermediate list materialization | ruff PERF + memray (Phase 3) |
| 7 | `purity_print_side_effect.py` | impure print in pure-named function | custom rule (Phase 1+) / CrossHair @pure |

## 各サンプルの構造
1 ファイル = 1 違反 isolating
docstring に:
- `violation`: 違反種類
- `expected_detection`: 期待ツール
- `expected_skeleton`: 修正後骨格
- `expected_fix`: 期待修正後コード (ground truth)

## メタデータ集約: [manifest.json](manifest.json)

全サンプルの構造化メタデータは [manifest.json](manifest.json) で管理 (2026-05-19 chai 指示で landing)。 各 entry articulate:

- `id` / `file` / `category` (Layer 1/2/3)
- `violation`: type / name / rule_source
- `expected_detection`: tool / rule_id / **command (実行可能)** / expected_exit_code / expected_output_marker
- `what_to_verify`: **AF が何を検証するのか** (LLM 自己修正サイクル中の検出 + フィードバック)
- `what_is_the_problem`: **何が問題なのか** (なぜこのコードが好ましくないか、 副次影響まで)
- `expected_fix`: skeleton / code_example / **feedback_payload_template** (Phase 4 LLM最適化フィードバック整形の構造)
- `verification_result`: phase_0_actual_detection (PASS / PARTIAL / DEFERRED) + phase_0_evidence (EXECUTED marker 付き)

Phase 1 拡充計画も `planned_additions_phase_1` section に articulate (Functor 則 / Foldable / Monad 則 / 可換律 / 冪等性 / Stream Fusion / 純粋性 variants / 型注釈 variants の 7 カテゴリ、 各 3-5 variation で計 30-50 件目標)。

## TDD 3 層 articulate (chai 指示 2026-05-19 反映)

| 層 | 配置 | 役割 |
|---|---|---|
| 仕様層 | [manifest.json](manifest.json) | 各 sample の expected_detection / what_to_verify / what_is_the_problem / expected_fix を articulate |
| テスト層 | [tests/test_manifest_driven.py](tests/test_manifest_driven.py) | manifest 駆動 pytest parametrize で red-green 検証 |
| Ground truth 層 | [fixed/](fixed/) | 各 sample の修正後コード = AF hook 経由の Claude 自己修正で到達すべき形 |
| 実装層 | (Phase 1) AF hook | Phase 1 で landing、 Phase 1 planned tests が GREEN になる |

実行: `cd algebraic-filter && python -m pytest samples/violations/tests/test_manifest_driven.py -v`

Phase 0 実行結果: **12 passed in 1.51s** (EXECUTED 2026-05-19)。

### TDD growth property

manifest.json の `samples` array に新 entry を追加すれば、 `test_ruff_detects_violation_in_unfixed` / `test_ruff_no_violation_in_fixed` 等の parametrize テストが自動的に増加。 サンプル拡充 = テスト拡充の継続的 path = chai 指示「大量」 への対応。

## 検出能力 matrix の取得方法
各サンプルに対し各ツールを流し、 「期待 violation を出力するか」 を yes/no で記録。
- 分母 = 期待検出 marked pattern 数 (= 7)
- 分子 = 実検出数
- カバレッジ% = 分子 / 分母

## Phase 1 での拡充計画
- 各 pattern につき 3-5 variation (現状: 1 pattern 1 sample)
- 追加 pattern: Functor 則、 単位律、 冪等性、 可換律、 Stream Fusion 系
- hook OFF / hook ON の A/B 計測の入力 (Phase 1 後半 4 日)
