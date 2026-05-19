"""pytest collection guard: violation-detection tests を default collect から外す。

これら test ファイルは unfixed sample に対する FAIL (= 違反検出 PASS) 期待のため、
直接 pytest 実走時に session 全体を FAIL にしてしまう。
test_manifest_driven.py が subprocess 経由でこれら test を起動し、
manifest entry の expected_exit_code 1 + expected_output_marker を assert することで wrap する。
"""

collect_ignore_glob = [
    "test_functor_*.py",
    "test_fmap_*.py",
    "test_foldable_*.py",
    "test_monad_*.py",
    "test_commutativity_*.py",
    "test_idempotence_*.py",
    "test_monoid_*.py",
    "test_weighted_*.py",
    "test_concat_*.py",
    "test_intersect_*.py",
]
