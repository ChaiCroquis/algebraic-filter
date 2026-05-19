"""Scalpel CFG (Control Flow Graph) を使った関数間 data flow articulate.

container 内で実行、 stdout に JSON 出力で AF main env (Windows native) に bridge.

Usage:
    python -m af_phase3_scalpel.cfg_analyzer <file_path>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def analyze(file_path: str) -> dict:
    """Python file の CFG + 関数 list を取得."""
    try:
        from scalpel.cfg import CFGBuilder
    except ImportError as e:
        return {"error": f"scalpel import failed: {e}"}

    source = Path(file_path).read_text(encoding="utf-8")
    try:
        cfg = CFGBuilder().build_from_src(name=Path(file_path).stem, src=source)
    except Exception as e:
        return {"error": f"CFG build failed: {type(e).__name__}: {e}"}

    functions = []
    for fname, sub_cfg in (cfg.functioncfgs or {}).items():
        functions.append(
            {
                "function_name": fname,
                "block_count": len(list(sub_cfg)) if hasattr(sub_cfg, "__iter__") else 0,
            }
        )

    return {
        "file": file_path,
        "module_cfg_blocks": len(list(cfg)) if hasattr(cfg, "__iter__") else 0,
        "function_cfgs": functions,
        "function_count": len(functions),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: cfg_analyzer <file_path>"}))
        return 1
    result = analyze(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())
