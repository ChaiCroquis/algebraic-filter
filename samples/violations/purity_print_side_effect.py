"""
violation: purity violation (print side effect in a pure-named function)
expected_detection: custom ruff rule (Phase 1+ AF original) or CrossHair with @pure contract
expected_skeleton: pure function (no I/O, no global mutation)
expected_fix:
    def calc(x: int) -> int:
        return x * 2
"""


def calc(x: int) -> int:
    # function name "calc" implies pure computation
    # but print(...) is an I/O side effect → impure
    print(f"calc({x})")
    return x * 2
