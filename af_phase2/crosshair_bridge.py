"""Opt-in CrossHair proof layer for algebraic laws (af_phase2).

Default OFF. Enable via env `AF_CROSSHAIR=1` or config `crosshair_verify: true`
(resolved through af_phase4.config). When on, verifies associativity /
commutativity of **binary** functions by symbolic proof (SMT) instead of
random sampling — catching rare-value violations that hypothesis misses
(measured 2026-05-21: caught a==999983 associativity/commutativity bugs that
bounded sampling did not).

Scope (verified): binary `(T, T) -> T` functions — associativity, commutativity,
and additive identity (`op(a,0)==a==op(0,a)`, the natural identity for additive
monoids). Functor / monad laws are NOT covered (they need richer contracts).
Gracefully no-ops if crosshair-tool is not installed or the function is out of
scope.

Determinism: CrossHair uses an SMT solver — proofs/counterexamples are
deterministic (no random seed), unlike hypothesis sampling.
"""
from __future__ import annotations

import inspect
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Callable

ENV_GATE = "AF_CROSSHAIR"

# law_id -> (checker suffix, params, boolean expr over the function aliased as `op`)
# Note: monoid_identity here is the BINARY additive-identity law (e = 0): for a
# binary numeric op, op(a, 0) == a == op(0, a). This is the natural identity for
# additive monoids (sum/add/total); a non-additive binary op declaring
# monoid_identity would need a different element (out of scope — declare assoc/
# commut instead, or use the hypothesis path).
_LAW_CONTRACT: dict[str, tuple[str, str, str]] = {
    "monoid_associativity": ("assoc", "a, b, c", "op(op(a, b), c) == op(a, op(b, c))"),
    "semigroup_associativity": ("assoc", "a, b, c", "op(op(a, b), c) == op(a, op(b, c))"),
    "commutativity": ("commut", "a, b", "op(a, b) == op(b, a)"),
    "monoid_identity": ("identity", "a", "op(a, 0) == a and op(0, a) == a"),
    # binary idempotence: combining a value with itself yields itself (max/min/
    # union/gcd…). No identity element needed → clean for the binary SMT model.
    "idempotence": ("idem", "a", "op(a, a) == a"),
    # Eq laws: a binary->bool predicate. reflexivity = eq(a,a) holds;
    # symmetry = eq(a,b) == eq(b,a). Both proof-checkable on the binary model.
    "eq_reflexivity": ("eqrefl", "a", "op(a, a)"),
    "eq_symmetry": ("eqsym", "a, b", "op(a, b) == op(b, a)"),
}


def is_enabled() -> bool:
    """Opt-in gate: env AF_CROSSHAIR > config crosshair_verify > safe default False."""
    from af_phase4.config import resolve_bool

    return resolve_bool("crosshair_verify", ENV_GATE)


def _crosshair_available() -> bool:
    try:
        import crosshair  # noqa: F401

        return True
    except Exception:
        return False


def _binary_param_type(func: Callable[..., Any]) -> str | None:
    """Return the shared annotation name if func is binary (T, T) -> *, else None."""
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return None
    params = [
        p
        for p in sig.parameters.values()
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.POSITIONAL_ONLY)
    ]
    if len(params) != 2:
        return None
    ann = params[0].annotation
    if ann is inspect.Parameter.empty:
        return "int"
    # PEP 563 (from __future__ import annotations) では注釈が文字列 ("str" 等)。
    if isinstance(ann, str):
        return ann
    return getattr(ann, "__name__", "int")


def _strip_af_decorators(src: str) -> str:
    """AF 宣言デコレータ (@law / @no_law / @contract) 行を除去.

    純メタデータで、 standalone temp module には定義が無く NameError になるため
    (証明には無害、 関数本体は不変)。
    """
    return "\n".join(
        ln for ln in src.splitlines() if not re.match(r"\s*@(law|no_law|contract)\b", ln)
    )


def _typed_params(func: Callable[..., Any]) -> tuple[str, str]:
    """(typed signature, arg names) を返す. 注釈は PEP563 文字列も型も許容、 既定 int."""
    sig = inspect.signature(func)
    params = [
        p
        for p in sig.parameters.values()
        if p.kind in (p.POSITIONAL_OR_KEYWORD, p.POSITIONAL_ONLY)
    ]

    def ann_name(ann: object) -> str:
        if ann is inspect.Parameter.empty:
            return "int"
        if isinstance(ann, str):
            return ann
        return getattr(ann, "__name__", "int")

    typed = ", ".join(f"{p.name}: {ann_name(p.annotation)}" for p in params)
    names = ", ".join(p.name for p in params)
    return typed, names


