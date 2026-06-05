"""_local_judge_refiner.py — 本地智能進化：由案例庫 + 金磚 + 歷史戰報歸納「雲端高失敗灰區」，寫入 local_judge_rules.json。

Asset_Value_Evaluator_Agent 於灰區載入規則後，若命中 dodge_profiles 則跳過 Groq，
改採本地分數修正（預設乘數 defaults.local_score_multiplier）。

用法：
  python _local_judge_refiner.py --build
  python _local_judge_refiner.py --build --max-reports 5
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, DefaultDict, Dict, List, Tuple

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore

GROQ_WHITELIST_EXT = frozenset(
    {".py", ".php", ".json", ".jsonc", ".json5", ".yml", ".yaml", ".toml"}
)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ambiguous_row(row: Dict[str, Any]) -> bool:
    ext = str(row.get("extension") or "").lower()
    if ext not in GROQ_WHITELIST_EXT:
        return False
    try:
        conf = float(row.get("confidence") or 0)
        loc = float(row.get("local_score") or 0)
    except (TypeError, ValueError):
        return False
    return (conf < 0.65) or (4.0 <= loc <= 6.0)


def _collect_from_eval_rows(rows: List[Dict[str, Any]]) -> DefaultDict[Tuple[str, str], Dict[str, int]]:
    agg: DefaultDict[Tuple[str, str], Dict[str, int]] = defaultdict(
        lambda: {"cloud_ok": 0, "cloud_fail": 0, "ambiguous_hits": 0}
    )
    for row in rows:
        if row.get("error"):
            continue
        ext = str(row.get("extension") or "").lower()
        ot = str(row.get("original_type") or "unknown").lower()
        key = (ext, ot)
        if _ambiguous_row(row):
            agg[key]["ambiguous_hits"] += 1
        if row.get("groq_used") is True:
            gr = str(row.get("groq_reason") or "")
            gv = row.get("groq_value")
            if gr == "groq_ok" and isinstance(gv, (int, float)):
                agg[key]["cloud_ok"] += 1
            else:
                agg[key]["cloud_fail"] += 1
    return agg


def _merge_elite_signals(elite_path: str) -> DefaultDict[Tuple[str, str], int]:
    pos: DefaultDict[Tuple[str, str], int] = defaultdict(int)
    if not os.path.isfile(elite_path):
        return pos
    try:
        with open(elite_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:  # noqa: BLE001
        return pos
    for ent in data.get("entries") or []:
        if not isinstance(ent, dict):
            continue
        ext = str(ent.get("extension") or "").lower()
        ot = str(ent.get("original_type") or "unknown").lower()
        pos[(ext, ot)] += 1
    return pos


def build_rules(root: str, *, max_reports: int) -> Dict[str, Any]:
    rep_dir = resolve_agent_output_path(root, "06_Exports_Output", "reports")
    elite_path = os.path.join(rep_dir, "elite_cache.json")
    lib_path = os.path.join(rep_dir, "difficult_case_library.json")

    merged: DefaultDict[Tuple[str, str], Dict[str, int]] = defaultdict(
        lambda: {"cloud_ok": 0, "cloud_fail": 0, "ambiguous_hits": 0}
    )

    cands = sorted(
        glob.glob(os.path.join(rep_dir, "asset_value_eval_*.json")),
        key=lambda p: os.path.getmtime(p),
        reverse=True,
    )
    if max_reports > 0:
        cands = cands[:max_reports]
    for p in cands:
        try:
            with open(p, "r", encoding="utf-8") as f:
                rep = json.load(f)
        except Exception:  # noqa: BLE001
            continue
        rows = list(rep.get("rows") or [])
        part = _collect_from_eval_rows(rows)
        for k, v in part.items():
            for kk, vv in v.items():
                merged[k][kk] += vv

    if os.path.isfile(lib_path):
        try:
            with open(lib_path, "r", encoding="utf-8") as f:
                lib = json.load(f)
        except Exception:  # noqa: BLE001
            lib = {}
        for ent in (lib.get("cases") or {}).values():
            if not isinstance(ent, dict):
                continue
            ext = str(ent.get("extension") or "").lower()
            ot = str(ent.get("original_type") or "unknown").lower()
            gr = str(ent.get("groq_reason") or "")
            gv = ent.get("groq_value")
            if gr == "groq_ok" and isinstance(gv, (int, float)):
                merged[(ext, ot)]["cloud_ok"] += 1
            elif gr.startswith("groq_http_") or gr in {"groq_bad_response", "groq_not_object", "groq_value_not_number"}:
                merged[(ext, ot)]["cloud_fail"] += 3
            elif gr and gr not in {"case_library_hit"}:
                merged[(ext, ot)]["cloud_fail"] += 1

    elite_pos = _merge_elite_signals(elite_path)

    dodge_profiles: List[Dict[str, Any]] = []
    rid = 0
    for (ext, ot), v in merged.items():
        if ext not in GROQ_WHITELIST_EXT:
            continue
        amb = int(v.get("ambiguous_hits") or 0)
        ok = int(v.get("cloud_ok") or 0)
        fail = int(v.get("cloud_fail") or 0)
        cloud_trials = ok + fail
        if amb < 80 and cloud_trials < 20:
            continue
        fail_ratio = fail / max(1, cloud_trials)
        if fail_ratio < 0.28:
            continue
        if elite_pos.get((ext, ot), 0) > 500 and fail_ratio < 0.45:
            continue
        rid += 1
        dodge_profiles.append(
            {
                "rule_id": f"dodge_{rid}_{ext.lstrip('.')}_{ot}",
                "extension": ext,
                "original_type": ot,
                "local_score_min": 4.0,
                "local_score_max": 6.0,
                "confidence_max": 0.65,
                "stats": {"ambiguous_hits": amb, "cloud_ok": ok, "cloud_fail": fail, "fail_ratio": round(fail_ratio, 4)},
            }
        )

    dodge_profiles.sort(key=lambda x: float(x.get("stats", {}).get("fail_ratio", 0)), reverse=True)

    return {
        "schema_version": "1.0",
        "built_at": _utc_iso(),
        "sources": {
            "eval_reports": len(cands),
            "elite_cache": elite_path.replace("\\", "/"),
            "difficult_library": lib_path.replace("\\", "/"),
        },
        "defaults": {"local_score_multiplier": 0.99},
        "dodge_profiles": dodge_profiles[:48],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="寫入 local_judge_rules.json")
    ap.add_argument("--max-reports", type=int, default=12, help="掃描最近 N 份 asset_value_eval；0=全部")
    args = ap.parse_args()

    root = get_tang_gov_root()
    rep_dir = resolve_agent_output_path(root, "06_Exports_Output", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    out_path = os.path.join(rep_dir, "local_judge_rules.json")

    max_rep = int(args.max_reports or 0)
    rules = build_rules(root, max_reports=max_rep)
    print(
        json.dumps(
            {"ok": True, "preview": {"dodge_rules": len(rules.get("dodge_profiles") or [])}},
            ensure_ascii=False,
            indent=2,
        )
    )

    if args.build:
        tmp = out_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        os.replace(tmp, out_path)
        print(json.dumps({"ok": True, "written": out_path}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
