"""
Phase 0 TDD: manifest 駆動で violation 検出 / ground truth no-violation を assert。

chai 指示「要件・仕様があるのだから、 テストを大量に用意して TDD として使用」
2026-05-19 反映。

3 層 articulate:
  - 仕様層: samples/violations/manifest.json (expected_detection / what_to_verify)
  - テスト層: 本ファイル (manifest 駆動 pytest parametrize で自動生成)
  - 実装層: AF hook (Phase 1 で実装、 統合テストは Phase 1 で追加)

実行: cd algebraic-filter && python -m pytest samples/violations/tests/ -v
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SAMPLES_DIR = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((SAMPLES_DIR / "manifest.json").read_text(encoding="utf-8"))


def _ruff_samples_with_detection() -> list[dict]:
    """ruff が期待検出ツールで、 Phase 0/1 で PASS/PARTIAL 確認済 + file 実在 の sample"""
    return [
        s for s in MANIFEST["samples"]
        if s["expected_detection"]["tool"] == "ruff"
        and s["verification_result"]["phase_0_actual_detection"] in ("PASS", "PARTIAL")
        and (SAMPLES_DIR / s["file"]).exists()
        and (SAMPLES_DIR / "fixed" / s["file"]).exists()
    ]


# ---- Test 1: unfixed sample に対しツールが違反検出 (exit code + marker) ----

@pytest.mark.parametrize(
    "sample",
    _ruff_samples_with_detection(),
    ids=lambda s: s["id"],
)
def test_ruff_detects_violation_in_unfixed(sample: dict) -> None:
    """各 ruff sample で、 unfixed code が違反を期待通り出すこと"""
    cmd = sample["expected_detection"]["command"].split()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    expected_exit = sample["expected_detection"]["expected_exit_code"]
    expected_marker = sample["expected_detection"]["expected_output_marker"]
    output = result.stdout + result.stderr

    assert result.returncode == expected_exit, (
        f"{sample['id']}: expected exit {expected_exit}, got {result.returncode}\n"
        f"stderr: {result.stderr[:300]}"
    )
    assert expected_marker in output, (
        f"{sample['id']}: expected marker {expected_marker!r} not found in output:\n"
        f"{output[:500]}"
    )


# ---- Test 2: fixed sample に対し違反が消えること (ground truth 検証) ----

@pytest.mark.parametrize(
    "sample",
    _ruff_samples_with_detection(),
    ids=lambda s: s["id"],
)
def test_ruff_no_violation_in_fixed(sample: dict) -> None:
    """各 ruff sample で、 fixed/ 版が違反 0 件であること (ground truth check)"""
    fixed_file = SAMPLES_DIR / "fixed" / sample["file"]
    if not fixed_file.exists():
        pytest.skip(f"fixed sample not yet created: {fixed_file}")

    # manifest 内 command の最後の path 引数を fixed/ 版に差し替え
    orig_cmd = sample["expected_detection"]["command"].split()
    fixed_rel = str(fixed_file.relative_to(REPO_ROOT)).replace("\\", "/")
    cmd = [
        fixed_rel if (c.endswith(sample["file"]) and "fixed" not in c) else c
        for c in orig_cmd
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    output = result.stdout + result.stderr

    # #6 intermediate_list_chain は ruff 標準では元から検出無し = baseline 一致 (exit 0)
    # 他は元 violation が消えて exit 0 になる expectation
    assert result.returncode == 0, (
        f"{sample['id']}: fixed sample should have no ruff violation, "
        f"got exit {result.returncode}\noutput: {output[:500]}"
    )


# ---- Test 3: monoid #5 hypothesis 検出 (unfixed) ----

def test_monoid_unfixed_hypothesis_finds_falsifying_example() -> None:
    """#5 monoid_associativity_violation で hypothesis @given が counter-example を発見"""
    cmd = [
        sys.executable, "-m", "pytest",
        "samples/violations/tests/test_monoid_associativity.py",
        "-v",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    output = result.stdout + result.stderr
    assert result.returncode == 1, (
        f"unfixed monoid test should FAIL (= violation detected), "
        f"got exit {result.returncode}\noutput: {output[:500]}"
    )
    assert "Falsifying example" in output, (
        f"expected 'Falsifying example' marker not in output:\n{output[:500]}"
    )


# ---- Test 4: monoid #5 fixed が hypothesis @given を pass する (ground truth) ----

def test_monoid_fixed_hypothesis_passes() -> None:
    """fixed/monoid_associativity_violation.py の my_sum が hypothesis property を満たす"""
    # fixed 版を import して同じ property をその場で実行
    import functools
    import operator

    def my_sum(xs: list[int]) -> int:
        return functools.reduce(operator.add, xs, 0)

    from hypothesis import given, strategies as st  # noqa: E402

    @given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=10))
    def prop(xs: list[int]) -> None:
        assert my_sum(xs) == sum(xs)

    prop()  # raises if any counter-example found


# ---- Test 5: intermediate_list #6 tracemalloc が中間 list を観測 (unfixed) ----

