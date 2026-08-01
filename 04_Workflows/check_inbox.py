#!/usr/bin/env python3
"""Inbox scanner — thin CLI wrapper. 核心邏輯已合併至 _inbound_watchdog.py。

用法同前：python check_inbox.py
→ 委託 _inbound_watchdog.py --inbox-check

Merge history:
  2026-07-29 合併 check_inbox → _inbound_watchdog (check_inbox() 函式 + --inbox-check CLI)
"""
from __future__ import annotations

import os
import sys

_workflows = os.path.dirname(os.path.abspath(__file__))
if _workflows not in sys.path:
    sys.path.insert(0, _workflows)

from _inbound_watchdog import check_inbox  # type: ignore[import-untyped]

def main():
    result = check_inbox()
    if result["status"] == "has_work":
        print(f"📬 收到 {result['count']} 個新檔案：")
        for f in result["files"]:
            print(f"  - {f['name']} ({f['size_kb']} KB)")
    else:
        print("📭 目前沒有新工作")
    return result

if __name__ == "__main__":
    main()
