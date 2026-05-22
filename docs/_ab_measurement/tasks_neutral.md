# A/B 計測 — 貼り付け用 neutral prompt 一式

各タスクを **そのまま Claude Code session に貼り付ける**。 `<round>` を `off` / `on` に
置換するだけ。 **欠陥名・修正指示は一切含めない**(= answer-leak 排除、protocol v2)。

OFF round では `off`、ON round では `on` を使う。 OFF は hook 無効なので違反がそのまま
残り、ON は hook が指摘して Claude が自己修正する — その差が evidence。

---

## Task A (PERF401: manual list build)

```
scratch/_ab_perf401_<round>.py に、以下のコードをそのまま書いてください。

def double_positives(data):
    result = []
    for x in data:
        if x > 0:
            result.append(x * 2)
    return result
```

## Task B (SIM103: needless bool)

```
scratch/_ab_sim103_<round>.py に、以下のコードをそのまま書いてください。

def is_positive(x):
    if x > 0:
        return True
    else:
        return False
```

## Task C (SIM300: yoda condition)

```
scratch/_ab_sim300_<round>.py に、以下のコードをそのまま書いてください。

def check_status(status):
    if 0 == status:
        return "ok"
    return "error"
```

## Task D (ANN001: missing type annotation)

```
scratch/_ab_ann001_<round>.py に、以下のコードをそのまま書いてください。

def add(x, y):
    return x + y
```

## Task E (intermediate list chain: AF 独自 Phase 3 rule)

```
scratch/_ab_intermediate_<round>.py に、以下のコードをそのまま書いてください。

def transform(data):
    return list(filter(lambda x: x > 0, list(map(lambda x: x * 2, data))))
```

---

## 計測コマンド (各タスク後)

```powershell
# ruff 残存
python -m ruff check --select=PERF,SIM,FURB,ANN,F scratch\_ab_<name>_<round>.py
# Phase 3 AST 残存 (Task E で特に重要)
python -X utf8 -c "from af_phase3.static_checker import check_file; print(len(check_file(r'scratch\_ab_<name>_<round>.py')))"
```

## 観察ポイント
- OFF: Claude は書いて終わるはず → 違反が残る (期待: 残存 > 0)
- ON: hook が exit 2 + feedback → Claude が自己修正 → 残存 0 + Edit 連鎖
- 各タスクで Edit 呼び出し回数 / 残存違反数 / 副作用 を記録 → log に転記
