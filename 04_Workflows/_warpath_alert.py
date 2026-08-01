"""_warpath_alert.py — thin CLI wrapper. 核心邏輯已合併至 _report_generator.py。

用法同前：python _warpath_alert.py "<message>"
→ 委託 _report_generator.send_alert()

Merge history:
  2026-07-29 合併 _warpath_alert → _report_generator (send_alert() 函式)
"""
from __future__ import annotations

import os
import sys

_workflows = os.path.dirname(os.path.abspath(__file__))
if _workflows not in sys.path:
    sys.path.insert(0, _workflows)

from _tang_paths import bootstrap_sys_path  # type: ignore[import-untyped]

_here = os.path.dirname(os.path.abspath(__file__))
bootstrap_sys_path(_here)

from _report_generator import send_alert  # type: ignore[import-untyped]


def main() -> int:
    if len(sys.argv) < 2:
        print("[warpath-alert] usage: _warpath_alert.py <message>", file=sys.stderr)
        return 2
    text = " ".join(sys.argv[1:]).strip()
    if not text:
        print("[warpath-alert] empty message", file=sys.stderr)
        return 2
    return send_alert(text)


if __name__ == "__main__":
    raise SystemExit(main())
