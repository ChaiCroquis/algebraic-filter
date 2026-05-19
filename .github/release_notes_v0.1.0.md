# algebraic-filter v0.1.0 — initial release

**AI生成コードに対する代数法則レベルの機械検証ガードレール** の initial public release。 Claude Code の PostToolUse hook で AI 生成 Python コードを書き込み時点で自動検証 → 違反時に `exit code 2` + 構造化 feedback で Claude 自己修正サイクルを起動。

## ハイライト

- **46 違反サンプル + 46 ground truth + manifest 駆動 TDD growth**: 仕様層 (manifest.json) → テスト層 (pytest parametrize 自動増加) → ground truth 層 (fixed/) → 実装層 (AF hook) の TDD 4 層構造
- **13 代数法則テンプレ**: Monoid (2) / Functor (2) / Monad (3) / Semigroup (1) / Foldable (1) / Eq (2) / Commutativity / Idempotence (2) — Haskell QuickCheck-classes 参照で Python に移植
- **3 層検証パイプライン**: Layer 1 静的 (ruff 標準 + AF 独自 AST 4 rule) / Layer 2 代数法則 PBT (hypothesis 自動生成) / Layer 3 データ移動量 (tracemalloc + Scalpel Docker bridge)
- **end-to-end Claude 自己修正サイクル**: 多 step feedback chain (PERF401 → ANN201 → ANN001 → PASS) を実 Claude Code session で動作確認

## A/B 計測 evidence (= 真の AF 効果立証)

| niche | hook OFF 完成度 | hook ON 完成度 | delta |
|---|---|---|---|
| AI 生成 raw コード (= 型注釈なし、 5 sample) | 20% | 100% | **+80%** |
| 整理済みコード (= 型注釈完備、 12 sample) | 91.7% | 100% | +8.3% |

両 niche で Phase 1 撤退判定基準 (= pass@1 +5%) クリア = AF 有効性立証。

## Phase 0 H1-H4 binding 仮説 達成

- **H1** 既存ツールカバレッジ ≥70%: 78.6% PASS
- **H2** 差別化軸独立性: VeCoGen は C 対象、 Python skill 層は独立 niche PASS
- **H3** baseline 計測 ≥10 件: LayerForge で 59 件 PASS
- **H4** AET-OS Verified Orchestrator Pattern Layer 3 整合: full PASS 昇格

## Phase 2 法則自動生成 coverage

- hypothesis-target subset **100%** (= single 8/8 + monad pair 3/3 + class-based 3/3)
- 全 46 sample wide で 21.7% (= AF Phase 2 適用 niche は関数名駆動の代数法則系に特化)

## Phase 3 静的 + 実測 coverage

- data-movement subset **100%** (= 5/5: intermediate_list_chain / multi_step / dict_keys_list / explicit_copy / string_concat)
- Scalpel Docker bridge (Python 3.10 isolated env) で関数 CFG 解析動作確認

## install

```bash
git clone https://github.com/ChaiCroquis/algebraic-filter.git
cd algebraic-filter
pip install -e .
```

Claude Code hook 登録は [USAGE.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/USAGE.md#1-claude-code-session-で-hook-を有効化) 参照。

## ドキュメント

- [README.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/README.md) — 概要 + ドキュメント索引
- [USAGE.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/USAGE.md) — 使い方ガイド (4 use case)
- [docs/architecture.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/docs/architecture.md) — 詳細アーキテクチャ (二層構造 / 3 層パイプライン / AET-OS Layer 3 mapping)
- [docs/evidence_summary.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/docs/evidence_summary.md) — A/B 計測 + Phase 0-4 evidence 集約
- [docs/troubleshooting.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/docs/troubleshooting.md) — 既知の問題 + 対策
- [CONTRIBUTING.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/CONTRIBUTING.md) — 違反 sample 追加 / 法則拡張 / PR submission

## 既知の制約

- **Windows path mangling**: hook command path は forward slash 必須 (= backslash escape 剥がれで hook 起動失敗)
- **Scalpel Python 3.13 build 失敗**: typed-ast 依存問題、 Docker container (Python 3.10) で迂回
- **memray Windows native 非対応**: tracemalloc (stdlib) 代替で Layer 3 動作

詳細: [docs/troubleshooting.md](https://github.com/ChaiCroquis/algebraic-filter/blob/main/docs/troubleshooting.md)

## 関連プロジェクト

- **philosophy filter** (方針層): AF はこの物理実装アーム
- **AET-OS** (Agentic Evolutionary Technology - Operating System): AF はその Layer 3 (Verification Layer) 実装

## 設計参照

- Banerjee et al. *CRANE: Reasoning with constrained LLM generation*, 2025 — constrained decoding の trade-off
- Mündler et al. *Type-Constrained Code Generation*, PLDI 2025
- Maaz et al. *Agentic Property-Based Testing*, [arXiv:2510.09907](https://arxiv.org/abs/2510.09907) — AF Phase 4 と相補的方向性
- Haskell QuickCheck-classes / checkers — Phase 2 法則テンプレの設計 reference

## License

MIT — [LICENSE](https://github.com/ChaiCroquis/algebraic-filter/blob/main/LICENSE)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) — Phase 5 OSS 公開