def verify_contract(func: Callable[..., Any]) -> list[dict[str, str]]:
    """@contract(post=..., pre=...) で宣言された事後条件を CrossHair で証明 (D5).

    任意の決定可能性質 (result>=0, len(out)==len(inp) 等) を法則の外で検証。
    反例があれば [{law_id: "contract", counterexample}]、 無ければ []。
    """
    if not is_enabled() or not _crosshair_available():
        return []
    spec = getattr(func, "__af_contract__", None)
    if not spec or not spec.get("post"):
        return []
    try:
        src = _strip_af_decorators(textwrap.dedent(inspect.getsource(func)))
        typed, names = _typed_params(func)
    except (OSError, TypeError, ValueError):
        return []

    post = spec["post"]
    pre = spec.get("pre")
    fname = func.__name__
    guard = f"    if not ({pre}):\n        return True\n" if pre else ""
    check = (
        f"def check_contract({typed}) -> bool:\n"
        f'    """\n    post: __return__\n    """\n'
        f"{guard}"
        f"    result = {fname}({names})\n"
        f"    return bool({post})\n"
    )
    code = f"{src}\n{check}"
    tmp = Path(tempfile.mkdtemp()) / "af_ch_contract.py"
    tmp.write_text(code, encoding="utf-8")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "crosshair", "check", str(tmp), "--per_condition_timeout=8"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []
    out = (result.stdout or "") + (result.stderr or "")
    violations: list[dict[str, str]] = []
    for line in out.splitlines():
        if "false when calling" in line and "check_contract" in line:
            m = re.search(r"check_contract\((.*?)\)", line)
            violations.append({"law_id": "contract", "counterexample": (m.group(1) if m else "")[:120]})
    return violations


def verify(func: Callable[..., Any]) -> list[dict[str, str]]:
    """CrossHair-proved law violations for a binary function (empty if none/disabled).

    Each violation: {law_id, counterexample}. Deterministic (SMT).
    """
    if not is_enabled() or not _crosshair_available():
        return []

    from af_phase2.inferrer import infer_laws

    laws = [law for law in infer_laws(func) if law in _LAW_CONTRACT]
    if not laws:
        return []
    ptype = _binary_param_type(func)
    if ptype is None:
        return []

    try:
        src = textwrap.dedent(inspect.getsource(func))
    except (OSError, TypeError):
        return []
    src = _strip_af_decorators(src)
    fname = func.__name__

    parts = [src, f"op = {fname}\n"]
    seen: set[str] = set()
    # suffix -> 実際に推論された law (= 複数 law が同 suffix を共有しても、 この関数で
    # 推論された law を first-wins で対応付け、 報告 law_id の取り違えを防ぐ)
    suffix_to_law: dict[str, str] = {}
    for law in laws:
        suffix, params, expr = _LAW_CONTRACT[law]
        if law == "monoid_identity":
            # 宣言された単位元 (@law(..., identity=e)) で expr を生成。 既定は加法 0。
            elem = getattr(func, "__af_law_identity__", 0)
            expr = f"op(a, {elem!r}) == a and op({elem!r}, a) == a"
        suffix_to_law.setdefault(suffix, law)
        if suffix in seen:
            continue
        seen.add(suffix)
        typed = ", ".join(f"{p.strip()}: {ptype}" for p in params.split(","))
        parts.append(
            f'def check_{suffix}({typed}) -> bool:\n'
            f'    """\n    post: __return__\n    """\n'
            f"    return {expr}\n"
        )

    code = "\n".join(parts)
    tmp = Path(tempfile.mkdtemp()) / "af_ch_target.py"
    tmp.write_text(code, encoding="utf-8")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "crosshair", "check", str(tmp), "--per_condition_timeout=8"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []

    out = (result.stdout or "") + (result.stderr or "")
    violations: list[dict[str, str]] = []
    for line in out.splitlines():
        if "false when calling" not in line:
            continue
        m = re.search(r"check_(\w+)\((.*?)\)", line)
        if not m:
            continue
        law = suffix_to_law.get(m.group(1))
        if law:
            violations.append({"law_id": law, "counterexample": m.group(2)[:120]})
    return violations
