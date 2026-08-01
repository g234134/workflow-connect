"""_watch_refine.py — 監控精煉進度，每 15 秒 poll 進度檔案並輸出"""
import json
import os
import glob
import time
from datetime import datetime, timezone

STATUS_JSON = "D:/大唐三省六部/04_Workflows/Status.json"
REPORTS_DIR = "D:/大唐三省六部/06_Exports_Output/reports"
WAVE_BENCHMARK = os.path.join(REPORTS_DIR, "wave_benchmark.jsonl")

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def read_status():
    try:
        with open(STATUS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def read_wave_benchmark_tail():
    try:
        with open(WAVE_BENCHMARK, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if lines:
            last = json.loads(lines[-1].strip())
            return last
    except Exception:
        return None

def latest_eval_report():
    cands = glob.glob(os.path.join(REPORTS_DIR, "asset_value_eval_*.json"))
    if not cands:
        return None
    cands.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    latest = cands[0]
    try:
        with open(latest, "r", encoding="utf-8") as f:
            d = json.load(f)
        rows = d.get("rows", []) if isinstance(d, dict) else []
        return {"file": os.path.basename(latest), "rows": len(rows)}
    except Exception:
        return None

last_line_count = 0
cycles = 0

while True:
    cycles += 1
    now = utc_now()
    status = read_status()
    
    # Check wave benchmark for new entry
    bench = read_wave_benchmark_tail()
    
    # Check eval report for row count
    report_info = latest_eval_report()
    
    # Check process output file if available
    line = f"[{now}] CYCLE {cycles}"
    
    if status and "wave" in status:
        s = status["wave"] if isinstance(status["wave"], dict) else {}
        processed = s.get("processed", "?")
        of = s.get("of", "?")
        avg = s.get("avg_so_far", "?")
        grades = s.get("grades_so_far", {})
        groq_calls = s.get("groq_calls", 0)
        groq_ok = s.get("groq_success", 0)
        case_hits = s.get("case_library_hits", 0)
        local_skip = s.get("local_judge_skips", 0)
        line += f" | processed={processed}/{of} avg={avg} grades={grades}"
        line += f" | groq={groq_calls}ok={groq_ok} case_hits={case_hits} local_skip={local_skip}"
    
    if report_info:
        line += f" | eval_file={report_info['file']} rows={report_info['rows']}"
    
    print(line, flush=True)
    
    if bench:
        print(f"  [BENCHMARK] {json.dumps(bench, ensure_ascii=False)}", flush=True)
    
    if cycles >= 600:  # ~2.5 hours max
        print(f"[{now}] WATCHER_EXIT: reached max cycles", flush=True)
        break
    
    time.sleep(15)
