# Contributing to algebraic-filter

AF プロジェクトへの貢献ガイド。 違反 sample 追加 / 法則テンプレ拡張 / hook 改善の 3 軸で articulate。

## Quick principles

1. **違反 sample 本体は不変式**: `samples/violations/*.py` は監査証跡 + ground truth ペア。 修正対象としては扱わず、 「触らず増やす」 設計。
2. **manifest 駆動 TDD growth**: `samples/violations/manifest.json` に entry 追加 → pytest parametrize で test 自動増加。
3. **3 層補完**: Phase 1 (ruff) / Phase 2 (代数法則 PBT) / Phase 3 (データ移動) / Phase 4 (フィードバック整形) はそれぞれ独自 contribution niche、 別 layer の出力を活用する補完設計。

---

## 1. 違反 sample 追加 (= 最頻繁な貢献)

### 手順 (= 3 step + 1 testpartition)

1. **`samples/violations/<id>.py` に違反コード作成**:
   ```python
   """
   violation: <rule_id> (<rule_name>)
   expected_detection: ruff --select=<category>
   expected_skeleton: <fix 骨格>
   expected_fix:
       <fix コード例>
   """
   
   def buggy_function(x):
       # 違反コード
       ...
   ```

2. **`samples/violations/fixed/<id>.py` に修正後コード作成**:
   ```python
   """ground truth (fixed) for <id>"""
   
   def buggy_function(x: int) -> int:
       # 修正後コード (= ruff PASS)
       ...
   ```

3. **`samples/violations/manifest.json` に entry 追加** (= 既存 entry を copy + 値書き換え):
   ```json
   {
     "id": "<id>",
     "file": "<id>.py",
     "category": "Layer 1 静的 (ruff <category>)",
     "violation": {
       "type": "<violation type slug>",
       "name": "<short name>",
       "rule_source": "ruff <rule_id>"
     },
     "expected_detection": {
       "tool": "ruff",
       "rule_id": "<rule_id>",
       "command": "python -m ruff check --select=<category> samples/violations/<id>.py",
       "expected_exit_code": 1,
       "expected_output_marker": "<rule_id>"
     },
     "what_to_verify": "<何を確認するか>",
     "what_is_the_problem": "<何が問題か (= 副次影響まで articulate)>",
     "expected_fix": {
       "skeleton": "<fix 骨格>",
       "code_example": "<fix code one-liner>",
       "feedback_payload_template": {
         "violation_law": "<rule_id>",
         "alternative_skeleton": "<skeleton>",
         "fix_example": "<fix one-liner>"
       }
     },
     "verification_result": {
       "phase_0_actual_detection": "PASS",
       "phase_0_evidence": "ruff <rule_id> 検出 (EXECUTED <date>)"
     }
   }
   ```

4. **test 自動増加確認**:
   ```bash
   python -m pytest samples/violations/tests/test_manifest_driven.py -v
   # → ruff_detects_unfixed[<id>] PASSED
   # → ruff_no_violation_in_fixed[<id>] PASSED
   ```

### 違反タイプ別の追加 path

| 違反タイプ | 追加先 | 必須 articulate |
|---|---|---|
| ruff 検出可能 (PERF/SIM/FURB/ANN/F/B/UP/RUF/C) | manifest entry のみ | expected_detection.tool = "ruff" |
| hypothesis 検出 (代数法則) | manifest + `tests/test_<id>.py` (= @given test) + conftest collect_ignore_glob 更新 | tool = "hypothesis"、 test file path を command に articulate |
| tracemalloc 検出 (データ移動) | manifest + `tests/measure_<id>.py` (= driver) | tool = "tracemalloc"、 driver path を command に articulate |
| custom rule (Phase 1+) | manifest 内 verification_result.phase_0_actual_detection = "DEFERRED" | 検出 tool 未実装、 articulate のみ |

---

## 2. Phase 2 法則テンプレ拡張

### 追加 step

1. **`af_phase2/law_templates.py` に法則 factory 追加**:
   ```python
   def my_law(target_func: Callable, element_strategy: Any = None) -> Callable:
       """説明 (= Haskell QuickCheck-classes 等 reference)"""
       strategy = element_strategy if element_strategy is not None else st.integers(...)
       
       @given(strategy)
       def prop(a: Any) -> None:
           # 法則 articulate
           assert ..., f"my_law failed: ..."
       
       return prop
   ```

2. **`LAW_REGISTRY` dict に登録**:
   ```python
   LAW_REGISTRY: dict[str, Callable] = {
       ...,
       "my_law": my_law,
   }
   ```

