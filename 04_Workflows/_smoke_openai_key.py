"""OpenAI 單鑰盲測 — thin CLI wrapper. 核心邏輯已合併至 _core_agent_smoke.py。

用法同前：python _smoke_openai_key.py
→ 委託 _core_agent_smoke.py --smoke-openai

Merge history:
  2026-07-29 合併 _smoke_openai_key → _core_agent_smoke (smoke_openai_key() + --smoke-openai)
"""
from __future__ import annotations

import os
import sys

_workflows = os.path.dirname(os.path.abspath(__file__))
if _workflows not in sys.path:
    sys.path.insert(0, _workflows)

from _core_agent_smoke import smoke_openai_key  # type: ignore[import-untyped]

if __name__ == "__main__":
    raise SystemExit(smoke_openai_key())
