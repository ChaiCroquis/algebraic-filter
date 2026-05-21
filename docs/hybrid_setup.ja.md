# ハイブリッド構築 — base 品質ツール + algebraic-filter (+α)

[English](hybrid_setup.md)

**claude-code-quality-hook (base) + algebraic-filter (+α)** を併用し、 各 `.py`
書込で両方が発火して各々の defect class を捕捉する構成の手順:

- **base** ([claude-code-quality-hook](https://github.com/dhofheinz/claude-code-quality-hook)):
  ruff デフォルト + **pyright 型検査** + (任意) 3 段 AI 修正。
- **+α** (algebraic-filter): 代数法則 PBT (Layer 2) + データ移動量 (Layer 3) =
  pyright/ruff には見えない defect class。

両者は相補的: 実測で検出 defect が **重複しない** (= 型エラー vs 代数法則違反) ため、
併用しても無駄がない。 end-to-end 検証済 ([検証](#検証) 参照)。

> **最速 path**: [examples/hybrid-starter/](../examples/hybrid-starter/) を copy
> して `setup_hybrid` を実行。 Docker があれば **Docker mode (host 依存ゼロ)**、
> なければ **venv mode** を自動選択する。 以下の手順は venv mode の手動版。

## Docker mode (host 依存ゼロ)

host に python/node/pip を一切入れたくなければ、 雛型が AF +α **と** pyright を
同梱した `af-hybrid` image を build し、 単一 PostToolUse hook として動かす (=
host→container path 翻訳込み)。 Docker 検出時 `setup_hybrid` が自動配線、 host 要件
は Docker のみ。 2026-05-21 検証: container hook が `exit 2` + AF (`monoid_identity`)
+ base (pyright `reportReturnType`) 両検出
([_plugin_verification/docker_hybrid_hook_fire_2026-05-21.json](_plugin_verification/docker_hybrid_hook_fire_2026-05-21.json))。

## 前提 (venv mode)

venv を使い global 導入を避ける (= pyright は pip で入る、 global `npm` 不要):

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1   |   macOS/Linux: source .venv/bin/activate
pip install ruff hypothesis pyright   # ruff: 両ツール / hypothesis: AF Phase 2 / pyright: base 型検査
```

> `claude` は **venv 有効化 shell から起動**すること (= 両 hook は bare `python`
> を呼ぶので、 venv の依存を継承させる)。

## Step 1 — base: claude-code-quality-hook

```bash
git clone https://github.com/dhofheinz/claude-code-quality-hook
cd claude-code-quality-hook
./setup.sh        # .claude/settings.json hook + .quality-hook.json を生成
```

推奨 base config (`.quality-hook.json`) — **検出 + block のみ** (= AI 修正段を
無効化、 nested `claude` agent spawn + Windows 非対応を回避):

```json
{
  "type_checking": { "enabled": true },
  "claude_code": { "enabled": false }
}
```

> **Windows**: base は `✓` 出力時に cp932 で crash する。 Claude Code (と hook) を
> `PYTHONUTF8=1` を環境にセットして起動すること。

これで base hook が project の `.claude/settings.json` に配線される。

## Step 2 — +α: algebraic-filter plugin

対象 project の Claude Code session 内で:

```
/plugin marketplace add ChaiCroquis/algebraic-filter
/plugin install algebraic-filter@algebraic-filter-marketplace --scope local
```

`--scope local` で AF を **この project だけ** に限定 (= 全 project 発火を避ける)。
任意 — 代数法則 runtime を有効化 (= 書込 module を実行、 trusted / 書き捨て領域のみ):

```json
// project root の .algebraic-filter.json
{ "phase2_runtime": true }
```

## Step 3 — 合成挙動

両 hook とも `Write|Edit|MultiEdit` の `PostToolUse`。 base は
`.claude/settings.json`、 AF は plugin hook。 Claude Code は各 edit で **両方** を
走らせる (= settings hook + plugin hook が合成、 互いに override しない):

- **型エラー** → base が block (pyright) + feedback
- **代数法則 / データ移動量** defect → AF が block + 構造化 feedback
- **両方** 持つ file → 両 hook 発火、 各々の defect class を報告

## 注意点

- **冗長性**: 両方発火時、 Claude は 2 つの feedback block を見る。 衝突ではなく
  text 量増。 (うるさければ base の rule を絞るか AF の `feedback_shape: minimal`)
- **hook 順序は非保証** (= settings hook と plugin hook 間)。 検出+block 用途では無関係。
- **ruff が 2 回走る** (base: デフォルト / AF: PERF/SIM/FURB/ANN/F/RUF013) = rule
  set が違うので軽微な二重実行 (= ruff binary 経由で各 ~16ms)。
- **Windows**: base 用に `PYTHONUTF8=1` を維持。

## 検証

本ハイブリッドは 2026-05-21 実測 (= mock でなく実 competitor hook)。 型エラー +
`monoid_identity` 違反を両方持つ file に対し:

- base (competitor) → `exit 2`、 pyright が
  `reportReturnType: "None" is not assignable to "int"` 検出
- AF (+α) → `exit 2`、 Phase 2 が `monoid_identity at target.py:4` 検出
  (history 記録: [_plugin_verification/hybrid_competitor_plus_af_2026-05-21.json](_plugin_verification/hybrid_competitor_plus_af_2026-05-21.json))

両者が独立に発火し各々の defect class を捕捉 = +α layer が base の上に綺麗に合成。
[evidence_summary.ja.md](evidence_summary.ja.md) §8 も参照。
