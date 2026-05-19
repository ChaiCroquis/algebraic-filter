"""tracemalloc driver for #dict_keys_list_for_iter.

期待結果: find_key の list(d.keys()) で中間 list allocation が観測される
"""
import sys
import tracemalloc
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SAMPLES_DIR))

from dict_keys_list_for_iter import find_key  # noqa: E402


def main() -> None:
    tracemalloc.start()
    d = {f"key{i}": i for i in range(1000)}
    snap_before = tracemalloc.take_snapshot()
    result = find_key(d, 500)
    snap_after = tracemalloc.take_snapshot()
    print(f"searched {len(d)} keys -> found {result}")
    print("\n--- Top 5 allocation diffs (find_key call) ---")
    diff = snap_after.compare_to(snap_before, "lineno")
    for stat in diff[:5]:
        print(stat)
    tracemalloc.stop()


if __name__ == "__main__":
    main()
