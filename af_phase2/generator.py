"""推論結果 + 法則テンプレ → hypothesis @given test の自動生成.

minimal prototype: 関数を直接受け取って property を inline 実行する API。
Phase 2 後半で「test file 出力」 path に拡張予定。
"""
from __future__ import annotations

from typing import Any, Callable

from af_phase2.inferrer import (
    infer_laws,
    infer_laws_for_monad_pair,
    infer_strategies_for_func,
)
from af_phase2.law_templates import LAW_REGISTRY


class PropertyTestResult:
    """auto-generated property test の実行結果"""

    def __init__(self, law_id: str, status: str, error: str | None = None) -> None:
        self.law_id = law_id
        self.status = status  # "PASS" / "FAIL"
        self.error = error

    def __repr__(self) -> str:
        return f"PropertyTestResult(law={self.law_id}, status={self.status}, error={self.error!r})"


def auto_test(func: Callable, *, extra_args: dict[str, Any] | None = None) -> list[PropertyTestResult]:
    """関数 1 つから expected 法則を推論 + property test を inline 実行."""
    laws = infer_laws(func)
    results: list[PropertyTestResult] = []
    extra_args = extra_args or {}

    # 型シグネチャベース strategy 推論 (Phase 2 拡張)
    strategies = infer_strategies_for_func(func)
    # 法則別 strategy = first non-None strategy from inferred list (commutativity は a, b 用 element)
    element_strategy = next((s for s in strategies if s is not None), None)

    for law_id in laws:
        template = LAW_REGISTRY.get(law_id)
        if template is None:
            continue
        try:
            if law_id == "monoid_identity":
                identity = extra_args.get("identity", 0)
                prop = template(func, identity)
            elif law_id == "commutativity":
                prop = template(func, element_strategy)
            elif law_id in (
                "functor_identity",
                "functor_compose",
                "monoid_associativity",
                "idempotence",
            ):
                prop = template(func)
            else:
                # monad / foldable は pair API、 単 func では skip
                continue
            prop()
            results.append(PropertyTestResult(law_id, "PASS"))
        except AssertionError as e:
            results.append(PropertyTestResult(law_id, "FAIL", str(e)[:200]))
        except Exception as e:
            results.append(PropertyTestResult(law_id, "ERROR", f"{type(e).__name__}: {e}"[:200]))

    return results


def auto_test_class_idempotence(
    cls: type, method_name: str = "add"
) -> list[PropertyTestResult]:
    """class-based 冪等性 property test (Hypothesis stateful 系の minimal API).

    'add' / 'remove' / 'update' / 'increment' 等の method 名を指定して
    method(x) を 2 回呼んだ state == 1 回呼んだ state を検証.
    """
    template = LAW_REGISTRY.get("class_idempotence")
    if template is None:
        return []
    results: list[PropertyTestResult] = []
    try:
        prop = template(cls, method_name)
        prop()
        results.append(PropertyTestResult("class_idempotence", "PASS"))
    except AssertionError as e:
        results.append(PropertyTestResult("class_idempotence", "FAIL", str(e)[:200]))
    except Exception as e:
        results.append(
            PropertyTestResult("class_idempotence", "ERROR", f"{type(e).__name__}: {e}"[:200])
        )
    return results


def auto_test_monad_pair(
    pure: Callable, bind: Callable
) -> list[PropertyTestResult]:
    """pure + bind の pair から Monad left identity を property test."""
    laws = infer_laws_for_monad_pair(pure, bind)
    results: list[PropertyTestResult] = []
    for law_id in laws:
        template = LAW_REGISTRY.get(law_id)
        if template is None:
            continue
        try:
            prop = template(pure, bind)
            prop()
            results.append(PropertyTestResult(law_id, "PASS"))
        except AssertionError as e:
            results.append(PropertyTestResult(law_id, "FAIL", str(e)[:200]))
        except Exception as e:
            results.append(PropertyTestResult(law_id, "ERROR", f"{type(e).__name__}: {e}"[:200]))
    return results
