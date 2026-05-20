"""Phase 4 拡張: hook 実行時に Phase 2 PBT を inline で走らせる runner (opt-in).

Hook 起動時に env var `AF_HOOK_PHASE2_PBT=1` が設定されている場合のみ、
指定された .py file から関数を抽出して af_phase2.auto_test() を実行し、
FAIL/ERROR を Phase 4 統一 schema (= phase2_failures dict list) に整形する.

設計 trade-off:
  - 速度: hypothesis 実行は秒オーダー、 hook 全体 latency が 2-3 秒増加する
  - 安全性: target file を import する = side effect 走行 risk あり (__init__ 内 IO 等)
  - 適用範囲: 推奨は scratch/ や samples/ など書き捨て領域への限定

opt-in 既定 OFF の理由:
  - hook の主用途 (= 静的検査 Layer 1/3) は ms オーダーで完了、 fast loop に最適
  - Phase 2 PBT は 「論理的等価性を保証したい純粋関数」 向けの 重い検証で、
    日常 write 全てに走らせる cost に見合わない (= 適用 niche 限定)
"""
from __future__ import annotations

import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Callable


ENV_GATE = "AF_HOOK_PHASE2_PBT"


def _get_function_line(func: Callable[..., Any]) -> int:
    """関数の定義行を返す、 取得失敗時は 0."""
    try:
        return inspect.getsourcelines(func)[1]
    except (OSError, TypeError):
        return 0


def is_enabled() -> bool:
    """env var で opt-in 有効化されているか判定 (= '1' / 'true' / 'on' で有効)."""
    val = os.environ.get(ENV_GATE, "").strip().lower()
    return val in ("1", "true", "on", "yes")


def collect_phase2_failures(file_path: str) -> list[dict[str, Any]]:
    """指定 .py file から関数を抽出 + auto_test を走らせ FAIL/ERROR を返す.

    例外は全て握り潰し (= import 失敗、 関数なし、 hypothesis hang 等)。
    target file が production code なら本 runner を有効化すべきでない (= safety).

    返り値 dict 形式は af_phase4.feedback_formatter.format_phase2_violations
    が期待する schema と一致:
        {law_id, function_name, line, counter_example}
    """
    if not is_enabled():
        return []

    path = Path(file_path)
    if not path.exists() or path.suffix != ".py":
        return []

    failures: list[dict[str, Any]] = []
    try:
        # 動的 import: spec_from_file_location で sandbox module load
        module_name = f"_af_phase2_target_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            return []
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            # SyntaxError / ImportError / runtime side-effect failure 全て skip
            return []

        # af_phase2 が import 可能か確認
        try:
            from af_phase2.generator import auto_test  # type: ignore
            from af_phase2.inferrer import infer_laws  # type: ignore
        except Exception:
            return []

        # module-level callable を列挙
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            # target module 内で定義された関数のみ (= import 由来は除外)
            if getattr(obj, "__module__", "") != module_name:
                continue
            try:
                laws = infer_laws(obj)
            except Exception:
                continue
            if not laws:
                continue
            # auto_test を走らせ FAIL/ERROR を抽出
            try:
                results = auto_test(obj)
            except Exception:
                continue
            failures.extend(
                {
                    "law_id": r.law_id,
                    "function_name": name,
                    "line": _get_function_line(obj),
                    "counter_example": (r.error or "")[:120],
                }
                for r in results
                if r.status in ("FAIL", "ERROR")
            )
    finally:
        # sandbox module を sys.modules から removal (= memory hygiene)
        sys.modules.pop(f"_af_phase2_target_{path.stem}", None)

    return failures


