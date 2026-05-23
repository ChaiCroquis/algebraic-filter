"""AF CI ランナー: profile が有効化した層を渡されたファイル群に適用し、 違反で exit 非ゼロ.

write-time profile では重い証明層 (phase2/CrossHair) を skip し hook と同じ軽量、
ci profile で重い証明まで全層を走らせる (= コストで二層を綺麗に分割)。

使い方:
    AF_PROFILE=ci python scripts/af_ci.py <changed>.py ...   # CI/CD: 全層
    python scripts/af_ci.py <files>.py ...                   # 既定 write-time: 軽量層のみ

exit code: 違反合計 > 0 で 1、 さもなくば 0。 純粋性は情報として表示 (合否に含めない)。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

SELECT_RULES = "PERF,SIM,FURB,ANN,F,RUF013"


def _ruff_violations(path: str) -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", f"--select={SELECT_RULES}", path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    m = re.search(r"Found (\d+) error", out)
    return int(m.group(1)) if m else 0


def main(argv: list[str]) -> int:
    paths = [p for p in argv[1:] if p.endswith(".py")]
    if not paths:
        print("usage: [AF_PROFILE=ci] python scripts/af_ci.py <file>.py ...")
        return 2

    from af_phase3.purity_checker import check_purity_file
    from af_phase3.static_checker import check_file
    from af_phase4.config import resolve_profile
    from af_phase4.phase2_runner import collect_phase2_failures

    profile = resolve_profile()
    total = 0
    for p in paths:
        ruff_n = _ruff_violations(p)
        phase3_n = len(check_file(p))
        # phase2 (laws + CrossHair) は config 経由で自動 gate (write-time profile では [] )
        phase2_n = len(collect_phase2_failures(p))
        impurity = len(check_purity_file(p))
        n = ruff_n + phase3_n + phase2_n
        total += n
        print(f"{p}: ruff={ruff_n} phase3={phase3_n} phase2={phase2_n} (impurity_info={impurity})")

    print(f"profile={profile} total_violations={total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
