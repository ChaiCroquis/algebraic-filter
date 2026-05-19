# A/B 計測 log template

各 round 実行後、 chai が以下 template を copy + 値を埋めて `log_hook_<off|on>_<YYYY-MM-DD>.md` として landing。

---

## Round metadata

| 項目 | 値 |
|---|---|
| Round | (hook OFF / hook ON) |
| 実行日 | YYYY-MM-DD |
| Claude Code session ID (任意) | |
| .claude/settings.local.json の状態 | (active / disabled) |
| AF hook version (= posttool_af_check.py の sha256) | `python -c "import hashlib, pathlib; print(hashlib.sha256(pathlib.Path('hooks/posttool_af_check.py').read_bytes()).hexdigest()[:16])"` |

---

## Task 結果

### Task A: PERF401 (manual list comprehension)

| 項目 | 値 |
|---|---|
| ファイル名 | scratch/_ab_perf401_(off/on).py |
| 修正サイクル数 (Edit 呼び出し回数) | ? |
| 最終 ruff 違反数 (`ruff --select=PERF,SIM,FURB,ANN,F`) | ? |
| 修正成功 (= 違反 0) | (Yes / No) |
| 副作用 (= 元 violation 以外の追加違反) | (なし / あり: ...) |
| メモ | |

### Task B: SIM103 (needless bool)

| 項目 | 値 |
|---|---|
| ファイル名 | scratch/_ab_sim103_(off/on).py |
| 修正サイクル数 | ? |
| 最終 ruff 違反数 | ? |
| 修正成功 | (Yes / No) |
| 副作用 | |
| メモ | |

### Task C: SIM300 (yoda condition)

| 項目 | 値 |
|---|---|
| ファイル名 | scratch/_ab_sim300_(off/on).py |
| 修正サイクル数 | ? |
| 最終 ruff 違反数 | ? |
| 修正成功 | (Yes / No) |
| 副作用 | |
| メモ | |

### Task D: ANN001 (missing type)

| 項目 | 値 |
|---|---|
| ファイル名 | scratch/_ab_ann001_(off/on).py |
| 修正サイクル数 | ? |
| 最終 ruff 違反数 | ? |
| 修正成功 | (Yes / No) |
| 副作用 | |
| メモ | |

### Task E: intermediate list chain

| 項目 | 値 |
|---|---|
| ファイル名 | scratch/_ab_intermediate_(off/on).py |
| 修正サイクル数 | ? |
| 最終 ruff 違反数 | ? |
| Phase 3 AST violation 数 (`python -c "from af_phase3.static_checker import check_file; print(len(check_file('scratch/_ab_intermediate_(off/on).py')))"`) | ? |
| 修正成功 | (Yes / No) |
| 副作用 | |
| メモ | |

---

## 集計 (= 5 task 平均)

| 指標 | 値 |
|---|---|
| 平均修正サイクル数 | ? |
| 修正成功率 | ?/5 = ?% |
| 副作用合計 | ? |
| AF hook feedback 発動回数 (hook ON のみ) | ? |

---

## 観察メモ (= chai 自由記述)

(Claude の behavior、 hook feedback の質、 想定外の動作、 etc.)
