"""AF main env (Windows native, Python 3.13) から Docker container 経由で Scalpel を呼ぶ bridge.

Scalpel (python-scalpel) は typed-ast 依存で Python 3.13 build 失敗のため、
Docker container (Python 3.10) に閉じ込めて subprocess + volume mount で bridge する.

container build:
    docker build -t af-scalpel -f Dockerfile.scalpel .

使用例:
    from af_phase3.scalpel_bridge import analyze_cfg
    result = analyze_cfg("samples/violations/intermediate_list_chain.py")
    print(result["function_count"], result["function_cfgs"])
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
DOCKER_IMAGE = "af-scalpel"


def _to_container_path(file_path: str | Path) -> str:
    """Windows native path を container 内 /workspace 相対 path に変換."""
    abs_path = Path(file_path).resolve()
    try:
        rel = abs_path.relative_to(_REPO_ROOT)
    except ValueError as e:
        raise ValueError(f"file_path must be inside repo root {_REPO_ROOT}: {abs_path}") from e
    return f"/workspace/{rel.as_posix()}"


def analyze_cfg(file_path: str | Path, timeout_seconds: int = 60) -> dict[str, Any]:
    """指定 Python file を Docker container 内 Scalpel で CFG 解析."""
    container_path = _to_container_path(file_path)
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{_REPO_ROOT}:/workspace",
        DOCKER_IMAGE,
        "python",
        "-m",
        "af_phase3_scalpel.cfg_analyzer",
        container_path,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"docker run timeout after {timeout_seconds}s"}
    except FileNotFoundError:
        return {"error": "docker CLI not found in PATH"}

    if result.returncode != 0:
        return {
            "error": f"docker exec returncode={result.returncode}",
            "stderr": (result.stderr or "")[:500],
            "stdout": (result.stdout or "")[:500],
        }
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode failed: {e}", "raw": result.stdout[:500]}


def is_docker_available() -> bool:
    """Docker CLI + af-scalpel image が利用可能かチェック."""
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", DOCKER_IMAGE],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