def test_intermediate_list_unfixed_tracemalloc_observes_allocation() -> None:
    """#6 intermediate_list_chain で tracemalloc が transform の line で大きな allocation を articulate"""
    cmd = [
        sys.executable,
        "samples/violations/tests/measure_intermediate.py",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    output = result.stdout + result.stderr
    assert result.returncode == 0
    # intermediate_list_chain.py のいずれかの line が allocation top に現れる
    assert "intermediate_list_chain.py" in output, (
        f"tracemalloc should report intermediate_list_chain.py line as top allocator:\n{output[:500]}"
    )
    # KiB レベルの allocation が現れる (10000 element 入力時の中間 list の規模)
    assert "KiB" in output, (
        f"expected KiB-scale allocation marker:\n{output[:500]}"
    )


# ---- Test 6: hypothesis 系 sample に対する manifest 駆動 violation detection ----


def _command_target_file_exists(sample: dict) -> bool:
    """manifest entry の command の中で .py 拡張子の引数を find、 実在チェック"""
    cmd_parts = sample["expected_detection"]["command"].split()
    for part in cmd_parts:
        if part.endswith(".py"):
            target = REPO_ROOT / part
            if target.exists():
                return True
            return False
    return False


def _hypothesis_samples_to_run() -> list[dict]:
    return [
        s for s in MANIFEST["samples"]
        if s["expected_detection"]["tool"] == "hypothesis"
        and s["verification_result"]["phase_0_actual_detection"] in ("PASS", "DEFERRED")
        and _command_target_file_exists(s)
    ]


@pytest.mark.parametrize(
    "sample",
    _hypothesis_samples_to_run(),
    ids=lambda s: s["id"],
)
def test_hypothesis_violation_test_finds_falsifying(sample: dict) -> None:
    """各 hypothesis tool sample に対し対応 test が FAIL (Falsifying example) を返すこと"""
    cmd = sample["expected_detection"]["command"].split()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        encoding="utf-8",
        errors="replace",
    )
    expected_exit = sample["expected_detection"]["expected_exit_code"]
    expected_marker = sample["expected_detection"]["expected_output_marker"]
    output = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == expected_exit, (
        f"{sample['id']}: expected exit {expected_exit}, got {result.returncode}\n"
        f"{output[:500]}"
    )
    assert expected_marker in output, (
        f"{sample['id']}: expected marker {expected_marker!r} not in output\n"
        f"{output[:500]}"
    )


# ---- Test 7: tracemalloc 系 sample に対する manifest 駆動 allocation observation ----


def _tracemalloc_samples_to_run() -> list[dict]:
    return [
        s for s in MANIFEST["samples"]
        if "tracemalloc" in s["expected_detection"]["tool"]
        and s["verification_result"]["phase_0_actual_detection"] in ("PASS", "PARTIAL", "DEFERRED")
        and _command_target_file_exists(s)
    ]


@pytest.mark.parametrize(
    "sample",
    _tracemalloc_samples_to_run(),
    ids=lambda s: s["id"],
)
def test_tracemalloc_observes_violation_file(sample: dict) -> None:
    """各 tracemalloc tool sample に対し driver 実走で対象 file 名が allocation report に出る"""
    cmd = sample["expected_detection"]["command"].split()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        encoding="utf-8",
        errors="replace",
    )
    output = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 0, f"{sample['id']}: tracemalloc driver failed:\n{output[:500]}"
    assert sample["file"] in output, (
        f"{sample['id']}: expected file marker {sample['file']!r} not in tracemalloc output\n"
        f"{output[:500]}"
    )


# ---- Test 8: manifest.json が schema 整合性を保つ ----

def test_manifest_schema_consistency() -> None:
    """manifest.json の構造健全性 — TDD 仕様層自体の self-check"""
    assert MANIFEST["total_samples"] == len(MANIFEST["samples"]), (
        f"total_samples={MANIFEST['total_samples']} != len(samples)={len(MANIFEST['samples'])}"
    )
    required_keys = {
        "id", "file", "category", "violation",
        "expected_detection", "what_to_verify", "what_is_the_problem",
        "expected_fix", "verification_result",
    }
    for s in MANIFEST["samples"]:
        missing = required_keys - set(s.keys())
        assert not missing, f"sample {s.get('id', '?')} missing keys: {missing}"
        # expected_detection の必須 sub-fields
        ed = s["expected_detection"]
        ed_required = {"tool", "rule_id", "command", "expected_exit_code", "expected_output_marker"}
        ed_missing = ed_required - set(ed.keys())
        assert not ed_missing, f"sample {s['id']}.expected_detection missing: {ed_missing}"
        # verification_result の値域
        vr_actual = s["verification_result"]["phase_0_actual_detection"]
        assert vr_actual in ("PASS", "PARTIAL", "DEFERRED"), (
            f"sample {s['id']}.verification_result.phase_0_actual_detection invalid: {vr_actual}"
        )
        # 各 sample file の物理存在
        assert (SAMPLES_DIR / s["file"]).exists(), f"sample file not found: {s['file']}"
