"""Config switch-layer verification: env > file > safe-default precedence.

The security-sensitive Phase 2 runtime (imports/executes the written module)
must default to OFF and be switchable via a discoverable config file as well
as env var. This test pins that precedence so the safe-default can't silently
regress (= anti-flame: a reviewer can audit one file and see Phase 2 is off).

実走: cd algebraic-filter && python -m pytest samples/violations/tests/test_af_phase4_config.py -v
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from af_phase4 import config  # noqa: E402


def _clear_env() -> None:
    for k in ("AF_HOOK_PHASE2_PBT", "AF_FEEDBACK_SHAPE", "AF_CONFIG_PATH"):
        os.environ.pop(k, None)


def test_safe_default_phase2_off() -> None:
    """設定ファイル / env 不在時、 Phase 2 runtime は安全 default OFF"""
    saved = {k: os.environ.get(k) for k in ("AF_HOOK_PHASE2_PBT", "AF_CONFIG_PATH")}
    try:
        _clear_env()
        # cwd に設定ファイルが無い前提 (= AF_CONFIG_PATH を存在しない先に向ける)
        os.environ["AF_CONFIG_PATH"] = str(REPO_ROOT / "_no_such_config.json")
        assert config.resolve_bool("phase2_runtime", "AF_HOOK_PHASE2_PBT") is False
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_config_file_enables_phase2() -> None:
    """設定ファイルで phase2_runtime=true → 有効 (env 不在時)"""
    saved = {k: os.environ.get(k) for k in ("AF_HOOK_PHASE2_PBT", "AF_CONFIG_PATH")}
    try:
        _clear_env()
        cfg = REPO_ROOT / "_test_af_config.json"
        cfg.write_text(json.dumps({"phase2_runtime": True}), encoding="utf-8")
        os.environ["AF_CONFIG_PATH"] = str(cfg)
        try:
            assert config.resolve_bool("phase2_runtime", "AF_HOOK_PHASE2_PBT") is True
        finally:
            cfg.unlink(missing_ok=True)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_env_overrides_config_file() -> None:
    """env var が設定ファイルより優先 (= file で false でも env で true なら true)"""
    saved = {k: os.environ.get(k) for k in ("AF_HOOK_PHASE2_PBT", "AF_CONFIG_PATH")}
    try:
        _clear_env()
        cfg = REPO_ROOT / "_test_af_config2.json"
        cfg.write_text(json.dumps({"phase2_runtime": False}), encoding="utf-8")
        os.environ["AF_CONFIG_PATH"] = str(cfg)
        os.environ["AF_HOOK_PHASE2_PBT"] = "1"
        try:
            assert config.resolve_bool("phase2_runtime", "AF_HOOK_PHASE2_PBT") is True
        finally:
            cfg.unlink(missing_ok=True)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_feedback_shape_resolution() -> None:
    """feedback_shape も env > file > default (= verbose) で解決、 不正値は default"""
    saved = {k: os.environ.get(k) for k in ("AF_FEEDBACK_SHAPE", "AF_CONFIG_PATH")}
    try:
        _clear_env()
        valid = ("verbose", "minimal", "skeleton_only")
        # default
        os.environ["AF_CONFIG_PATH"] = str(REPO_ROOT / "_no_such_config.json")
        assert config.resolve_str("feedback_shape", "AF_FEEDBACK_SHAPE", valid) == "verbose"
        # file
        cfg = REPO_ROOT / "_test_af_config3.json"
        cfg.write_text(json.dumps({"feedback_shape": "minimal"}), encoding="utf-8")
        os.environ["AF_CONFIG_PATH"] = str(cfg)
        try:
            assert config.resolve_str("feedback_shape", "AF_FEEDBACK_SHAPE", valid) == "minimal"
            # env override
            os.environ["AF_FEEDBACK_SHAPE"] = "skeleton_only"
            assert config.resolve_str("feedback_shape", "AF_FEEDBACK_SHAPE", valid) == "skeleton_only"
            # invalid env → default
            os.environ["AF_FEEDBACK_SHAPE"] = "bogus"
            os.environ["AF_CONFIG_PATH"] = str(REPO_ROOT / "_no_such_config.json")
            assert config.resolve_str("feedback_shape", "AF_FEEDBACK_SHAPE", valid) == "verbose"
        finally:
            cfg.unlink(missing_ok=True)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_phase2_runner_honors_config_file() -> None:
    """phase2_runner.is_enabled() が config 層経由で設定ファイルを尊重する"""
    saved = {k: os.environ.get(k) for k in ("AF_HOOK_PHASE2_PBT", "AF_CONFIG_PATH")}
    try:
        _clear_env()
        from af_phase4 import phase2_runner

        importlib.reload(config)
        cfg = REPO_ROOT / "_test_af_config4.json"
        cfg.write_text(json.dumps({"phase2_runtime": True}), encoding="utf-8")
        os.environ["AF_CONFIG_PATH"] = str(cfg)
        try:
            assert phase2_runner.is_enabled() is True
        finally:
            cfg.unlink(missing_ok=True)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
