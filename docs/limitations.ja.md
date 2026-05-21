# 限界と境界 (実測)

[English](limitations.md)

algebraic-filter (AF) が「できること / 拡張で届くこと / 構造的に対応不可なこと」 の
honest な実測マップ。 全行が再現可能なプローブに裏付けられている ([再現](#再現))。

> 一行境界: **AF は *構造* (代数法則 / データ移動 / lint) を検証し、 *意図*
> (コードが仕様通りか) は検証しない。** 「`average` は可換であるべき」 は分かるが
> 「`average` が +1 すべきか」 は分からない。

## ① できること (= 実測 true positive)

| 能力 | Layer | 備考 |
|---|---|---|
| lint 検出: PERF / SIM / FURB / ANN / F / RUF013 | 1 (ruff) | ruff binary 経由で ~16 ms |
| データ移動量: 中間 list / dict.keys / explicit-copy / 文字列連結 | 3 (AST) | + tracemalloc runtime |
| 代数法則違反 (Monoid / Functor / Monad / …) | 2 (hypothesis) | **keyword 名関数のみ** — ③ 参照 |
| 構造化 feedback → Claude 自己修正 | 4 | 実測 pass@1 raw 20→100% / curated 91.7→100% (小 n / 自前 corpus) |

AF 自前 46 sample で full-stack 検出 **28/46 (61%)**。

## ② 拡張で届く (= 作業すれば対応可)

| gap | 作業量 |
|---|---|
| inferrer keyword 被覆 (`mean` / `compute` / `process` が現状 skip) | 小 — keyword 追記 (`add`/`plus`/`total`/`accumulate` は追加済) |
| 代数法則の追加 (現 13 を超えて) | 小〜中 |
| 型検査 (pyright) | **既に対応済** — hybrid / Docker mode 経由 |
| SMT 証明 (CrossHair) で結合/可換律 | **opt-in で対応済** (`AF_CROSSHAIR`)。 コストは **型依存 — int は ~0.3s だが str/dict/複雑型は ~8s** (= 2026-05-21 stress test 実測、 当初報告の int 限定 ~0.3s でない)。 int/float/str/dict/分岐/ループ/再帰で動作 (= 当初 claim した「binary int」 より広い)、 identity/functor/monad 法則は保留 |
| 他言語 (TypeScript / Rust) | 大 — 別生態系。 Rust の trait system が代数軸に最適合 |

## ③ 構造的に対応不可 (= 実測 見逃し)

意図的に欠陥コードを投入し hook の exit code を記録 (`AF_HOOK_PHASE2_PBT=1`)。
`exit 0` = 見逃し (clean pass):

| 欠陥プローブ | 結果 |
|---|---|
| off-by-one (`xs[len(xs)]`) | exit 0 — **見逃し** |
| 型エラー (`-> str` だが int 返す)、 AF 単体 | exit 0 — **見逃し** (hybrid なら pyright が拾う) |
| security (`eval(user_input)`) | exit 0 — **見逃し** |
| 並行性 / shared mutable aliasing | exit 0 — **見逃し** |
| **非 keyword 名関数の monoid 違反** (`thingy` で減算) | exit 0 — **見逃し** |
| keyword 名関数の意味バグ (`my_average` で +1) | exit 2 — 検出 (= `average`→可換、 +1 が破った) |

最後の 2 行が核心: AF が意味バグを捕捉するのは **「inferrer が認識する名前の関数で、
バグが代数法則違反として顕在化した時」 だけ**。 関数名を変えれば同じバグが素通りする。

### Phase 2 inferrer は意味理解でなく名前 heuristic

32 個の一般的関数名での keyword 被覆: **16/32 = 50%** が法則推論を起動
(= 2026-05-21 miss-loop iteration2 改善で 12/32=38% から向上: monoid/可換 synonym
追加 + word-boundary 一致)。

- 認識 (✓): `sum` `total` `add` `plus` `accumulate` `merge` `concat` `combine`
  `union` `fold` `reduce` `aggregate` `fmap` `map` `transform` `average`
  (+ synonym `tally` `gather` `collect` `blend` `mix`)
- なお skip (·): `join` `apply` `compose` `mean` `max` `min` `count` `sort`
  `filter` `compute` `process` `handle` `calc` `thingy` …

> **精度修正 (同一変更)**: 一致を **word-boundary (token)** に変更 (substring 廃止)。
> 修正前に実測した誤マッチを解消: `consume`/`summary`/`assume` → `sum` 誤マッチ消滅、
> `remap`/`transformer` → `map`/`transform` 誤マッチ消滅、 `combiner` → `combine`
> 誤マッチ消滅。 = この iteration は **recall 向上 (38→50%) と false-positive 削減を同時達成**。

> **保留 (実測)**: idempotence synonym (`normalize`/`canonicalize`/`dedup`/
> `sanitize`) は**追加せず**。 `idempotence` 法則 template が任意型 unary に robust
> でなく **ERROR (= clean PASS でない)** を出すため = false-positive 化。 template
> 堅牢化まで保留。

帰結 — Phase 2 は **両側エラー**:
- **false negative**: 非認識名の真の法則違反 (例: 非結合的な `add`) を見逃す。
- **false positive**: 正しく `merge` と名付けたが意図的に非可換 (= 左優先 merge) な
  関数を誤検出しうる。

## honest な要点

AF の価値は **自動の構造ガードレール**。 仕様/意図の正しさは test・人間 review・
(型は) pyright の役割のまま。 ここでの「対応不可」 は欠陥でなく **意図的な niche 境界**:
AF は構造軸を niche 内で確実に守り、 それ以外は適切な tool に振り分ける。

## 再現

```bash
# false-negative プローブ (= AF の defect class 外の buggy コード)
# inferrer keyword 被覆
# 両者 2026-05-21 に inline 実行 (プローブ code は本 commit message に記録)
python -m pytest samples/violations/tests/   # positive 側被覆 (117 passed)
python scripts/compare_competitor.py          # AF vs competitor 検出 (28/46 vs 7/46)
python scripts/miss_loop.py                   # miss 切り分け: clustered (一括修正可) vs hard tail 比率
python scripts/miss_loop.py my_corpus.json    # ...任意の labeled corpus で (= 内蔵 corpus の co-design bias を回避)
```

[evidence_summary.ja.md](evidence_summary.ja.md) (positive evidence) +
[hybrid_setup.ja.md](hybrid_setup.ja.md) (= pyright で型 gap を補完) も参照。
