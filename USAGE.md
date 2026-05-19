# USAGE — algebraic-filter 使い方ガイド

AF の主要 use case 4 つを順に articulate:

1. [Claude Code session で hook を有効化](#1-claude-code-session-で-hook-を有効化)
2. [手動で violation 検出 (CLI)](#2-手動で-violation-検出-cli)
3. [Phase 2 代数法則 PBT 自動生成 API](#3-phase-2-代数法則-pbt-自動生成-api)
4. [A/B 計測 で AF 効果を実測](#4-ab-計測-で-af-効果を実測)

---

## 1. Claude Code session で hook を有効化

### 1-1. install

```bash
git clone https://github.com/ChaiCroquis/algebraic-filter.git
cd algebraic-filter
pip install -e .
```

### 1-2. project-local hook 登録

AF プロジェクト直下に `.claude/settings.local.json` を作成 (= 既存 file あれば merge):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python -X utf8 /absolute/path/to/algebraic-filter/hooks/posttool_af_check.py"
          }
        ]
      }
    ]
  }
}
```

**Windows ユーザー必須**: command path は **forward slash** (`/`) で記述。 backslash (`\`) は bash 経由で `\w \a \h \p` escape 剥がれ → path mangling で hook 起動失敗。 詳細: [docs/troubleshooting.md](docs/troubleshooting.md)

### 1-3. Claude Code session 起動 + 動作確認

```bash
# AF プロジェクト or AF を使う別プロジェクトで:
cd /path/to/your-project
claude
```

session 内で Claude に違反コードを書かせる:

```
scratch/test_hook.py に以下のコードを書いて、 PERF401 を修正してください:

def double_positives(data):
    result = []
    for x in data:
        if x > 0:
            result.append(x * 2)
    return result
```

期待動作:
1. Claude が Write tool で scratch/test_hook.py 作成
2. AF hook 発火 → ruff PERF401 検出 → exit 2 + structured feedback
3. Claude が hook feedback (= skeleton + fix_example) を parse して list comprehension に修正
4. Claude が Edit で再度 hook 起動 → 残違反 (= ANN001/ANN201 等) 検出 → 再 feedback
5. Claude が型注釈追加 → hook PASS (exit 0)

---

## 2. 手動で violation 検出 (CLI)

### 2-1. Phase 1 (ruff 統合)

```bash
python -m ruff check --select=PERF,SIM,FURB,ANN,F samples/violations/perf401_manual_list_comp.py
```

### 2-2. Phase 3 (AF 独自 AST rule)

```python
from af_phase3.static_checker import check_file

violations = check_file("samples/violations/intermediate_list_chain.py")
for v in violations:
    print(f"{v.rule_id} (line {v.line}): {v.message}")
```

検出 rule (4 種):
- `intermediate-list-chain` — `list(map/filter(..., list(...)))`
- `dict-keys-list` — `list(d.keys())` / `list(d.values())`
- `explicit-copy` — `.copy()` method call
- `string-concat-in-loop` — for-body 内 `result += x`

### 2-3. Phase 3 runtime tracemalloc

```python
from af_phase3.runtime_checker import check_threshold
from samples.violations.intermediate_list_chain import transform

data = list(range(10000))
violation, measurement = check_threshold(transform, data, max_bytes=100*1024)
if violation:
    print(f"{violation.rule_id}: {violation.measured_bytes} bytes > {violation.threshold_bytes}")
print(f"function {measurement.function_name}: {measurement.total_size_bytes} bytes, {measurement.allocation_count} allocations")
```

### 2-4. Phase 4 structured feedback formatter

```python
from af_phase4.feedback_formatter import combine_violations
from af_phase3.static_checker import check_file

ruff_output = "..."  # ruff --select=PERF,... の出力
phase3_violations = check_file("path/to/file.py")
combined = combine_violations(ruff_output, phase3_violations, "path/to/file.py")
for v in combined:
    print(f"[{v['layer']}] {v['violation_law']} at {v['violation_location']}")
    print(f"  skeleton: {v['alternative_skeleton']}")
    print(f"  fix: {v['fix_example']}")
```

---

## 3. Phase 2 代数法則 PBT 自動生成 API

### 3-1. 単 callable 関数

```python
from af_phase2.generator import auto_test
from samples.violations.monoid_associativity_violation import my_sum

results = auto_test(my_sum)
for r in results:
    print(f"law={r.law_id} status={r.status}")
    if r.error:
        print(f"  error: {r.error}")
```

期待出力:
```
law=monoid_identity status=FAIL
  error: my_sum([1])=−1, sum=1
law=monoid_associativity status=FAIL
  ...
```

法則推論基準 (= 関数名 keyword + 型シグネチャ):
- `sum / fold / aggregate / reduce` → `monoid_identity` + `monoid_associativity`
- `map / fmap / transform` → `functor_identity` + `functor_compose`
- `merge / average / intersect / union / combine` → `commutativity`

### 3-2. Monad pair (pure + bind)

```python
from af_phase2.generator import auto_test_monad_pair
from samples.violations.monad_left_identity_violation import pure, bind

results = auto_test_monad_pair(pure, bind)
# → monad_left_identity / monad_right_identity / monad_associativity 3 法則
```

### 3-3. class-based 冪等性

```python
from af_phase2.generator import auto_test_class_idempotence
from samples.violations.idempotence_violation_in_named_set_add import FakeSet

results = auto_test_class_idempotence(FakeSet, "add")
```

---

## 4. A/B 計測 で AF 効果を実測

### 4-1. 自動実走 (= nested claude --print 経由)

5 task × 2 round:
```bash
python scripts/ab_automation.py
```

12 sample × 2 round (= manifest 駆動):
```bash
python scripts/ab_automation_wide.py
```

結果: `docs/_ab_measurement/log_auto_*.json` に landing。

### 4-2. 手動 A/B (= chai 別 session で実走)

詳細手順: [docs/_ab_measurement/protocol.md](docs/_ab_measurement/protocol.md)

```powershell
# Round 1 hook OFF
Move-Item .claude\settings.local.json .claude\settings.local.json.disabled
claude   # → 5 task 順次依頼

# Round 2 hook ON
Move-Item .claude\settings.local.json.disabled .claude\settings.local.json
claude   # → 同 5 task を _on suffix で repeat
```

log template: [docs/_ab_measurement/log_template.md](docs/_ab_measurement/log_template.md)

### 4-3. 計測指標 + 判定

| 指標 | 計測方法 | Phase 1 撤退判定基準 |
|---|---|---|
| pass@1 改善 (= 全 layer 修正成功率) | ruff `--select=PERF,SIM,FURB,ANN,F` で違反 0 件到達数 | +5% 以上で AF 有効 |
| 修正サイクル数 | Claude の Edit ツール呼び出し回数 | -10% 以上で AF 有効 |
| 副作用検出 | 元 violation 以外の追加違反混入数 | 0 件 (= ideal) |

判定: **pass@1 +5% 改善 + 修正サイクル -10% 改善 の両方未達** → 撤退。 片方達成 = AF 有効。

---

## 関連参照

- [README.md](README.md) — AF 概要 + 設計哲学
- [docs/architecture.md](docs/architecture.md) — 詳細アーキテクチャ
- [docs/evidence_summary.md](docs/evidence_summary.md) — A/B 計測 + 各 Phase evidence
- [docs/troubleshooting.md](docs/troubleshooting.md) — 既知の問題 + 対策
- [CONTRIBUTING.md](CONTRIBUTING.md) — 違反 sample 追加 / TDD growth
