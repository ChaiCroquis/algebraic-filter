"""Phase 2 精度 P3-C1: 小有限ドメインでの exhaustive (全数) 検証.

入力域が小さく有限なら、 hypothesis サンプリングでなく全数列挙で法則を検査する。
これは「その有限ドメインに対する決定論的保証」 (= サンプリングの確率性を排除)。
CrossHair (無限域の SMT 証明) より弱いが、 外部依存ゼロ・常に決定論で再現可能。

対象: binary int 関数の commutativity / associativity / idempotence / additive
identity。 反例があれば dict、 なければ None を返す。
"""
from __future__ import annotations

import inspect
import itertools
from collections.abc import Sequence
from typing import Callable

BinaryIntOp = Callable[[int, int], int]


def complete_domain(func: Callable[..., object]) -> tuple[object, ...] | None:
    """引数が全て *有限型* (現状 bool) 注釈なら、 その型の完全ドメインを返す.

    bool なら (False, True)。 完全ドメインで exhaustive すれば「有界」 でなく
    打ち切りなしの **完全証明** になる (型全体を尽くすため)。 無限型 (int 等) は None。
    """
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return None
    params = [
        p
        for p in sig.parameters.values()
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.POSITIONAL_ONLY)
    ]
    # `from __future__ import annotations` (PEP 563) 下では注釈が文字列 "bool" に
    # なるため、 bool 型と文字列 "bool" の両方を許容する。
    if params and all(p.annotation is bool or p.annotation == "bool" for p in params):
        return (False, True)
    return None


def exhaustive_verify(
    func: BinaryIntOp,
    law_id: str,
    *,
    bound: int = 5,
    domain: Sequence[object] | None = None,
    identity: object = 0,
) -> dict[str, str] | None:
    """binary 関数の法則を全数で検証. 反例 dict or None.

    domain 指定時はその全数 (有限型なら **完全証明**)、 未指定なら int の [-bound, bound]
    (有界証明 = この域内のみ保証)。 いずれも決定論・取りこぼしなし。
    """
    vals: Sequence[object] = list(domain) if domain is not None else range(-bound, bound + 1)
    try:
        if law_id == "commutativity":
            for a, b in itertools.product(vals, repeat=2):
                if func(a, b) != func(b, a):
                    return {"law_id": law_id, "counterexample": f"a={a}, b={b}"}
        elif law_id in ("monoid_associativity", "semigroup_associativity"):
            for a, b, c in itertools.product(vals, repeat=3):
                if func(func(a, b), c) != func(a, func(b, c)):
                    return {"law_id": law_id, "counterexample": f"a={a}, b={b}, c={c}"}
        elif law_id == "idempotence":
            for a in vals:
                if func(a, a) != a:
                    return {"law_id": law_id, "counterexample": f"a={a}"}
        elif law_id == "monoid_identity":
            for a in vals:
                if func(a, identity) != a or func(identity, a) != a:
                    return {"law_id": law_id, "counterexample": f"a={a}"}
        elif law_id == "eq_reflexivity":
            for a in vals:
                if not func(a, a):
                    return {"law_id": law_id, "counterexample": f"a={a}"}
        elif law_id == "eq_symmetry":
            for a, b in itertools.product(vals, repeat=2):
                if func(a, b) != func(b, a):
                    return {"law_id": law_id, "counterexample": f"a={a}, b={b}"}
    except Exception as exc:  # noqa: BLE001 - any raise within the domain is itself a defect
        return {"law_id": law_id, "counterexample": f"raised {type(exc).__name__}"}
    return None
