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
    """各 rule_id の累計件数を確認、 threshold 超過するものについて hint message 生成."""
    history = _load_history(history_path)
    hints: list[str] = []
    for rule_id in set(rule_ids):
        count = sum(1 for e in history if e["rule_id"] == rule_id)
        if count >= threshold:
            hints.append(
                f"WARNING: rule `{rule_id}` has been triggered {count} times across sessions. "
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
