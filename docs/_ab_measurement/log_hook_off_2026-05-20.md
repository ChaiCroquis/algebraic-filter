# A/B 計測 log — hook OFF round (2026-05-20)

[log_template.md](log_template.md) に基づく round 記録。

---

## Round metadata

| 項目 | 値 |
|---|---|
| Round | hook OFF |
| 実行日 | 2026-05-20 |
| Claude Code session ID (任意) | (本 session、ID 未割当) |
| .claude/settings.local.json の状態 | disabled (= `settings.local.json.disabled` rename 状態、session 起動前確認済) |
| AF hook version (= posttool_af_check.py の sha256 先頭 16 桁) | `c9aa5ccdc33abd33` |

---

## Task 結果

### Task A: PERF401 (manual list comprehension)

| 項目 | 値 |
|---|---|
| ファイル名 | scratch/_ab_perf401_off.py |
| 修正サイクル数 (Edit 呼び出し回数) | **N/A (未実施)** |
| 最終 ruff 違反数 | **N/A (未実施)** |
| 修正成功 | **N/A (未実施)** |
| 副作用 | **N/A (未実施)** |
| メモ | 本 session では Task A は chai から依頼されず、Task B〜E のみ実行。集計時は分母を 4 で扱う or 別 session で補足取得が必要。 |

### Task B: SIM103 (needless bool)

| 項目 | 値 |
|---|---|
| ファイル名 | scratch/_ab_sim103_off.py |
| 修正サイクル数 | 1 |
| 最終 ruff 違反数 (`ruff --select=PERF,SIM,FURB,ANN,F`) | 2 (ANN001 + ANN202、いずれも元コードに pre-existing) |
| 修正成功 (= 指示 rule SIM103 = 0) | Yes (SIM103 自体は完全解消、`--select=SIM103` で exit=0) |
| 修正成功 (= protocol 包括 filter = 0) | No (ANN 系 2 件残存) |
| 副作用 (= 元 violation 以外の追加違反) | なし (残存 ANN001/ANN202 は元コードからの継承で、修正で新規導入したものではない) |
| メモ | Edit 1 回で `if x > 0: return True else: return False` → `return x > 0` に変換。指示 scope (SIM103) のみに集中し、surrounding pre-existing ANN 系には介入しなかった。 |

### Task C: SIM300 (yoda condition)

| 項目 | 値 |
|---|---|
| ファイル名 | scratch/_ab_sim300_off.py |
| 修正サイクル数 | 1 |
| 最終 ruff 違反数 | 2 (ANN001 + ANN202、pre-existing) |
| 修正成功 (= 指示 rule SIM300 = 0) | Yes (`--select=SIM300` で exit=0) |
| 修正成功 (= protocol 包括 filter = 0) | No (ANN 系 2 件残存) |
| 副作用 | なし (同上、ANN は pre-existing) |
| メモ | Edit 1 回で `0 == status` → `status == 0`。最小 diff で yoda 解消。Task B と同じく scope 厳守 behavior。 |

### Task D: ANN001 (missing type)

| 項目 | 値 |
|---|---|
| ファイル名 | scratch/_ab_ann001_off.py |
| 修正サイクル数 | 1 |
| 最終 ruff 違反数 | 1 (ANN202 のみ、pre-existing 且つ指示 scope 外と articulate 済) |
| 修正成功 (= 指示 rule ANN001 = 0) | Yes (`--select=ANN001` で exit=0) |
| 修正成功 (= protocol 包括 filter = 0) | No (ANN202 残存) |
| 副作用 | なし |
| メモ | Edit 1 回で `def add(x, y)` → `def add(x: int, y: int)`。ANN201/ANN202 (戻り値型) は明示的に scope 外として未対処と chai に articulate 済。`int` を採用したのは「numeric add の自然な default」判断。 |

### Task E: intermediate list chain

| 項目 | 値 |
|---|---|
| ファイル名 | scratch/_ab_intermediate_off.py |
| 修正サイクル数 | 1 |
| 最終 ruff 違反数 (`ruff --select=PERF,SIM,FURB,ANN,F`) | 2 (ANN001 + ANN202、pre-existing) |
| Phase 3 AST violation 数 | **未計測** (`af_phase3.static_checker` モジュールが本 session の PYTHONPATH/インストール状態で import 可否未確認、protocol §74 のコマンドは hook ON round 環境前提と推定) |
| 修正成功 (= intermediate list 解消) | Yes (`list(map(...))` materialization 排除、ruff `--select=PERF,SIM,FURB,C4` で exit=0) |
| 修正成功 (= protocol 包括 filter = 0) | No (ANN 系 2 件残存) |
| 副作用 | なし |
| メモ | Edit 1 回で `list(filter(p, list(map(f, data))))` → `[x*2 for x in data if x*2 > 0]` に fusion。述語意味厳密保存 (= `x*2 > 0` のまま) を選択、`if x > 0` への strength reduction は別代数変換のため未適用と articulate 済。 |

---

## 集計 (= 実施 4 task、Task A は未実施で除外)

| 指標 | 値 |
|---|---|
| 平均修正サイクル数 | 1.0 (= 4/4、全 task で Write 後 1 Edit の最短経路) |
| 修正成功率 (= 指示 rule scope) | 4/4 = 100% |
| 修正成功率 (= protocol 包括 filter `PERF,SIM,FURB,ANN,F` = 0) | 0/4 = 0% |
| 副作用合計 (= 修正で新規導入された違反) | 0 |
| AF hook feedback 発動回数 | 0 (hook OFF round のため定義上 0、確認: 本 session 履歴に AF feedback 文字列は不在) |

---

## 観察メモ

### Behavioral observation (= hook OFF 経路の baseline)

1. **scope 厳守 behavior が一貫**: 4 task 全てで「指示された rule のみ」を対象とし、surrounding pre-existing 違反 (特に ANN201/ANN202) には自発介入しなかった。これは hook OFF 経路で AI feedback が無い場合の default 行動として記録に値する。
2. **修正 path が 1 Edit に収斂**: 全 task が Write (初期) → Edit (1 回) の最短経路で完了。hook OFF では追加サイクルを誘発する外部 signal が無いため、最初の Edit が「正解」と判断されればそこで終了する pattern。
3. **代数的変換選択の articulate**: Task E で `x*2 > 0` → `x > 0` strength reduction を「別変換のため未適用」と明示。hook OFF 経路でも内部的 scope 判断は機能している。

### Protocol 解釈の gap (= chai 判断仰ぐ点)

- **template の「最終 ruff 違反数」列**: protocol §117 では `--select=PERF,SIM,FURB,ANN,F` を判定 filter にしているが、各 task 依頼文は対象 rule のみを scope 指定。この乖離により「100% 成功 (scope 解釈) / 0% 成功 (filter 解釈)」と二重の articulate になった。hook ON round と比較する際、どちらの解釈を採用するか chai が事前 alignment 必要。
- **Task A (PERF401) 未実施**: 本 session では依頼が Task B〜E のみで PERF401 が含まれなかった。集計分母を 4 とするか、別 session で Task A 補足取得して 5 に揃えるか chai 判断仰ぐ。

### Phase 3 AST checker の未計測

Task E の Phase 3 行は未計測 (= `af_phase3.static_checker` モジュール import 可否未確認)。hook ON round 環境では hooks/posttool_af_check.py 経由で同モジュールが invoke される設計と推定されるが、hook OFF round 環境では standalone 確認 step が protocol に明示されていない。hook ON round 実行時に同一確認 step を併走するか、独立 verification block を protocol §72 に追記するかは chai 判断領域。
