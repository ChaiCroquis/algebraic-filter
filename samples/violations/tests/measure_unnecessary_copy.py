"""tracemalloc driver for #unnecessary_copy_chain.

期待結果: unnecessary_copy_chain.py の process 内で複数の中間 list (copy / slice / list())
が allocation tracker に line-level で articulate される。
"""
import sys
import tracemalloc
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SAMPLES_DIR))

from unnecessary_copy_chain import process  # noqa: E402


def main() -> None:
    tracemalloc.start()
    data = list(range(10000))
    snap_before = tracemalloc.take_snapshot()
    result = process(data)
    snap_after = tracemalloc.take_snapshot()
    print(f"processed {len(data)} -> {len(result)} items")
    print("\n--- Top 5 allocation diffs (process call) ---")
    diff = snap_after.compare_to(snap_before, "lineno")
    for stat in diff[:5]:
        print(stat)
    tracemalloc.stop()


if __name__ == "__main__":
    main()
