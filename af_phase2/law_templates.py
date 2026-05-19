"""代数法則の property template 集.

各 template は (target_function, optional_args) を受け取り、
hypothesis @given test を返す callable factory として articulate。

実装は minimal prototype: Monoid / Functor / Commutativity / Monad 4 法則カテゴリ。
"""
from __future__ import annotations

from typing import Any, Callable

from hypothesis import given, strategies as st


def monoid_identity_law(my_op: Callable, identity: Any) -> Callable:
    """Monoid identity: my_op(xs, init=identity) == my_op(xs) (or sum semantics)"""

    @given(st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=10))
    def prop(xs: list[int]) -> None:
        # standard sum semantics 期待
        expected = sum(xs) if identity == 0 else identity + sum(xs)
        actual = my_op(xs)
        assert actual == expected, f"monoid identity: {my_op.__name__}({xs})={actual}, expected={expected}"

    return prop


def functor_identity_law(my_map: Callable) -> Callable:
    """Functor identity: my_map(id, xs) == xs"""

    @given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=5))
    def prop(xs: list[int]) -> None:
        actual = my_map(lambda x: x, xs)
        assert actual == list(xs), f"functor identity: {my_map.__name__}(id, {xs})={actual}"

    return prop


def commutativity_law(binary_op: Callable, element_strategy: Any = None) -> Callable:
    """Commutativity: op(a, b) == op(b, a) — element_strategy で型に応じた input"""
    strategy = element_strategy if element_strategy is not None else st.integers(min_value=-50, max_value=50)

    @given(strategy, strategy)
    def prop(a: Any, b: Any) -> None:
        from hypothesis import assume

        assume(a != b)
        lhs = binary_op(a, b)
        rhs = binary_op(b, a)
        assert lhs == rhs, f"commutativity: {binary_op.__name__}({a!r},{b!r})={lhs!r}, ({b!r},{a!r})={rhs!r}"

    return prop


def monad_left_identity_law(pure: Callable, bind: Callable) -> Callable:
    """Monad left identity: bind(pure(a), f) == f(a)"""

    @given(st.integers(min_value=-50, max_value=50))
    def prop(a: int) -> None:
        def f(x: int) -> Any:
            return pure(x * 2)

        lhs = bind(pure(a), f)
        rhs = f(a)
        assert lhs == rhs, f"monad left identity: bind(pure({a}), f)={lhs}, expected {rhs}"

    return prop


def functor_compose_law(my_map: Callable) -> Callable:
    """Functor compose: my_map(f . g, xs) == my_map(f, my_map(g, xs))"""

    @given(st.lists(st.integers(min_value=-50, max_value=50), min_size=1, max_size=5))
    def prop(xs: list[int]) -> None:
        def f(x: int) -> int:
            return x + 1

        def g(x: int) -> int:
            return x * 2

        lhs = my_map(f, my_map(g, xs))
        rhs = my_map(lambda x: f(g(x)), xs)
        assert lhs == rhs, f"functor compose: {my_map.__name__} fails for {xs}"

    return prop


def monoid_associativity_law(my_op: Callable) -> Callable:
    """Monoid associativity for reduce-style: result is order-independent for chunked input"""

    @given(st.lists(st.integers(min_value=-50, max_value=50), min_size=3, max_size=8))
    def prop(xs: list[int]) -> None:
        # 全 list と前半+後半 (concat) が同じ結果になるかの大局チェック
        full = my_op(xs)
        mid = len(xs) // 2
        # standard sum semantics 期待
        chunked = my_op(xs[:mid]) + my_op(xs[mid:])
        assert full == chunked, f"monoid associativity: {my_op.__name__}({xs}) inconsistent"

    return prop


def foldable_foldl_foldr_equivalence_law(left_fold: Callable, right_fold: Callable) -> Callable:
    """Foldable: foldl と foldr が associative op で等価"""

    @given(st.lists(st.integers(min_value=-50, max_value=50), min_size=2, max_size=5))
    def prop(xs: list[int]) -> None:
        lhs = left_fold(xs)
        rhs = right_fold(xs)
        assert lhs == rhs, f"foldl/foldr equivalence: lhs={lhs}, rhs={rhs} for {xs}"

    return prop


def monad_right_identity_law(pure: Callable, bind: Callable) -> Callable:
    """Monad right identity: bind(m, pure) == m"""

    @given(st.integers(min_value=-50, max_value=50))
    def prop(a: int) -> None:
        m = pure(a)
        result = bind(m, pure)
        assert result == m, f"monad right identity: bind(pure({a}), pure)={result}, expected {m}"

    return prop


