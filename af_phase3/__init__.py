"""algebraic-filter Phase 3: データ移動量フィードバック.

project_plan §6 Phase 3 着手 (2 週間 scope):
- 静的: 中間 list / 不要 copy / 連鎖 comprehension の検出 (ruff PERF 系拡張)
- 実測: tracemalloc allocation 計測 + 閾値判定
- 閾値判定 → Claude 向け構造化フィードバック

Modules:
  static_checker: Python AST visitor で data movement violations を検出
  runtime_checker: tracemalloc で allocation 計測 + 閾値判定
"""

__version__ = "0.1.0-phase3-prototype"
