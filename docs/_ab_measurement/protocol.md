# A/B 計測 protocol v2 (= in-vivo 効果計測、 answer-leak 排除版)

| 項目 | 内容 |
|---|---|
| 目的 | AF hook が「Claude が気づいていない違反を指摘し自己修正させる」 in-vivo 効果を立証する evidence 取得 |
| 対象 | hook OFF vs hook ON の 2 round、 各 round 5 sample task を別 Claude Code session で実行 |
| 主権 | chai 別 session 実行 (= AI agent 不可)、 結果集計後の判定は chai 主権 |
| 整備日 | v1 2026-05-20 / **v2 改訂 2026-05-22** |

---

## v2 で何を変えたか (= v1 の致命的 bug)

v1 の各タスクは「コードを書いて、 **そのあと PERF401 違反を修正してください**」 と
**欠陥名を明示**していた。 結果、 hook OFF でも Claude が 1 Edit で直してしまい
(2026-05-20 実測: OFF = 平均 1.0 cycle / 成功 4/4)、 **hook が価値を出す余地が
無かった** (= ON vs OFF の差が原理的に出ない設計 bug)。

AF hook の真価は **「Claude が気づいていない違反を AF が指摘して自己修正させる」**
点にある。 よって v2 では **タスク文から欠陥名・修正指示を完全に削除**し、 「ただ
コードを書いてもらう」 だけにする。 すると:

- **OFF**: Claude は書いて終了 → 違反がそのまま **出荷される** (= 残存違反 > 0)
- **ON**: hook が exit 2 + feedback → Claude が **自己修正** → 違反消失 (= 残存違反 0)

→ **主指標 = 最終ファイルに残る AF 違反数 (OFF vs ON)**。 ON < OFF なら AF が実コード
品質を in-vivo で改善する立証になる。 修正サイクル数は副指標。

> v1 で取得した `log_hook_off_2026-05-20.md` は **answer-leak 設計のため無効**。
> v2 では OFF round も neutral prompt で取り直す。

---

## 重要な前提 (= 違反サンプル本体は触らない)

`samples/violations/*.py` は AF test harness の不変式 (監査証跡 + ground truth +
回帰フィクスチャ + Phase 4 baseline)。 A/B では `scratch/_ab_*.py` に Claude が
書く throwaway で実施。 違反サンプル本体は読み取り専用扱い。

---

## 準備 (= 2026-05-22 実機確認済、 すべて green)

```powershell
# 1. AF root + scratch 存在
cd C:\work\algebraic-filter
Test-Path scratch                              # 期待: True

# 2. hook 登録 (= 本 session で発火している本体)
Get-Content .claude\settings.local.json
# 期待: command = "python -X utf8 C:/work/algebraic-filter/hooks/posttool_af_check.py"

# 3. chai env config (CrossHair ON)
Get-Content .algebraic-filter.json             # 期待: { "crosshair_verify": true }
```

---

## Round 1: hook OFF run (= baseline)

### Step 1: hook 無効化
```powershell
Move-Item C:\work\algebraic-filter\.claude\settings.local.json `
          C:\work\algebraic-filter\.claude\settings.local.json.disabled
```

### Step 2: 新 Claude Code session 起動
別ターミナルで `claude` を起動 (= settings.local.json が load される。 今回 disabled で
AF hook 無効)。 **同 session 内 settings reload は不可**、 必ず新 session。

### Step 3: 5 タスクを順次依頼 (★修正指示なし = neutral prompt)

[tasks_neutral.md](tasks_neutral.md) の Task A〜E をそのまま貼り付け
(`<round>` = `off`)。 各タスクは **「このコードを scratch/_ab_X_off.py に書いて」だけ**で、
欠陥への言及は一切しない。

### Step 4: 各タスクの残存違反を計測
```powershell
# ruff (PERF/SIM/FURB/ANN/F) 残存数
python -m ruff check --select=PERF,SIM,FURB,ANN,F scratch\_ab_perf401_off.py
# Phase 3 AST 残存数 (intermediate task で特に重要)
python -X utf8 -c "from af_phase3.static_checker import check_file; print(len(check_file(r'scratch\_ab_intermediate_off.py')))"
```
記録: (a) Claude の Edit 呼び出し回数, (b) 残存 AF 違反数, (c) 副作用。
→ [log_template.md](log_template.md) を copy し `log_hook_off_<YYYY-MM-DD>.md` に landing。

---

## Round 2: hook ON run

### Step 1: hook 再有効化
```powershell
Move-Item C:\work\algebraic-filter\.claude\settings.local.json.disabled `
          C:\work\algebraic-filter\.claude\settings.local.json
```

### Step 2: 新 session 起動 (= 前 session terminate 必須)

### Step 3: 同 5 タスクを `<round>` = `on` で依頼
- ファイル名を `_off` → `_on` に変えるだけ、 タスク文は同一 (neutral prompt)。
- hook が違反を exit 2 で指摘 → Claude が自己修正する過程を観察。

### Step 4: 残存違反を同コマンドで計測 (`_off` → `_on`)
→ `log_hook_on_<YYYY-MM-DD>.md` に landing。 hook feedback 発動回数も記録。

---

## 集計 + 判定 (= chai 主権)

| 指標 (5 task 平均) | hook OFF | hook ON | 差分 |
|---|---|---|---|
| **残存 AF 違反数 (主指標)** | ? | ? | ? |
| 修正サイクル数 (副) | ? | ? | ? |
| 副作用検出件数 | ? | ? | ? |
| hook feedback 発動回数 | 0 (定義上) | ? | — |

判定軸:
- [ ] **残存違反: ON が OFF より少ないか?** (= AF が出荷品質を改善したか) — 主判定
- [ ] 副作用: ON で新規違反が増えていないか? (= feedback が悪さしないか)
- 主指標で ON < OFF なら **in-vivo 有効性 立証**。 差が無ければ「neutral prompt でも
  Claude が元々 clean に書く = AF の marginal value 小」 と honest に記録 (= 撤退でなく
  適用領域の精緻化)。

---

## 終了後 cleanup
```powershell
Remove-Item C:\work\algebraic-filter\scratch\_ab_*.py
```

---

## 関連参照
- [tasks_neutral.md](tasks_neutral.md) — 貼り付け用 neutral prompt 一式
- [log_template.md](log_template.md) — round 記録テンプレ
- [project_plan.md §6 Phase 1 撤退判定ポイント 1](../algebraic_filter_project_plan.md)
- [hooks/posttool_af_check.py](../../hooks/posttool_af_check.py)
