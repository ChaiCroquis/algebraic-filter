"""
violation: string concat in loop (= O(n^2) allocation、 ''.join に置換可能)
expected_detection: tracemalloc (string intermediate allocation 観測) + 将来 ruff custom rule
"""


def concat_all(parts: list[str]) -> str:
    result = ""
    for p in parts:
        # bug: 文字列 immutable なため += で毎回 new string 生成
        result += p
    return result
