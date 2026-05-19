"""
Phase 0 Day 4 memray Windows 不可 → tracemalloc (stdlib) 代替 driver。

memray は Windows native 非対応 (pip install は成功するが C extension が build されず
import 不可)。Phase 0 では tracemalloc で「中間 list の materialization が観測される」
ことを示す代替計測を行う。

期待結果:
  - intermediate_list_chain.transform の line で大きな allocation が観測される
  - 中間 list (map result, filter result) の materialization が明示される
"""
import sys
import tracemalloc
from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SAMPLES_DIR))

from intermediate_list_chain import transform  # noqa: E402


def main() -> None:
    tracemalloc.start()
    data = list(range(10000))
    snapshot_before = tracemalloc.take_snapshot()
    result = transform(data)
    snapshot_after = tracemalloc.take_snapshot()
    print(f"transformed {len(data)} -> {len(result)} items")
    print("\n--- Top 5 allocation diffs (transform call) ---")
    diff = snapshot_after.compare_to(snapshot_before, "lineno")
    for stat in diff[:5]:
        print(stat)
    tracemalloc.stop()


if __name__ == "__main__":
    main()
