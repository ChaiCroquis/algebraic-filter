"""決定論拡張 D4: 純粋性/決定性 静的検証のテスト.

非チェリーピック: 純粋な正例 + 各不純カテゴリ (global/nonlocal/io/nondeterminism) を
系統的に網羅。 純粋判定は「シグナル不在」を assert し、 不純判定は kind を assert。

実行: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase3_purity.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase3.purity_checker import check_purity, is_pure  # noqa: E402


def _kinds(src: str) -> set[str]:
    return {f.kind for f in check_purity(src)}


def test_pure_arithmetic_is_pure() -> None:
    src = "def f(a, b):\n    return a * b + 1\n"
    assert is_pure(src)
    assert check_purity(src) == []


def test_pure_stdlib_math_is_pure() -> None:
    """決定論的 stdlib (math) は純粋扱い (非決定集合に入っていない)."""
    src = "import math\ndef f(x):\n    return math.sqrt(x) + math.floor(x)\n"
    assert is_pure(src)


def test_global_is_impure() -> None:
    src = "g = 0\ndef f(x):\n    global g\n    g = x\n    return g\n"
    assert "global" in _kinds(src)
    assert not is_pure(src)


def test_nonlocal_is_impure() -> None:
    src = "def outer():\n    s = 0\n    def f(x):\n        nonlocal s\n        s += x\n    return f\n"
    assert "nonlocal" in _kinds(src)


def test_io_calls_are_impure() -> None:
    for src in (
        "def f(x):\n    print(x)\n    return x\n",
        "def f(p):\n    return open(p).read()\n",
        "def f():\n    return input()\n",
    ):
        assert "io" in _kinds(src), src


def test_nondeterminism_calls_are_impure() -> None:
    for src in (
        "import random\ndef f():\n    return random.random()\n",
        "import time\ndef f():\n    return time.time()\n",
        "import uuid\ndef f():\n    return uuid.uuid4()\n",
        "import datetime\ndef f():\n    return datetime.datetime.now()\n",
        "import os\ndef f():\n    return os.urandom(8)\n",
    ):
        assert "nondeterminism" in _kinds(src), src


def test_deterministic_os_path_not_flagged() -> None:
    """os.path.join は決定論的 → flag しない (os 全体を非決定にしない健全さ)."""
    src = "import os\ndef f(a, b):\n    return os.path.join(a, b)\n"
    # os.path.join は os.urandom 等の curated 集合に無いので nondeterminism 扱いされない
    assert "nondeterminism" not in _kinds(src)
