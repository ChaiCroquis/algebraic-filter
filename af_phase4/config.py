"""AF 設定の集約スイッチ層 (= 監査可能 + 安全 default).

危険 / 重い挙動 (= Phase 2 runtime の target import 実行など) を、  env var だけ
でなく **可視の設定ファイル** で切替できるようにする。 security レビュー時に
「default で何が ON か」 を 1 ファイルで確認できる = 叩かれにくい設計。

優先順位 (= 高い方が勝つ):
    1. 環境変数 (= CI / 一時的 override)
    2. 設定ファイル `.algebraic-filter.json` (= cwd、 または AF_CONFIG_PATH)
    3. ハードコードされた安全 default (= 危険挙動は全て OFF)

設定ファイル例 (`.algebraic-filter.json`):
    {
      "phase2_runtime": false,     # target module を import 実行 (危険、 default OFF)
      "feedback_shape": "verbose"  # verbose / skeleton_only / minimal
    }
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_FILENAME = ".algebraic-filter.json"

# 安全 default (= 危険 / 重い挙動は全て OFF / 最小)
_SAFE_DEFAULTS: dict[str, Any] = {
    "phase2_runtime": False,
    "feedback_shape": "verbose",
    "crosshair_verify": False,
}

_TRUE_TOKENS = ("1", "true", "on", "yes")

# profile = コスト層の束 (= write-time の軽量ガード / CI の重い証明 を 1 スイッチで分割)。
# write-time: 重い決定論証明 (phase2 sampling / CrossHair / 契約) は OFF = hook を軽く保つ。
# ci: 重い証明まで全て ON (= CI/CD で時間予算がある層)。
# 個別スイッチ (env/file) は profile より優先 (= 1 層だけ上書き可)。
_PROFILES = ("write-time", "ci")
_DEFAULT_PROFILE = "write-time"
_PROFILE_DEFAULTS: dict[str, dict[str, bool]] = {
    "write-time": {"phase2_runtime": False, "crosshair_verify": False},
    "ci": {"phase2_runtime": True, "crosshair_verify": True},
}


def resolve_profile() -> str:
    """profile を env AF_PROFILE > file "profile" > 既定 write-time の順で解決."""
    env = os.environ.get("AF_PROFILE", "").strip().lower()
    if env in _PROFILES:
        return env
    cfg = load_config()
    val = cfg.get("profile")
    if isinstance(val, str) and val in _PROFILES:
        return val
    return _DEFAULT_PROFILE


def _config_path() -> Path:
    override = os.environ.get("AF_CONFIG_PATH", "").strip()
    if override:
        return Path(override)
    return Path.cwd() / CONFIG_FILENAME


def load_config() -> dict[str, Any]:
    """設定ファイルを読む (= 不在 / 壊れていれば空 dict、 例外送出なし)."""
    path = _config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def resolve_bool(key: str, env_name: str) -> bool:
    """bool 設定値を env > file > 安全 default の順で解決."""
    env = os.environ.get(env_name, "").strip().lower()
    if env:
        return env in _TRUE_TOKENS
    cfg = load_config()
    if key in cfg:
        return bool(cfg[key])
    # profile 既定 (= 個別スイッチ未指定時、 profile が層を束ねて決める)
    prof_defaults = _PROFILE_DEFAULTS.get(resolve_profile(), {})
    if key in prof_defaults:
        return prof_defaults[key]
    return bool(_SAFE_DEFAULTS.get(key, False))


def resolve_str(key: str, env_name: str, valid: tuple[str, ...]) -> str:
    """str 設定値を env > file > 安全 default の順で解決 (= valid 外は default)."""
    default = str(_SAFE_DEFAULTS.get(key, ""))
    env = os.environ.get(env_name, "").strip().lower()
    if env in valid:
        return env
    cfg = load_config()
    val = cfg.get(key)
    if isinstance(val, str) and val in valid:
        return val
    return default
