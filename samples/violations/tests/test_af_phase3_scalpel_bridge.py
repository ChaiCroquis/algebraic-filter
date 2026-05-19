"""Phase 3 拡張: Scalpel Docker bridge 動作確認.

Scalpel (python-scalpel) は Python 3.13 で typed-ast build 失敗のため Docker (Python 3.10)
container に閉じ込めて、 AF main env から subprocess + volume mount で bridge する。
本 test は bridge 経由で Phase 1 sample の CFG (Control Flow Graph) が取得できることを demo.

事前準備:
    cd algebraic-filter && docker build -t af-scalpel -f Dockerfile.scalpel .

実走: python -m pytest samples/violations/tests/test_af_phase3_scalpel_bridge.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase3.scalpel_bridge import analyze_cfg, is_docker_available  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _require_docker_image() -> None:
    if not is_docker_available():
        pytest.skip("Docker image af-scalpel not available; run docker build first", allow_module_level=True)


def test_scalpel_bridge_analyzes_intermediate_list_chain() -> None:
    """bridge 経由で #6 intermediate_list_chain の CFG 解析"""
    result = analyze_cfg("samples/violations/intermediate_list_chain.py")
    assert "error" not in result, f"bridge error: {result}"
    assert result["function_count"] >= 1
    # Scalpel CFG の function_name は [line, name] tuple として返る
    names = [
        f["function_name"][1] if isinstance(f["function_name"], list) else f["function_name"]
        for f in result["function_cfgs"]
    ]
    assert "transform" in names, f"expected 'transform' in {names}"


def test_scalpel_bridge_analyzes_multi_step_intermediate() -> None:
    """bridge 経由で #20 multi_step_intermediate_chain の CFG 解析"""
    result = analyze_cfg("samples/violations/multi_step_intermediate_chain.py")
    assert "error" not in result, f"bridge error: {result}"
    assert result["function_count"] >= 1
    names = [
        f["function_name"][1] if isinstance(f["function_name"], list) else f["function_name"]
        for f in result["function_cfgs"]
    ]
    assert "transform_3_steps" in names, f"expected 'transform_3_steps' in {names}"


def test_scalpel_bridge_analyzes_monoid_associativity() -> None:
    """bridge 経由で #5 monoid_associativity の CFG 解析 (Phase 2 sample も対応)"""
    result = analyze_cfg("samples/violations/monoid_associativity_violation.py")
    assert "error" not in result, f"bridge error: {result}"
    assert result["function_count"] >= 1


def test_scalpel_bridge_handles_invalid_path() -> None:
    """存在しない path で error 返却"""
    try:
        result = analyze_cfg("samples/violations/_nonexistent_.py")
        # container 内で FileNotFoundError → error 返却 or stderr
        assert "error" in result or result.get("function_count", -1) == 0
    except ValueError:
        # path that doesn't exist might fail at relative_to / read_text stage
        pass
