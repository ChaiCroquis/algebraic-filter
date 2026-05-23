"""D6: profile (write-time / ci) 解決と CI ランナーのテスト.

非チェリーピック:
  - profile 解決の優先順位を 4 経路で網羅 (既定 / file / env / 個別スイッチ override)。
  - CI ランナーの exit code を 違反ファイル / clean ファイルの *対* で確認。

実行: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_profile_and_ci.py -v
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase4.config import resolve_bool, resolve_profile  # noqa: E402

_NO_CONFIG = str(REPO_ROOT / "_no_such_af_config.json")


def _isolate(monkeypatch: pytest.MonkeyPatch) -> None:
    """個別 env + ローカル .algebraic-filter.json から隔離 (= 既定挙動を確かめる)."""
    for k in ("AF_PROFILE", "AF_CROSSHAIR", "AF_HOOK_PHASE2_PBT"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("AF_CONFIG_PATH", _NO_CONFIG)


def test_default_profile_is_write_time(monkeypatch: pytest.MonkeyPatch) -> None:
    _isolate(monkeypatch)
    assert resolve_profile() == "write-time"
    assert resolve_bool("crosshair_verify", "AF_CROSSHAIR") is False
    assert resolve_bool("phase2_runtime", "AF_HOOK_PHASE2_PBT") is False


def test_ci_profile_enables_heavy_layers(monkeypatch: pytest.MonkeyPatch) -> None:
    _isolate(monkeypatch)
    monkeypatch.setenv("AF_PROFILE", "ci")
    assert resolve_profile() == "ci"
    assert resolve_bool("crosshair_verify", "AF_CROSSHAIR") is True
    assert resolve_bool("phase2_runtime", "AF_HOOK_PHASE2_PBT") is True


def test_individual_env_switch_overrides_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """個別スイッチ (env) は profile より優先 (= 1 層だけ上書き可)."""
    _isolate(monkeypatch)
    monkeypatch.setenv("AF_PROFILE", "ci")  # profile は重い層 ON だが…
    monkeypatch.setenv("AF_CROSSHAIR", "0")  # …個別に OFF 指定が勝つ
    assert resolve_profile() == "ci"
    assert resolve_bool("crosshair_verify", "AF_CROSSHAIR") is False
    assert resolve_bool("phase2_runtime", "AF_HOOK_PHASE2_PBT") is True  # 上書きしてない層は profile 通り


def test_file_profile_resolved(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """file の "profile" が env 不在時に効く (env > file の file 側)."""
    for k in ("AF_PROFILE", "AF_CROSSHAIR", "AF_HOOK_PHASE2_PBT"):
        monkeypatch.delenv(k, raising=False)
    cfg = tmp_path / ".algebraic-filter.json"
    cfg.write_text('{"profile": "ci"}', encoding="utf-8")
    monkeypatch.setenv("AF_CONFIG_PATH", str(cfg))
    assert resolve_profile() == "ci"
    assert resolve_bool("crosshair_verify", "AF_CROSSHAIR") is True


def _run_ci(path: str) -> int:
    env = {k: v for k, v in os.environ.items() if k not in ("AF_PROFILE", "AF_CROSSHAIR", "AF_HOOK_PHASE2_PBT")}
    env["AF_CONFIG_PATH"] = _NO_CONFIG  # write-time 既定で隔離 (重い層 skip = 高速)
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "af_ci.py"), path],
        capture_output=True, text=True, env=env, check=False,
    )
    return proc.returncode


def test_ci_runner_clean_file_exit_zero(tmp_path: Path) -> None:
    f = tmp_path / "clean.py"
    f.write_text("def f(x: int) -> int:\n    return x\n", encoding="utf-8")
    assert _run_ci(str(f)) == 0


def test_ci_runner_violation_exit_nonzero(tmp_path: Path) -> None:
    f = tmp_path / "bad.py"
    f.write_text("def f(x):\n    return x\n", encoding="utf-8")  # ANN001 + ANN201
    assert _run_ci(str(f)) == 1
