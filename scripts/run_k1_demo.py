#!/usr/bin/env python
"""Minimal demo runner for K-1 LangGraph e2e."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.langgraph_flow_k1 import run_k1_flow


def main() -> int:
    out = run_k1_flow()
    summary = {
        "ok": out.get("ok"),
        "message": out.get("message"),
        "success": (out.get("record") or {}).get("success"),
        "retry_count": (out.get("record") or {}).get("retry_count"),
        "handoff_count": (out.get("record") or {}).get("handoff_count"),
        "context_token_usage": (out.get("record") or {}).get("context_token_usage"),
        "trace_completeness": (out.get("record") or {}).get("trace_completeness"),
        "final_result_ok": ((out.get("state") or {}).get("final_result") or {}).get("ok"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
