"""_build_elite_index.py — v2.56 A 級資產快速索引（elite_cache.json）。

掃描 05_Temp_Cache/cleaned_full 下 JSON；僅收錄 clean_status 符合允許清單（預設 indexed,ok）
且啟發式 Score > 7.5 且 grade=A 之條目，寫入 06_Exports_Output/reports/elite_cache.json 供 ROI 全量比對。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from _tang_paths import bootstrap_sys_path, sha256_file  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from Asset_Value_Evaluator_Agent import (  # type: ignore
    _flatten_summary_for_match,
    _heuristic_score,
    _grade,
)
from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore

# A 級 elite 收錄門檻：實際分數上限約 8.8，舊值 9.0 導致 elite_cache 永遠為空（P1）
ELITE_MIN_HEURISTIC_SCORE = 7.5


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _norm_status(s: Any) -> str:
    return str(s or "").strip().lower()


def main() -> int:
    parser = argparse.ArgumentParser(description="建立 A 級資產 elite_cache.json")
    parser.add_argument("--max-files", type=int, default=0, help="0=不限制；測試用可設 500")
    parser.add_argument(
        "--allow-status",
        default="indexed,ok",
        help="逗號分隔；精煉產物常為 ok，與 Chariot indexed 並列允許",
    )
    parser.add_argument(
        "--out",
        default="",
        help="輸出檔路徑；預設 06_Exports_Output/reports/elite_cache.json",
    )
    args = parser.parse_args()

    root = get_tang_gov_root()
    cleaned = resolve_agent_output_path(root, "05_Temp_Cache", "cleaned_full")
    reports = resolve_agent_output_path(root, "06_Exports_Output", "reports")
    os.makedirs(reports, exist_ok=True)
    out_path = args.out.strip() or os.path.join(reports, "elite_cache.json")

    allow: Set[str] = {s.strip().lower() for s in str(args.allow_status).split(",") if s.strip()}

    if not os.path.isdir(cleaned):
        print(json.dumps({"ok": False, "error": "cleaned_full_missing", "cleaned": cleaned}, ensure_ascii=False))
        return 2

    paths = sorted(
        os.path.join(cleaned, fn) for fn in os.listdir(cleaned) if fn.endswith(".json")
    )
    if args.max_files and args.max_files > 0:
        paths = paths[: int(args.max_files)]

    entries: List[Dict[str, Any]] = []
    t0 = time.time()
    files_seen = 0
    for fp in paths:
        files_seen += 1
        try:
            with open(fp, "r", encoding="utf-8") as f:
                rec = json.load(f)
        except Exception:
            continue
        st = _norm_status(rec.get("clean_status"))
        if st not in allow:
            continue
        hscore, _conf, tags = _heuristic_score(rec)
        gr = _grade(hscore)
        if not (hscore > ELITE_MIN_HEURISTIC_SCORE and gr == "A"):
            continue
        blob = _flatten_summary_for_match(rec.get("content_summary"))
        blob = blob or str(rec.get("source_path") or rec.get("name") or "")
        try:
            digest = sha256_file(fp)
        except OSError:
            digest = ""
        entries.append(
            {
                "json_path": fp.replace("\\", "/"),
                "stored_path": str(rec.get("stored_path") or "").replace("\\", "/"),
                "source_path": str(rec.get("source_path") or "").replace("\\", "/"),
                "name": rec.get("name"),
                "extension": rec.get("extension"),
                "original_type": rec.get("original_type"),
                "heuristic_score": hscore,
                "grade": gr,
                "clean_status": rec.get("clean_status"),
                "feature_blob": blob[:12000],
                "tags": tags[:24],
                "file_sha256": digest,
            }
        )

    payload = {
        "schema_version": "1.0",
        "version": "v2.56",
        "built_at": _utc_iso(),
        "tang_gov_root": root.replace("\\", "/"),
        "cleaned_full": cleaned.replace("\\", "/"),
        "allow_status": sorted(allow),
        "min_heuristic_score": ELITE_MIN_HEURISTIC_SCORE,
        "stats": {
            "files_seen": files_seen,
            "elite_count": len(entries),
            "elapsed_sec": round(time.time() - t0, 3),
        },
        "entries": entries,
    }
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, out_path)

    print(json.dumps({"ok": True, "out": out_path, **payload["stats"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
