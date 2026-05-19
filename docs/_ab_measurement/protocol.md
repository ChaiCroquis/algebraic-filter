# A/B 計測 protocol (= Phase 1 撤退判定ポイント 1 evidence 取得)

| 項目 | 内容 |
|---|---|
| 目的 | Phase 1 binding 契約「pass@1 改善 +5% / 修正サイクル数 -10%」 (= 撤退判定ポイント 1) の物理 evidence 取得 |
| 対象 | hook OFF vs hook ON の 2 round、 各 round で 5 sample task を別 Claude Code session で実行 |
| 主権 | chai 別 session 実行 (= AI agent 不可)、 結果集計後の判定は chai 主権 |
| 整備日 | 2026-05-20 |

---

## 重要な前提 (= 違反サンプル本体は触らない)

`samples/violations/*.py` は **AF プロジェクト test harness の不変式** (= 監査証跡 + ground truth ペア + 回帰フィクスチャ + Phase 4 baseline)。 A/B 計測では **scratch/_ab_*.py に同等違反コードを Claude に書かせて、 それを修正させる** 形式で実施。 違反サンプル本体は読み取り専用扱い。

---

## 準備

### 1. AF プロジェクト root に移動
```powershell
cd C:\work\algebraic-filter
```

### 2. scratch ディレクトリ確認 (= 既に作成済、 端末作業 dir)
```powershell
Test-Path C:\work\algebraic-filter\scratch
# 期待値: True
```

### 3. .claude/settings.local.json の hook command 確認
```powershell
Get-Content C:\work\algebraic-filter\.claude\settings.local.json
# 期待値: command が "python -X utf8 C:/work/algebraic-filter/hooks/posttool_af_check.py"
# (= forward slash 版、 path mangling 対策済)
```

---

## Round 1: hook OFF run (= baseline 取得)

### Step 1: hook 無効化
```powershell
Move-Item C:\work\algebraic-filter\.claude\settings.local.json `
          C:\work\algebraic-filter\.claude\settings.local.json.disabled
```

### Step 2: 新 Claude Code session 起動
- 別ターミナルで `claude` (= Claude Code CLI) を起動
- session 起動時に settings.local.json が load される (= 今回 disabled で AF hook 無効状態)

### Step 3: 5 sample task を順次依頼
各 task で **修正サイクル数** (= Claude が Edit ツールを呼んだ回数) と **最終到達状態** (= ruff で違反 0 件か) を観察。

#### Task A: PERF401 (manual list comprehension)
```
scratch/_ab_perf401_off.py に以下のコードを書いてください:

def double_positives(data):
    result = []
    for x in data:
        if x > 0:
            result.append(x * 2)
    return result

書いたら、 PERF401 違反を修正してください。
```

#### Task B: SIM103 (needless bool)
```
scratch/_ab_sim103_off.py に以下のコードを書いてください:

def is_positive(x):
    if x > 0:
        return True
    else:
        return False

書いたら、 SIM103 違反を修正してください。
```

#### Task C: SIM300 (yoda condition)
```
scratch/_ab_sim300_off.py に以下のコードを書いてください:

def check_status(status):
    if 0 == status:
        return "ok"
    return "error"

書いたら、 SIM300 違反を修正してください。
```

#### Task D: ANN001 (missing type annotation)
```
scratch/_ab_ann001_off.py に以下のコードを書いてください:

def add(x, y):
    return x + y

書いたら、 ANN001 違反を修正してください。
```

#### Task E: intermediate list chain (AF 独自 rule)
```
scratch/_ab_intermediate_off.py に以下のコードを書いてください:

def transform(data):
    return list(filter(lambda x: x > 0, list(map(lambda x: x * 2, data))))

書いたら、 中間 list materialization を解消するように修正してください。
```

### Step 4: log 取得
各 task で:
- Claude の `Edit` ツール呼び出し回数 (= 修正サイクル数) を session 観察記録
- 最終的に `python -m ruff check --select=PERF,SIM,FURB,ANN,F scratch/_ab_*_off.py` で違反 0 件まで到達したか
- 元 violation 以外の追加 violation が混入したか (= 副作用)

session 終了後、 観察結果を `docs/_ab_measurement/log_hook_off_<YYYY-MM-DD>.md` に landing。

---

## Round 2: hook ON run (= AF hook 効果計測)

### Step 1: hook 再有効化
```powershell
Move-Item C:\work\algebraic-filter\.claude\settings.local.json.disabled `
          C:\work\algebraic-filter\.claude\settings.local.json
```

### Step 2: 新 Claude Code session 起動 (= settings reload)
- 前 session を terminate して新 session 起動 (重要: 同 session 内 settings reload は不可)

### Step 3: 同 5 sample task を別 throwaway files で依頼
- ファイル名を `_off` → `_on` に変える (= scratch/_ab_perf401_on.py 等)
- 内容は同じ違反コード + 修正依頼

### Step 4: log 取得
同じ観察軸:
- 修正サイクル数 (= hook ON では AF feedback で多 step 連鎖の可能性)
- 最終到達状態
- 副作用

session 終了後、 `docs/_ab_measurement/log_hook_on_<YYYY-MM-DD>.md` に landing。

---

## 集計 + 判定 (= chai 主権)

### 集計指標 (5 sample 平均)

| 指標 | hook OFF | hook ON | 差分 |
|---|---|---|---|
| 平均修正サイクル数 | ? | ? | ? |
| 修正成功率 (違反 0 件到達) | ?/5 | ?/5 | ? |
| 副作用検出件数 | ? | ? | ? |
| 全 ruff 違反消失 (= 追加 ANN/型注釈 等含む) | ?/5 | ?/5 | ? |

### Phase 1 撤退判定ポイント 1 との照合

project_plan §6 Phase 1 撤退基準:
- pass@1 改善 +5% 未満 **かつ** 修正サイクル数改善 -10% 未満 → **ガードレール方式の有効性反証 → 全体撤退**

判定:
- [ ] 修正サイクル数: hook ON が hook OFF より **10% 以上少ない** か?
  - Yes → 撤退基準 該当せず、 AF 有効
  - No → 撤退基準該当 評価
- [ ] 修正成功率: hook ON が hook OFF より **5% 以上高い** か?
  - Yes → AF 有効
  - No → 部分検証
- [ ] **両方 No** で 撤退判定発動

---

## 終了後の cleanup

```powershell
# scratch/_ab_*.py を消去 (= 一時 test fixture、 .gitignore 候補)
Remove-Item C:\work\algebraic-filter\scratch\_ab_*.py
```

---

## 関連参照

- [project_plan.md §6 Phase 1 撤退判定ポイント 1](../algebraic_filter_project_plan.md)
- [hooks/posttool_af_check.py](../../hooks/posttool_af_check.py) — Phase 1 + 3 + 4 統合 hook
- [samples/violations/manifest.json](../../samples/violations/manifest.json) — 違反サンプル仕様
- [.claude/settings.local.json](../../.claude/settings.local.json) — hook 登録 (forward slash 版、 path mangling 対策済)
