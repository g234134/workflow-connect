"""寫入第一波（無內建計時）的對照列：從 PowerShell 轉錄檔解析 Warpath 全鏈秒數。"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore


def _parse_transcript_sec(path: str) -> int:
    t = open(path, "r", encoding="utf-8-sig", errors="replace").read()
    m1 = re.search(r"開始時間:\s*(\d{14})", t)
    m2 = re.search(r"結束時間:\s*(\d{14})", t)
    if not m1 or not m2:
        return 0
    a = datetime.strptime(m1.group(1), "%Y%m%d%H%M%S")
    b = datetime.strptime(m2.group(1), "%Y%m%d%H%M%S")
    return int((b - a).total_seconds())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--wave-n", type=int, default=30000)
    ap.add_argument("--groq-calls", type=int, default=0)
    ap.add_argument("--groq-success", type=int, default=0)
    ap.add_argument("--transcript", default="", help="last_run.log；預設 scheduler/last_run.log")
    args = ap.parse_args()

    root = get_tang_gov_root()
    rep = resolve_agent_output_path(root, "06_Exports_Output", "reports")
    tr = args.transcript.strip() or os.path.join(
        root, "06_Exports_Output", "reports", "scheduler", "last_run.log"
    )
    wall = _parse_transcript_sec(tr) if os.path.isfile(tr) else 0

    line = {
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label": "baseline_wave1_before_case_library_metrics",
        "run_id": args.run_id,
        "wave_n": args.wave_n,
        "factory_wall_sec": None,
        "evaluate_duration_sec": None,
        "warpath_transcript_sec": wall,
        "groq_calls": args.groq_calls,
        "groq_success": args.groq_success,
        "case_library_hits": 0,
        "case_library_loaded": 0,
    }
    out_p = os.path.join(rep, "wave_benchmark.jsonl")
    os.makedirs(rep, exist_ok=True)
    with open(out_p, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    print(json.dumps({"ok": True, "appended": out_p, "line": line}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
