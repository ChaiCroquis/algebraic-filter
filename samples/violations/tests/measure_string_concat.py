"""tracemalloc driver for #string_concat_in_loop.

期待結果: concat_all の += loop で string allocation が複数回観測される
"""
import sys
import tracemalloc
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SAMPLES_DIR))

from string_concat_in_loop import concat_all  # noqa: E402


def main() -> None:
    tracemalloc.start()
    parts = [f"part{i}" for i in range(500)]
    snap_before = tracemalloc.take_snapshot()
    result = concat_all(parts)
    snap_after = tracemalloc.take_snapshot()
    print(f"concatenated {len(parts)} parts -> {len(result)} chars")
    print("\n--- Top 5 allocation diffs (concat_all call) ---")
    diff = snap_after.compare_to(snap_before, "lineno")
    for stat in diff[:5]:
        print(stat)
    tracemalloc.stop()


if __name__ == "__main__":
    main()