def monad_associativity_law(pure: Callable, bind: Callable) -> Callable:
    """Monad associativity: bind(bind(m, f), g) == bind(m, lambda x: bind(f(x), g))"""

    @given(st.integers(min_value=-50, max_value=50))
    def prop(a: int) -> None:
        def f(x: int) -> Any:
            return pure(x + 1)

        def g(x: int) -> Any:
            return pure(x * 2)

        lhs = bind(bind(pure(a), f), g)
        rhs = bind(pure(a), lambda x: bind(f(x), g))
        assert lhs == rhs, f"monad associativity: a={a}, lhs={lhs}, rhs={rhs}"

    return prop


def idempotence_law_state_int(operation: Callable) -> Callable:
    """Idempotence: 2 回適用が 1 回適用と等価 (state-based、 int input)"""

    @given(st.integers(min_value=-50, max_value=50))
    def prop(x: int) -> None:
        once = operation(x)
        twice = operation(operation(x))
        assert once == twice, f"idempotence: op({x})={once}, op(op({x}))={twice}"

    return prop


def semigroup_associativity_law(binary_op: Callable, element_strategy: Any = None) -> Callable:
    """Semigroup associativity: (a op b) op c == a op (b op c) — Haskell QuickCheck-classes reference."""
    strategy = element_strategy if element_strategy is not None else st.integers(min_value=-30, max_value=30)

    @given(strategy, strategy, strategy)
    def prop(a: Any, b: Any, c: Any) -> None:
        lhs = binary_op(binary_op(a, b), c)
        rhs = binary_op(a, binary_op(b, c))
        assert lhs == rhs, f"semigroup associativity: ({a!r} op {b!r}) op {c!r}={lhs!r} != {a!r} op ({b!r} op {c!r})={rhs!r}"

    return prop


def eq_reflexivity_law(eq_op: Callable, element_strategy: Any = None) -> Callable:
    """Eq reflexivity: a == a — Haskell QuickCheck-classes reference."""
    strategy = element_strategy if element_strategy is not None else st.integers(min_value=-50, max_value=50)

    @given(strategy)
    def prop(a: Any) -> None:
        assert eq_op(a, a), f"eq reflexivity: {a!r} == {a!r} expected True"

    return prop


def eq_symmetry_law(eq_op: Callable, element_strategy: Any = None) -> Callable:
    """Eq symmetry: a == b implies b == a — Haskell QuickCheck-classes reference."""
    strategy = element_strategy if element_strategy is not None else st.integers(min_value=-50, max_value=50)

    @given(strategy, strategy)
    def prop(a: Any, b: Any) -> None:
        if eq_op(a, b):
            assert eq_op(b, a), f"eq symmetry: {a!r}=={b!r} but {b!r}!={a!r}"

    return prop


# ---- class-based / stateful properties (Phase 2 拡張、 Hypothesis stateful testing 系) ----


def _capture_state(instance: Any) -> Any:
    """instance の state を hash 可能な representation で取得."""
    if hasattr(instance, "__len__"):
        try:
            return ("len", len(instance))
        except TypeError:
            pass
    if hasattr(instance, "__dict__"):
        return ("dict", tuple(sorted((k, repr(v)) for k, v in instance.__dict__.items())))
    return ("repr", repr(instance))


def class_idempotence_law(
    cls: type,
    method_name: str,
    arg_strategy: Any = None,
) -> Callable:
    """class の method の冪等性: method(x) を 2 回呼んだ state == 1 回呼んだ state."""
    strategy = arg_strategy if arg_strategy is not None else st.integers(min_value=-30, max_value=30)

    @given(strategy)
    def prop(x: Any) -> None:
        instance = cls()
        method = getattr(instance, method_name)
        method(x)
        state_once = _capture_state(instance)
        method(x)
        state_twice = _capture_state(instance)
        assert state_once == state_twice, (
            f"class idempotence: {cls.__name__}.{method_name}({x!r}) "
            f"1 回後={state_once} != 2 回後={state_twice}"
        )

    return prop


LAW_REGISTRY: dict[str, Callable] = {
    "monoid_identity": monoid_identity_law,
    "monoid_associativity": monoid_associativity_law,
    "semigroup_associativity": semigroup_associativity_law,
    "functor_identity": functor_identity_law,
    "functor_compose": functor_compose_law,
    "commutativity": commutativity_law,
    "monad_left_identity": monad_left_identity_law,
    "monad_right_identity": monad_right_identity_law,
    "monad_associativity": monad_associativity_law,
    "foldable_foldl_foldr_equivalence": foldable_foldl_foldr_equivalence_law,
    "idempotence": idempotence_law_state_int,
    "eq_reflexivity": eq_reflexivity_law,
    "eq_symmetry": eq_symmetry_law,
    "class_idempotence": class_idempotence_law,
}
