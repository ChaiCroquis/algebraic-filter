"""
ground truth (fixed) for sim300_yoda_conditions
expected_detection_after_fix: ruff SIM should find NO violations (exit 0)
"""


def check_status(status: int) -> str:
    if status == 0:
        return "ok"
    return "error"
