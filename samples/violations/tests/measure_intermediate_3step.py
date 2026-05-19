"""tracemalloc driver for #multi_step_intermediate_chain.

期待結果: multi_step_intermediate_chain.py の transform_3_steps line で
3 段の中間 list materialization が allocation tracker に line-level で articulate される。
"""
import sys
import tracemalloc
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SAMPLES_DIR))

from multi_step_intermediate_chain import transform_3_steps  # noqa: E402


def main() -> None:
    tracemalloc.start()
    data = list(range(10000))
    snap_before = tracemalloc.take_snapshot()
    result = transform_3_steps(data)
    snap_after = tracemalloc.take_snapshot()
    print(f"transformed {len(data)} -> {len(result)} items")
    print("\n--- Top 5 allocation diffs (transform_3_steps call) ---")
    diff = snap_after.compare_to(snap_before, "lineno")
    for stat in diff[:5]:
        print(stat)
    tracemalloc.stop()


if __name__ == "__main__":
    main()
