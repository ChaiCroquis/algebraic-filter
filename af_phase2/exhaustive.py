"""Phase 2 精度 P3-C1: 小有限ドメインでの exhaustive (全数) 検証.

入力域が小さく有限なら、 hypothesis サンプリングでなく全数列挙で法則を検査する。
これは「その有限ドメインに対する決定論的保証」 (= サンプリングの確率性を排除)。
CrossHair (無限域の SMT 証明) より弱いが、 外部依存ゼロ・常に決定論で再現可能。

対象: binary int 関数の commutativity / associativity / idempotence / additive
identity。 反例があれば dict、 なければ None を返す。
"""
from __future__ import annotations

import itertools
from typing import Callable

BinaryIntOp = Callable[[int, int], int]


def exhaustive_verify(
    func: BinaryIntOp, law_id: str, *, bound: int = 5
) -> dict[str, str] | None:
    """binary int 関数の法則を [-bound, bound] の全数で検証. 反例 dict or None.

    全数なので、 この有限ドメイン内では「証明」 (決定論・取りこぼしなし)。
    """
    vals = range(-bound, bound + 1)
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
                if func(a, 0) != a or func(0, a) != a:
                    return {"law_id": law_id, "counterexample": f"a={a}"}
    except Exception as exc:  # noqa: BLE001 - any raise within the domain is itself a defect
        return {"law_id": law_id, "counterexample": f"raised {type(exc).__name__}"}
    return None
