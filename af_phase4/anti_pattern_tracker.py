"""Phase 4: anti-pattern 自動蓄積 + 同一違反 N 回検出で事前 hint.

violation history を JSON file に永続化、 hook 起動時に rule_id ごとの累計件数を
articulate して、 threshold (default 3) 超過時に pre-emptive hint message を返す.

これにより Claude が「同種違反を繰り返している」 という meta-context を取得し、
自己修正サイクルが accelerate される (= Phase 4 LLM 最適化フィードバックの core).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_HOOK_DIR = Path(__file__).resolve().parent.parent / "hooks"
DEFAULT_HISTORY_PATH = _HOOK_DIR / "af_violation_history.json"
PREEMPTIVE_HINT_THRESHOLD = 3
MAX_HISTORY_ENTRIES = 1000

# Per-rule threshold override (= rule_id ごとに別 threshold を設定可能).
# 設計動機: 重い違反 (= 修正コスト大、 代数法則違反等) は早めに hint、
# 軽い違反 (= ANN001 等の型注釈) は default threshold で十分。
# default 値 (= PREEMPTIVE_HINT_THRESHOLD = 3) を override する場合のみ articulate。
RULE_THRESHOLD_OVERRIDES: dict[str, int] = {
    # 代数法則違反 (= Phase 2) は意味的影響が大きいため 2 回目で hint
    "monoid_associativity": 2,
    "monoid_identity": 2,
    "semigroup_associativity": 2,
    "functor_identity": 2,
    "functor_compose": 2,
    "monad_left_identity": 2,
    "monad_right_identity": 2,
    "monad_associativity": 2,
    "commutativity": 2,
    "idempotence_state_int": 2,
    "idempotence_class": 2,
    # データ移動量違反 (= Phase 3) は perf 影響大、 2 回目で hint
    "intermediate-list-chain": 2,
    "string-concat-in-loop": 2,
    # 軽微違反は default threshold (= 3) のままで articulate 不要
    # PERF401 / SIM103 / SIM108 / ANN001 / ANN201 / F401 等
}


def _resolve_threshold(rule_id: str, default: int) -> int:
    """rule_id に対する有効 threshold を返す (override > default)."""
    return RULE_THRESHOLD_OVERRIDES.get(rule_id, default)


def record_violations(
    rule_ids: list[str],
    file_path: str,
    *,
    history_path: Path = DEFAULT_HISTORY_PATH,
) -> dict[str, int]:
    """違反 rule_id list を history に追記、 各 rule_id の累計件数 dict を返す."""
    history = _load_history(history_path)
    now = datetime.now().isoformat(timespec="seconds")
    for rule_id in rule_ids:
        history.append({"timestamp": now, "rule_id": rule_id, "file_path": file_path})
    # 累積 trim
    if len(history) > MAX_HISTORY_ENTRIES:
        history = history[-MAX_HISTORY_ENTRIES:]
    _save_history(history, history_path)
    counts: dict[str, int] = {}
    for rule_id in rule_ids:
        counts[rule_id] = sum(1 for e in history if e["rule_id"] == rule_id)
    return counts


def get_preemptive_hints(
    rule_ids: list[str],
    *,
    history_path: Path = DEFAULT_HISTORY_PATH,
    threshold: int = PREEMPTIVE_HINT_THRESHOLD,
) -> list[str]:
    """各 rule_id の累計件数を確認、 threshold 超過するものについて hint message 生成.

    threshold 解決順序: RULE_THRESHOLD_OVERRIDES[rule_id] > threshold 引数 > PREEMPTIVE_HINT_THRESHOLD。
    重い違反 (= 代数法則 / データ移動量) は override で 2 回目に hint。
    """
    history = _load_history(history_path)
    hints: list[str] = []
    for rule_id in set(rule_ids):
        count = sum(1 for e in history if e["rule_id"] == rule_id)
        effective_threshold = _resolve_threshold(rule_id, threshold)
        if count >= effective_threshold:
            hints.append(
                f"WARNING: rule `{rule_id}` has been triggered {count} times across sessions "
                f"(threshold={effective_threshold}). "
                "Pre-emptive hint: review the alternative skeleton before re-writing."
            )
    return hints


def reset_history(history_path: Path = DEFAULT_HISTORY_PATH) -> None:
    """history を初期化 (= test 用 utility)."""
    if history_path.exists():
        history_path.unlink()


def _load_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(history: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
