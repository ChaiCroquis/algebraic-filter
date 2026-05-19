"""
violation: 不要な copy 連鎖 (Stream Fusion 系、 list.copy / slice / list() の連鎖)
expected_detection: tracemalloc (中間 list allocation 観測)
expected_fix: 単一 comprehension で final 結果のみ生成
"""


def process(data: list[int]) -> list[int]:
    # bug: 3 つの不要 copy chain
    step1 = data.copy()
    step2 = step1[:]
    step3 = list(step2)
    return [x * 2 for x in step3]
