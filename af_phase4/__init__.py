"""algebraic-filter Phase 4: LLM 最適化フィードバック整形 + anti-pattern 蓄積.

project_plan §6 Phase 4 着手 (1 週間 scope):
- ruff / hypothesis / Phase 3 violation → {violation_location, violation_law,
  alternative_skeleton, fix_example} の構造化 dict
- anti-patterns の自動蓄積機構 (violation history JSON 永続化)
- 同一違反 3 回 → 事前ヒント注入

Modules:
  feedback_formatter: 各 layer violation → 構造化 payload dict 化
  anti_pattern_tracker: 違反 history persistent + pre-emptive hint 生成
"""

__version__ = "0.1.0-phase4-prototype"
