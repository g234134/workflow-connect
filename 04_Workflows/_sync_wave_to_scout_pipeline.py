"""_sync_wave_to_scout_pipeline.py — 將最近一次 Asset_Value 精煉戰報寫入 scout_last_pipeline.json。

供 v2.56 _report_generator.py 讀取（虛擬節省 TWD、A 級清單等）。
"""
from __future__ import annotations

import glob
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _latest_eval_report(root: str) -> str:
    rep = resolve_agent_output_path(root, "06_Exports_Output", "reports")
    cands = glob.glob(os.path.join(rep, "asset_value_eval_*.json"))
    if not cands:
        return ""
    cands.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return cands[0]


def main() -> int:
    root = get_tang_gov_root()
    path = _latest_eval_report(root)
    if not path:
        print(json.dumps({"ok": False, "error": "no_asset_value_eval_report"}, ensure_ascii=False))
        return 2
    with open(path, "r", encoding="utf-8") as f:
        rep: Dict[str, Any] = json.load(f)

    rows: List[Dict[str, Any]] = list(rep.get("rows") or [])
    a_rows = [r for r in rows if str(r.get("grade") or "").upper() == "A"]
    a_rows.sort(key=lambda r: float(r.get("final_score") or 0), reverse=True)
    top = a_rows[:24]

    match_report: Dict[str, Any] = {
        "ok": True,
        "pool_size": int(rep.get("pool_size") or 0),
        "scanned": int(rep.get("sampled") or 0),
        "match_source": "post_wave_asset_value_eval",
        "elite_assets_matched": len(a_rows),
        "coverage_pct": 0.0,
        "is_high_yield": bool(top),
        "best_match": top[0] if top else None,
        "top_matches": [
            {
                "source_path": x.get("source_path"),
                "name": x.get("name"),
                "heuristic_score": x.get("local_score"),
                "final_score": x.get("final_score"),
                "grade": x.get("grade"),
                "local_similarity_pct": None,
            }
            for x in top[:12]
        ],
        "grades": rep.get("grades"),
        "avg_score": rep.get("avg_score"),
        "groq_calls": rep.get("groq_calls"),
        "groq_success": rep.get("groq_success"),
        "wave_report_path": path.replace("\\", "/"),
    }

    lead = {
        "platform": "internal_wave",
        "title": "全量數據清算大戰役（Asset_Value 精煉波次）",
        "description": (
            f"Run_ID={rep.get('run_id')}  sampled={rep.get('sampled')} pool={rep.get('pool_size')} "
            f"avg={rep.get('avg_score')} grades={rep.get('grades')}"
        ),
        "budget": "",
        "url": "",
    }

    out_dir = resolve_agent_output_path(root, "06_Exports_Output", "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_p = os.path.join(out_dir, "scout_last_pipeline.json")
    payload = {
        "schema_version": "1.0",
        "saved_at": _utc_iso(),
        "run_tag": str(rep.get("run_id") or "wave_sync"),
        "lead": lead,
        "match_report": match_report,
    }
    tmp = out_p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, out_p)
    print(json.dumps({"ok": True, "written": out_p, "source_report": path}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
