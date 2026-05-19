"""関数シグネチャ → 期待法則の推論 + hypothesis strategy 自動選択 (Phase 2 拡張).

入力: callable (関数オブジェクト)
出力: list[str] (期待法則 ID) + strategy mapping
"""
from __future__ import annotations

import inspect
from typing import Any, Callable

from hypothesis import strategies as st


_TYPE_TO_STRATEGY = {
    int: st.integers(min_value=-50, max_value=50),
    float: st.floats(min_value=-50, max_value=50, allow_nan=False, allow_infinity=False),
    str: st.text(min_size=1, max_size=5),
    bool: st.booleans(),
}


def infer_strategy_for_annotation(annotation: Any) -> st.SearchStrategy:
    """型注釈 → hypothesis strategy. generic (list[T]) も unwrap."""
    if annotation is inspect.Parameter.empty:
        return _TYPE_TO_STRATEGY[int]

    origin = getattr(annotation, "__origin__", None)
    if origin is list:
        args = getattr(annotation, "__args__", (int,))
        inner = args[0] if args else int
        return st.lists(infer_strategy_for_annotation(inner), min_size=1, max_size=5)

    if annotation in _TYPE_TO_STRATEGY:
        return _TYPE_TO_STRATEGY[annotation]

    return _TYPE_TO_STRATEGY[int]


def infer_strategies_for_func(func: Callable) -> list:
    """各 positional 引数に対する strategy list を返す (callable 引数は None)."""
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return []

    strategies = []
    for param in sig.parameters.values():
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if param.name in ("f", "func", "fn", "g", "op", "operation"):
            strategies.append(None)
        else:
            strategies.append(infer_strategy_for_annotation(param.annotation))
    return strategies


_NAME_TO_LAWS: dict[str, list[str]] = {
    "sum": ["monoid_identity", "monoid_associativity"],
    "fold": ["monoid_identity", "monoid_associativity"],
    "aggregate": ["monoid_identity"],
    "reduce": ["monoid_identity", "monoid_associativity"],
    "concat": ["monoid_identity"],
    "map": ["functor_identity", "functor_compose"],
    "fmap": ["functor_identity", "functor_compose"],
    "transform": ["functor_identity"],
    "merge": ["commutativity"],
    "average": ["commutativity"],
    "intersect": ["commutativity"],
    "union": ["commutativity"],
    "combine": ["commutativity"],
}


def _name_lower(func: Callable) -> str:
    return getattr(func, "__name__", "").lower()


def infer_laws(func: Callable) -> list[str]:
    """関数名から期待法則 ID 集合を推論. Minimal heuristic."""
    name = _name_lower(func)
    laws: list[str] = []

    # 関数名部分一致
    for keyword, law_ids in _NAME_TO_LAWS.items():
        if keyword in name:
            laws.extend(law_ids)

    return list(dict.fromkeys(laws))  # dedup, preserve order


def infer_laws_for_monad_pair(pure: Callable, bind: Callable) -> list[str]:
    """pure + bind の関数 pair から Monad 3 法則を推論."""
    if _name_lower(pure) == "pure" and _name_lower(bind) == "bind":
        return ["monad_left_identity", "monad_right_identity", "monad_associativity"]
    return []


def inspect_signature_summary(func: Callable) -> dict:
    """関数の型シグネチャ summary (Phase 2 debug 用)."""
    try:
        sig = inspect.signature(func)
        return {
            "name": getattr(func, "__name__", "?"),
            "params": [(p.name, str(p.annotation)) for p in sig.parameters.values()],
            "return": str(sig.return_annotation),
        }
    except (ValueError, TypeError):
        return {"name": getattr(func, "__name__", "?"), "error": "signature unavailable"}
