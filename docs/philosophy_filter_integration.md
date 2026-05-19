# Philosophy Filter Integration — AF を方針層と組み合わせる

AF (algebraic-filter) を **方針層 (philosophy filter)** と組み合わせて、 AI 委任の二層 guardrail として運用する設計 articulate。

[English version](philosophy_filter_integration.en.md)

---

## 二層構造概観

```
┌──────────────────────────────────────────────┐
│ 方針層 (Philosophy Filter)                    │
│   AI に task を委任する前の事前判断:           │
│   4 段決定木 (機械検証可能 / 再現可能 /        │
│                業務領域 / 認知負荷削減)         │
└──────────────────────────────────────────────┘
                  ↓ 「AI 実行可能」 と判定された task
┌──────────────────────────────────────────────┐
│ 物理層 (Algebraic Filter, 本 OSS)              │
│   PostToolUse hook で書き込み時点に自動検証:    │
│   - Phase 1 ruff (PERF/SIM/FURB/ANN/F)        │
│   - Phase 2 代数法則 PBT (hypothesis 自動生成) │
│   - Phase 3 データ移動量 (tracemalloc)         │
│   - Phase 4 構造化 feedback                    │
│   違反検出 → exit 2 + Claude 自己修正サイクル  │
└──────────────────────────────────────────────┘
```

方針層が「**AI に渡してよい task か**」 を判断し、 物理層 (AF) が「**AI が出したコードが正しいか**」 を検証する補完設計。

---

## philosophy filter 4 段決定木 (= 方針層、 一般化版)

AI に task を委任する前に 4 段で評価:

| # | 判定 | AI 委任 | 例 |
|---|---|---|---|
| 1 | **機械検証可能** | ✓ AI 実行 | code 違反検出 / unit test 実行 / lint check (= AF の core domain) |
| 2 | **100% 再現可能な手続き** | ✓ AI 実行 | ファイル整形 / refactoring / docs 生成 |
| 3 | **業務領域** | ✗ user 委任 | release 判断 / 契約解釈 / 受領資料の意味判定 / タイミング判断 |
| 4 | **認知負荷削減に効く** | ✓ AI default 実行、 効かない場合は **タスク自体を捨てる** | 繰り返し作業 = AI 自動化 / 1 回限りの低価値作業 = 廃棄 |

**最上位原理**: 「楽したい」 = 認知負荷削減。 user に判断を投げる行為自体が認知負荷の上昇であり、 philosophy 違反。 検証済み task の口頭再生は不要、 AI が自律進行する path を default にする。

---

## AF を philosophy filter の物理層実装として運用

| 流れ | 方針層 | 物理層 (AF) |
|---|---|---|
| 1. task 受領 | 4 段決定木で評価 | (待機) |
| 2. AI 実行判定 | "AI 実行可能" 判定 → AF に投げる | (待機) |
| 3. AI 書き込み | (待機) | Claude が `Write` / `Edit` で code 生成 |
| 4. 書き込み時点検証 | (待機) | PostToolUse hook 発火 → ruff + AST + 代数法則 + データ移動を verify |
| 5. 違反検出 | (待機) | exit 2 + structured feedback で Claude 自己修正サイクル起動 |
| 6. 修正完了 | 完了報告 (= 機械検証 L1-L4 articulate) | (待機) |
| 7. 業務判定 | "業務領域" の最終判断は user 委任 | (待機) |

→ 方針層 + 物理層 = **AI 委任 guardrail の完成**。

---

## AF 単体使用 vs 二層運用

| use case | AF 単体 | 二層運用 |
|---|---|---|
| 違反検出 (= 書き込み時点) | ✓ | ✓ |
| Claude 自己修正サイクル | ✓ | ✓ |
| task 委任の事前判断 | ✗ | ✓ (= 方針層が事前 filter) |
| 認知負荷削減の最上位原理整合 | (部分) | ✓ (= 完成形) |
| 完了報告の業務判断 articulate | (任意) | ✓ (= 報告 template 含む) |

AF 単体でも価値ある (= ruff + 代数法則 + データ移動 検証)、 ただし二層運用で **AI 委任 guardrail が完成**。

---

## 個人運用への組み込み path

philosophy filter は **個人 OS layer** で運用される設計 = 各 user の運用原理を articulate する領域。 AF user が独自に整備する 4 つの代表 path:

### 1. CLAUDE.md に 4 段決定木 articulate

`~/.claude/CLAUDE.md` (= Claude Code session 起動時に load される universal 運用 doc) に 4 段決定木を articulate:

```markdown
## 判断委任ポリシー

### 4 段決定木 (= AI 委任前の事前判断)

1. 機械検証可能 → AI 実行
2. 100% 再現可能な手続き → AI 実行
3. 業務領域 (release / 契約 / 受領資料 / タイミング) → user 委任
4. 認知負荷削減に効く → AI default 実行 / 効かないなら タスク自体捨てる
```

### 2. Claude Code skill / hook で物理層化

委任判定を Claude Code skill 化 (= chai の例: `secretary` skill) + PostToolUse hook で「user 委任質問」 を block する physical layer 整備:

```python
# 例: hooks/pretool_delegation_guard.py
# tool_name == "AskUserQuestion" に対し、 question text を scan
# 例外 keyword (= 業務領域 / リリース / 契約 / タイミング) なし → block
# 「自律進行で進めるか、 例外 articulate して再 call」
```

### 3. profile 文書として permanent 化

運用原理を profile 文書 (= `~/.claude/profile/cognitive_load_principles.md` 等) に articulate して、 session 起動時に必ず load される flow を整備。

### 4. ADR (Architecture Decision Record) で運用 evolution を articulate

判断委任ポリシーの修正履歴を ADR で articulate (= `~/.claude/decisions/YYYY-MM-DD_*.md`)、 後 review 可能な audit trail として permanent 化。

---

## chai 個人運用例 (= 公開可能 subset)

AF 作者 chai の個人運用例 (= 詳細は個人領域、 一般化原理のみ articulate):

- 4 段決定木は `~/.claude/profile/cognitive_load_principles.md` (= 個人 canonical 哲学保管庫) に articulate
- 委任判定の 3 層強制機構 (= prompt 層 + 物理層 hook + 文脈層) で integrate
- chai 個人運用原理は OSS 化想定外 (= 個人 OS layer)、 ただし AF user が独自に同 pattern を整備する余地

詳細: AF 作者の運用原理は AF プロジェクト範囲外、 各 user が個人 OS layer として独自整備する path。

---

## 関連参照

- [README.md](../README.md) — AF 概要 + 設計哲学
- [docs/architecture.md](architecture.md) — 二層構造 + 3 層検証パイプライン詳細
- [docs/_index/aet_os_reference.md](_index/aet_os_reference.md) — AET-OS Verified Orchestrator Pattern Layer 3 として AF の位置づけ
- [CONTRIBUTING.md](../CONTRIBUTING.md) — AF への貢献ガイド (= sample 追加 / 法則拡張)
