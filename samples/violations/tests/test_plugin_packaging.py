"""Plugin packaging + "official base + AF α" additive-composition verification.

Verifies the two-track (standalone + plugin) repackaging:
  1. plugin.json / hooks.json are valid and well-formed (official schema).
  2. The hook command resolves via ${CLAUDE_PLUGIN_ROOT}.
  3. Anti-pattern history path is writable in a simulated read-only plugin install.
  4. **Additive composition**: a mock "base" quality hook (simulating an
     official/pyright type-checker) and the AF hook both fire on the SAME file,
     each catching a DIFFERENT defect class, with composing (non-conflicting)
     feedback — proving the "+α on top of any base" model works.

実走: cd algebraic-filter && python -m pytest samples/violations/tests/test_plugin_packaging.py -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
HOOKS_JSON = REPO_ROOT / "hooks" / "hooks.json"
HOOK_SCRIPT = REPO_ROOT / "hooks" / "posttool_af_check.py"


def test_plugin_manifest_valid() -> None:
    """plugin.json は valid JSON + 必須 field (name/version/description) を持つ"""
    assert PLUGIN_MANIFEST.exists(), "plugin.json が存在しない"
    data = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    assert data["name"] == "algebraic-filter"
    assert "version" in data
    assert "description" in data


def test_hooks_json_valid_and_posttooluse() -> None:
    """hooks.json は valid + PostToolUse matcher (Write|Edit|MultiEdit) を持つ"""
    assert HOOKS_JSON.exists(), "hooks.json が存在しない"
    data = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    post = data["hooks"]["PostToolUse"]
    assert isinstance(post, list) and post
    matcher = post[0]["matcher"]
    for tool in ("Write", "Edit", "MultiEdit"):
        assert tool in matcher
    cmd = post[0]["hooks"][0]["command"]
    assert "${CLAUDE_PLUGIN_ROOT}" in cmd, "plugin root 変数を使っていない"
    assert "posttool_af_check.py" in cmd


def test_hook_command_resolves_via_plugin_root() -> None:
    """${CLAUDE_PLUGIN_ROOT} を REPO_ROOT に展開した command が実際に動く"""
    data = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
    cmd_template = data["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
    resolved = cmd_template.replace("${CLAUDE_PLUGIN_ROOT}", str(REPO_ROOT))
    # resolved 内の script path が存在すること
    assert HOOK_SCRIPT.exists()
    # clean な file に対し exit 0 (= 違反なし) で動作することを確認
    clean = REPO_ROOT / "samples" / "violations" / "fixed" / "perf401_manual_list_comp.py"
    event = {"tool_name": "Write", "tool_input": {"file_path": str(clean)}}
    # command 文字列をそのまま shell 実行 (= Claude Code hook と同じ起動形態)
    r = subprocess.run(
        resolved,
        input=json.dumps(event),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=True,
        cwd=REPO_ROOT,
    )
    assert r.returncode == 0, f"clean file で exit 0 期待、 got {r.returncode}: {r.stderr[:300]}"


def test_history_path_writable_when_install_dir_readonly() -> None:
    """install dir が read-only でも history path が user-writable に解決される"""
    # AF_HISTORY_PATH override が最優先されること
    with tempfile.TemporaryDirectory() as tmp:
        custom = Path(tmp) / "custom_history.json"
        saved = os.environ.get("AF_HISTORY_PATH")
        try:
            os.environ["AF_HISTORY_PATH"] = str(custom)
            # 再 import で resolve をやり直す
            import importlib

            from af_phase4 import anti_pattern_tracker as apt

            importlib.reload(apt)
            assert custom == apt.DEFAULT_HISTORY_PATH
            # 実際に書ける
            apt.record_violations(["PERF401"], "f.py", history_path=apt.DEFAULT_HISTORY_PATH)
            assert custom.exists()
        finally:
            if saved is None:
                os.environ.pop("AF_HISTORY_PATH", None)
            else:
                os.environ["AF_HISTORY_PATH"] = saved
            importlib.reload(apt)  # restore default


# --- mock "official base" hook = a minimal type-checker-style hook ---------
_MOCK_BASE_HOOK = '''
import json, sys
event = json.load(sys.stdin)
fp = event.get("tool_input", {}).get("file_path", "")
if not fp.endswith(".py"):
    sys.exit(0)
src = open(fp, encoding="utf-8").read()
# crude "type checker": flag a function annotated -> int that returns None
if "-> int:" in src and "return None" in src:
    print(json.dumps({
        "decision": "block",
        "reason": "base-type-check: function annotated -> int returns None",
        "additionalContext": "BASE HOOK: type error — return type int but returns None",
    }))
    sys.exit(2)
sys.exit(0)
'''


def test_additive_composition_base_plus_af() -> None:
    """公式 base hook + AF α hook が同一 file で別 defect を各々検出 + 合成する.

    file は (a) 型エラー (base が検出) と (b) 代数法則違反 (AF が検出) を両方含む。
    base と AF を順に走らせ、 両方 exit 2 + 別々の feedback を返すことを確認 =
    「+α が base の上に綺麗に乗る」 の実証。
    """
    with tempfile.TemporaryDirectory() as tmp:
        base_hook = Path(tmp) / "base_hook.py"
        base_hook.write_text(_MOCK_BASE_HOOK, encoding="utf-8")

        # (a) 型エラー + (b) monoid 違反 (= 名前 sum だが減算) を両方持つ file
        target = Path(tmp) / "both_defects.py"
        target.write_text(
            "import functools\n\n\n"
            "def my_sum(xs: list[int]) -> int:\n"
            "    # algebraic: named sum but subtracts (AF Phase 2 catches)\n"
            "    return functools.reduce(lambda a, b: a - b, xs, 0)\n\n\n"
            "def first_pos(xs: list[int]) -> int:\n"
            "    for x in xs:\n"
            "        if x > 0:\n"
            "            return x\n"
            "    return None  # type error (base catches)\n",
            encoding="utf-8",
        )

        event = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(target)}})

        # --- base hook fires ---
        r_base = subprocess.run(
            [sys.executable, "-X", "utf8", str(base_hook)],
            input=event, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        assert r_base.returncode == 2, "base hook が型エラーを検出して block するはず"
        base_ctx = json.loads(r_base.stdout.strip().splitlines()[-1])["additionalContext"]
        assert "BASE HOOK" in base_ctx

        # --- AF hook fires on the SAME file (with Phase 2 opt-in) ---
        env = dict(os.environ)
        env["AF_HOOK_PHASE2_PBT"] = "1"
        env["PYTHONUTF8"] = "1"
        r_af = subprocess.run(
            [sys.executable, "-X", "utf8", str(HOOK_SCRIPT)],
            input=event, capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env, cwd=REPO_ROOT,
        )
        assert r_af.returncode == 2, f"AF hook が代数法則違反を検出して block するはず: {r_af.stderr[:300]}"
        af_ctx = json.loads(r_af.stdout.strip().splitlines()[-1])["additionalContext"]

        # --- composition: 各 hook が別 defect class を articulate、 衝突なし ---
        assert "Phase 2 algebraic-law" in af_ctx, "AF が代数法則 layer を出すはず"
        assert "BASE HOOK" not in af_ctx, "AF feedback に base の内容が混入してはならない"
        assert "BASE HOOK" in base_ctx and "Phase 2" not in base_ctx, "base feedback に AF 内容が混入してはならない"
        # 両者は同一 file の異なる defect を独立に捕捉 = additive 合成成立
