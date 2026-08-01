# _telegram_listener.py — 上行通信員入口（CLI wrapper）
# python _telegram_listener.py --mode once   # 消化 pending 即退出
# python _telegram_listener.py --mode loop   # 常駐長輪詢
#
# 薄層委託 Telegram_Listener_Agent.main()；此處僅保留為 PowerShell 相容入口。

from __future__ import annotations

import os
import sys

_workflows = os.path.dirname(os.path.abspath(__file__))
_agents_core = os.path.normpath(os.path.join(_workflows, "..", "02_Agents_Core"))
for _p in (_agents_core, _workflows):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from Telegram_Listener_Agent import main  # type: ignore

if __name__ == "__main__":
    raise SystemExit(main())
