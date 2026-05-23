# 限界と境界 (実測)

[English](limitations.md)

algebraic-filter (AF) が「できること / 拡張で届くこと / 構造的に対応不可なこと」 の
honest な実測マップ。 全行が再現可能なプローブに裏付けられている ([再現](#再現))。

> 一行境界: **AF は *構造* (代数法則 / データ移動 / lint) を検証し、 *意図*
> (コードが仕様通りか) は検証しない。** 「`average` は可換であるべき」 は分かるが
> 「`average` が +1 すべきか」 は分からない。

## 検証の正確な意味 (= 何を・どの強さで保証するか)

読み過ぎやすい 2 点を正確化する。

**1. Phase 2 が保証するもの — 正しさでなく「法則」、 かつ名前 gate。**
Phase 2 は関数が代数 *法則* を満たすか (例: `sum` が結合的、 `average` が可換) を
検査する。 *正しさ* は検査しない。 「法則を満たす」 ≠ 「仕様通り」 (= 可換だが
誤って +1 する `average` は pass する)。 保証には 3 条件が同時に必要:

- inferrer が **名前を認識** する (= でなければ法則自体が検査されない);
- 検査されるのは **その名前から推論した法則だけ** (`merge` → 可換律のみ。 `merge`
  の結合律が壊れていても対象外);
- 強さは 2 段階 — **hypothesis sampling = 確率的な確信であって証明でない** (= 稀な
  入力でだけ破れる violation は取りこぼし得る); **CrossHair (opt-in) = 決定論的
  証明、 ただし binary 関数の 14 法則テンプレ中 5 個に限定** (結合律・semigroup 結合・
  可換律・additive identity・binary 冪等。 残り 9 = functor/monad/foldable/eq は
  sampling のみ)。

正確な一文: *Phase 2 は、 認識名の関数が推論された法則を満たすことを、 sampling
信頼度 (該当すれば CrossHair 証明) で保証する。* 強いが条件付き・narrow。

**2. 対応可否は「難易度」でなく defect CLASS で決まる。**
AF が拾えるかはバグの種類で決まり、 難しさではない — 種類が合えば難バグでも拾い、
種類が外れれば易バグでも素通りする。

- **適用クラス内 (拾える = AF の使える適用領域):** 代数法則違反、 データ移動の
  非効率、 lint (PERF/SIM/FURB/F/RUF)、 型 (hybrid mode の pyright)。
- **適用クラス外 (素通り → 別 tool へ):** 一般 logic bug、 security、 並行性、
  仕様意図、 非認識名の法則違反。

代数法則クラスだけは他にない **二重 gate** が乗る: **名前を認識 かつ 推論法則の
違反として顕在化** すること。

## ① できること (= 実測 true positive)

| 能力 | Layer | 備考 |
|---|---|---|
| lint 検出: PERF / SIM / FURB / ANN / F / RUF013 | 1 (ruff) | ruff binary 経由で ~16 ms |
| データ移動量: 中間 list / dict.keys / explicit-copy / 文字列連結 | 3 (AST) | + tracemalloc runtime |
| 代数法則違反 (Monoid / Functor / Monad / …) | 2 (hypothesis) | **keyword 名関数のみ** — ③ 参照 |
| 構造化 feedback → Claude 自己修正 | 4 | クリーン再計測 (2026-05-22): OFF 0/5 → ON 5/5 clean、 ANN 主導、 小 n 自前 task (旧 20→100%/91.7→100% は撤回 — evidence_summary §1 参照) |

AF 自前 46 sample で full-stack 検出 **28/46 (61%)**。

> **中立 corpus check (home-field bias なし)** — 外部 corpus 2 件、 2026-05-21
> 実測、 両者再現可 ([再現](#再現))。 domain 一致度別の honest な gradient:
>
> | Corpus | domain 一致 | 検出 | 備考 |
> |---|---|---|---|
> | [QuixBugs](https://github.com/jkoppel/QuixBugs) (MIT, algo bug 38 件) | **domain 外** (logic bug) | **1/38 = 3%** | floor — `scripts/eval_quixbugs.py` |
> | [perflint](https://github.com/tonybaloney/perflint) (MIT, fixture 8 件) | **domain 内** (perf anti-pattern) | **2/8 = 25%** (= perflint 自身が flag する 6 件中 2/6 = 33%) | `scripts/eval_perflint.py` |
> | AF 自前 46 sample | home-field (co-designed) | **28/46 = 61%** | 上限 |
>
> 3% → 25/33% → 61% が欠陥でなく honest な核心。 QuixBugs の bug は一般 **logic**
> bug で AF の **structure** 軸の構造的外側 (floor)。 perflint は domain 内だが
> AF coverage の *superset* — AF は ruff-ported subset (PERF101/102/401-403) を
> 捕捉するが perflint 固有カテゴリ (use-tuple / loop-invariant-statement /
> memoryview) は対象外。 home-field 61% は co-designed の上限。 AF は構造専用
> verifier であり一般 bug-catcher ではない。
>
> **中立 corpus は de-biasing の役目も果たした**: perflint の `global_usage`
> fixture (`float` accumulator `total += i`) は Phase 3 `string-concat-in-loop`
> rule の *false positive* だった (= 型証跡なしに loop 内の任意 `x += …` に
> 一致していた)。 2026-05-21 に str 証跡 (literal/f-string init・ `str()`・
> `: str` 注釈) gate 追加で修正、 `test_phase3_string_concat_no_fp_on_numeric_accumulator`
> で regression guard。

## ② 拡張で届く (= 作業すれば対応可)

| gap | 作業量 |
|---|---|
| inferrer keyword 被覆 (`mean` / `compute` / `process` が現状 skip) | 小 — keyword 追記 (`add`/`plus`/`total`/`accumulate` は追加済) |
| 代数法則の追加 (現 13 を超えて) | 小〜中 |
| 型検査 (pyright) | **既に対応済** — hybrid / Docker mode 経由 |
| SMT 証明 (CrossHair) で binary 法則 | **opt-in で対応済** (`AF_CROSSHAIR`)。 **14 法則テンプレ中 5 個**を証明 (結合・semigroup 結合・可換・additive identity・binary 冪等 — 2026-05-22 に 3→5 へ厚く)。 コストは **型依存 — int ~0.3s / str/dict/複雑型 ~8s** (2026-05-21 実測)。 int/float/str/dict/分岐/ループ/再帰で動作、 functor/monad/foldable/eq は hypothesis のみ |
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

> **精度修正 — 推測でなく宣言を検証 (P1、 2026-05-22)**: 両エラーの根因は法則を
> *名前から推測* すること。 修正は *宣言された* 法則を検証すること。 デコレータ 2 つ
> (`af_phase2.inferrer`):
> - `@law("commutativity")` — 宣言した法則を **名前非依存** で検証 (= FN 根治: `thingy`
>   のような非認識名でも効く)。
> - `@no_law` (or `@law()`) — 「この関数は法則を持たない」 宣言で名前 heuristic を抑止
>   (= FP 根治: 意図的に非可換な `merge` がもう誤検出されない)。
>
> 宣言は名前 heuristic に優先し、 未宣言は従来どおり fallback (後方互換)。 これで
> Phase 2 は「推測して祈る」から「宣言を検証する」 = 形式手法の契約モデルへ移行。
> `test_af_phase2_declared_laws.py` で固定 (FP抑止 + FN修正 + 優先 + 後方互換)。

> **中立 mutation benchmark (home-field bias なし)、 2026-05-21 実測** —
> `scripts/eval_algebra_mutants.py`。 「algebra 名の関数が法則違反している」公開
> corpus は存在しない (調査で確認) ため、 *機械的 mutation* benchmark とした:
> canonical 演算 (`return a + b` 等) に標準 AOR mutation を適用、 独立な決定論
> oracle + name-gate control 群で評価。 結果 (`sampling` と `sampling+crosshair`
> で同一):
>
> | 測定 | 結果 | 読み |
> |---|---|---|
> | 認識名での検出 (oracle 確定の defect) | **7/7 = 100%** | niche 内では精密かつ完全 |
> | 正解 mutant への false-positive (認識名) | **0/8 = 0%** | 正しいコードを過剰 flag しない |
> | name-gate **control** での検出 (同一 bug・非認識名) | **0/7 = 0%** | 同じ defect も改名で素通り |
> | **name-gate 効果** | **100 pts** | Phase 2 の検出は *全て* 名前依存 |
> | FP-by-intent (意図的に非可換な `merge`) | **2/2 flag** | false-positive 側を定量化 |
>
> honest な要約: Phase 2 は **精密だが完全に名前 gate された** verifier。 認識
> niche 内では機械的 mutant に対し 100%/0% (検出/FP)、 niche 外 (改名 or 設計上
> 意図的な法則破り) では構造的に盲目 or 誤り。 これは QuixBugs 3% floor の代数法則
> 版 — 能力は実在するが niche 限定。 `test_phase2_name_gate_property` で guard。

## 2 つの honest 記録 (A/B 再計測、 2026-05-22)

裁定保留だった点を、 埋もれさせず公開記録として明示する:

1. **A/B 自己修正の看板数字は誤りで、 撤回した。** 旧「+80% / +8.3% pass@1」 は
   `scratch/` で計測していた — `per-file-ignores = ["ALL"]` が `--select` 明示でも
   ruff を無効化するため hook の ruff 層が発火せず — かつプロンプトが欠陥名を明示
   (= hook OFF でも修正)。 クリーン再計測 (機能プロンプト・`_ab_live/`・full select)
   は **OFF 0/5 → ON 5/5 clean (11→0)、 ほぼ型注釈 (ANN) 軸が主** = 有能なモデル上で
   実在するが控えめ・ANN 主導の効果で、 +80% boost ではない。 「% 改善」 でなく
   「保証」 (AF 検出可能な違反を出荷しない) として読む。 詳細訂正:
   [evidence_summary.ja.md](evidence_summary.ja.md) §1。
2. **hook は強制でなく助言。** `exit 2` feedback はユーザー意図と weigh される:
   「このコードを exactly に書け」 と指示すると hook を無視して維持する (実測 ON =
   OFF = 7)。 AF は指示に修正余地がある時に効果を出し、 それ以外では *通知* する
   (= *強制* しない)。

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
# 中立外部 corpus (home-field bias なし) — honest gradient
git clone https://github.com/jkoppel/QuixBugs C:/work/_quixbugs        # domain 外
python scripts/eval_quixbugs.py C:/work/_quixbugs/python_programs      # 1/38 = 3%
git clone https://github.com/tonybaloney/perflint C:/work/_perflint   # domain 内
python scripts/eval_perflint.py C:/work/_perflint/tests/functional    # 2/8 = 25%
# 代数法則軸: 中立 機械的 mutation benchmark (外部 clone 不要)
AF_HOOK_PHASE2_PBT=1 python scripts/eval_algebra_mutants.py           # recognized 100% / control 0%
```

[evidence_summary.ja.md](evidence_summary.ja.md) (positive evidence) +
[hybrid_setup.ja.md](hybrid_setup.ja.md) (= pyright で型 gap を補完) も参照。