3. **`af_phase2/inferrer.py` の `_NAME_TO_LAWS` に keyword 追加**:
   ```python
   _NAME_TO_LAWS: dict[str, list[str]] = {
       ...,
       "my_keyword": ["my_law"],
   }
   ```

4. **`af_phase2/generator.py` の auto_test() で dispatch 追加** (= 該当 if branch):
   ```python
   elif law_id == "my_law":
       prop = template(func, element_strategy)
   ```

### 法則設計の references

- Haskell [`quickcheck-classes`](https://hackage.haskell.org/package/quickcheck-classes) — Eq / Semigroup / Monoid / Functor / Foldable / Traversable / Monad
- Haskell [`checkers`](https://hackage.haskell.org/package/checkers) — morphism properties + standard type classes
- [`Agentic Property-Based Testing` (arXiv 2510.09907)](https://arxiv.org/abs/2510.09907) — LLM agent 経由 property 発見

---

## 3. Phase 3 静的 rule 追加

### 追加 step

1. **`af_phase3/static_checker.py` の `_DataMovementVisitor` に check method 追加**:
   ```python
   def _check_my_rule(self, node: ast.Call) -> None:
       if # 条件:
           self.violations.append(
               StaticViolation(
                   "my-rule-id",
                   node.lineno,
                   f"line {node.lineno}: <message>"
               )
           )
   ```

2. **`visit_Call` 等の visitor entry で呼ぶ**:
   ```python
   def visit_Call(self, node: ast.Call) -> None:
       self._check_my_rule(node)
       # ... existing checks
       self.generic_visit(node)
   ```

3. **`af_phase4/feedback_formatter.py` の `_PHASE3_SKELETON` + `_PHASE3_FIX` に追加** (= Phase 4 統合):
   ```python
   _PHASE3_SKELETON["my-rule-id"] = "<skeleton>"
   _PHASE3_FIX["my-rule-id"] = "<fix one-liner>"
   ```

4. **`samples/violations/<id>.py` + `fixed/<id>.py` + manifest entry 追加** (= 上記 §1 の 手順)。

---

## 4. test 実行

### 全 test suite

```bash
python -m pytest samples/violations/tests/ -v
```

### specific phase

```bash
# Phase 2 coverage
python -m pytest samples/violations/tests/test_af_phase2_coverage.py -v -s

# Phase 3 data movement
python -m pytest samples/violations/tests/test_af_phase3_data_movement.py -v

# Phase 4 feedback
python -m pytest samples/violations/tests/test_af_phase4_feedback.py -v
```

### hook 動作確認 (= subprocess dry-run)

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"samples/violations/perf401_manual_list_comp.py"}}' \
  | python -X utf8 hooks/posttool_af_check.py
echo "EXIT=$?"
# → exit 2 + JSON feedback
```

### Scalpel Docker bridge

```bash
docker build -t af-scalpel -f Dockerfile.scalpel .
python -m pytest samples/violations/tests/test_af_phase3_scalpel_bridge.py -v
```

---

## 5. PR submission

### checklist

- [ ] 新規 violation sample は `samples/violations/` + `fixed/` の対で追加
- [ ] `manifest.json` に entry 追加、 9 fields 全 articulate
- [ ] `pytest samples/violations/tests/` 全 GREEN (= 既存 test も含めて regression なし)
- [ ] hypothesis-target sample なら test file + conftest collect_ignore_glob 更新
- [ ] tracemalloc-target sample なら driver script + manifest command 整合
- [ ] commit message に変更概要 + 影響範囲 articulate

### Issues 例

- 「PERF402 / SIM209 等 新 ruff rule に対応する violation sample 追加」
- 「Traversable 法則テンプレ追加」 (= Phase 2 拡張)
- 「numpy vectorization 機会の静的検出」 (= Phase 3 さらなる拡張)
- 「Scalene + Ollama 統合 demo」 (= Phase 4 LLM proposals 連携の評価)

---

## 関連参照

- [README.ja.md](README.ja.md) — AF 概要
- [USAGE.ja.md](USAGE.ja.md) — 使い方ガイド
- [docs/architecture.ja.md](docs/architecture.ja.md) — 詳細アーキテクチャ
- [samples/violations/manifest.json](samples/violations/manifest.json) — 仕様層 (= 46 sample のメタデータ)
- [docs/troubleshooting.ja.md](docs/troubleshooting.ja.md) — 既知の問題 + 対策
