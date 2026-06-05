"""_warpath_alert.py — Launch-Warpath 用：透過 _telegram_alert 發送一段純文字。

用法：
    python _warpath_alert.py "<message>"

policy：
  · 只負責轉發 stdin/argv 文字到 _telegram_alert，不接受任何金鑰原文輸出。
  · 失敗以 exit code 1 回報，但**不**將 token 印至終端。
"""
from __future__ import annotations

import os
import sys

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
bootstrap_sys_path(_here)

from Code_Cleaner_Throttled_Agent import _telegram_alert  # type: ignore
from GroqHybridRecovery_Agent import format_groq_quota_telegram_suffix  # type: ignore


def main() -> int:
    if len(sys.argv) < 2:
        print("[warpath-alert] usage: _warpath_alert.py <message>", file=sys.stderr)
        return 2
    text = " ".join(sys.argv[1:]).strip()
    if not text:
        print("[warpath-alert] empty message", file=sys.stderr)
        return 2
    try:
        ammo, cost = format_groq_quota_telegram_suffix()
        text = text + "\n" + ammo + "\n" + cost
    except Exception:  # noqa: BLE001
        pass
    try:
        _telegram_alert(text)
    except Exception as e:  # noqa: BLE001
        print(f"[warpath-alert] failed: {type(e).__name__}", file=sys.stderr)
        return 1
    print("[warpath-alert] sent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
