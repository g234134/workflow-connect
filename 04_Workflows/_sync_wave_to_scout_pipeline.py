"""_sync_wave_to_scout_pipeline.py — 將最近一次 Asset_Value 精煉戰報寫入 scout_last_pipeline.json。

供 v2.56 _report_generator.py 讀取（虛擬節省 TWD、A 級匹配等）。

P4：若 eval rows 缺少 local_similarity_pct，以 Asset_Value_Evaluator 的本地語義覆蓋率
補算，回寫上游 asset_value_eval_*.json，再寫入 scout_last_pipeline。
"""
from __future__ import annotations

import glob
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore

# Asset_Value_Evaluator helpers（本地 Jaccard/SequenceMatcher → 0~100）
_agents = os.path.join(_root, "02_Agents_Core")
if _agents not in sys.path:
    sys.path.insert(0, _agents)
from Asset_Value_Evaluator_Agent import (  # type: ignore
    _flatten_summary_for_match,
    _semantic_overlap_pct,
)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _latest_eval_report(root: str) -> str:
    rep = resolve_agent_output_path(root, "06_Exports_Output", "reports")
    cands = glob.glob(os.path.join(rep, "asset_value_eval_*.json"))
    if not cands:
        return ""
    cands.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return cands[0]


def _load_elite_blob_index(root: str) -> Dict[str, str]:
    """name / source_path → feature_blob（來自 elite_cache）。"""
    path = os.path.join(
        resolve_agent_output_path(root, "06_Exports_Output", "reports"),
        "elite_cache.json",
    )
    out: Dict[str, str] = {}
    if not os.path.isfile(path):
        return out
    try:
        with open(path, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except Exception:  # noqa: BLE001
        return out
    for e in cache.get("entries") or []:
        if not isinstance(e, dict):
            continue
        blob = str(e.get("feature_blob") or "").strip()
        if not blob:
            continue
        name = str(e.get("name") or "").strip()
        src = str(e.get("source_path") or "").replace("\\", "/").strip()
        if name:
            out[f"name:{name}"] = blob
        if src:
            out[f"src:{src}"] = blob
    return out


def _blob_from_cleaned(root: str, row: Dict[str, Any]) -> str:
    stored = str(row.get("stored_path") or "").strip()
    if not stored or not os.path.isfile(stored):
        # fallback：cleaned_full 下依 name 猜
        name = str(row.get("name") or "").strip()
        if not name:
            return ""
        cleaned = resolve_agent_output_path(root, "05_Temp_Cache", "cleaned_full")
        if not os.path.isdir(cleaned):
            return ""
        for fn in os.listdir(cleaned):
            if fn.endswith(".json") and name in fn:
                stored = os.path.join(cleaned, fn)
                break
    if not stored or not os.path.isfile(stored):
        return ""
    try:
        with open(stored, "r", encoding="utf-8") as f:
            rec = json.load(f)
    except Exception:  # noqa: BLE001
        return ""
    blob = _flatten_summary_for_match(rec.get("content_summary"))
    if blob:
        return blob
    return str(rec.get("source_path") or rec.get("name") or row.get("name") or "")


def _resolve_blob(
    root: str, row: Dict[str, Any], elite_idx: Dict[str, str]
) -> str:
    name = str(row.get("name") or "").strip()
    src = str(row.get("source_path") or "").replace("\\", "/").strip()
    if name and f"name:{name}" in elite_idx:
        return elite_idx[f"name:{name}"]
    if src and f"src:{src}" in elite_idx:
        return elite_idx[f"src:{src}"]
    return _blob_from_cleaned(root, row)


def _build_needle(rep: Dict[str, Any], top: List[Dict[str, Any]]) -> str:
    """波次案源針：tags + 類型 + Top A 檔名（無外部 opportunity 時的本地覆蓋基準）。"""
    tags = rep.get("top_tags") or {}
    tag_keys = list(tags.keys())[:24] if isinstance(tags, dict) else []
    by_type = rep.get("by_type") or {}
    type_keys = list(by_type.keys())[:12] if isinstance(by_type, dict) else []
    names = [str(x.get("name") or "") for x in top[:8] if x.get("name")]
    parts = [
        "asset_value_wave_match",
        f"run_id={rep.get('run_id')}",
        "tags=" + " ".join(tag_keys),
        "types=" + " ".join(type_keys),
        "names=" + " ".join(names),
    ]
    return "\n".join(parts)


def _ensure_similarity_on_rows(
    root: str,
    rep: Dict[str, Any],
    top: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int]:
    """為 top A rows 補 local_similarity_pct；回傳 enriched top 與新寫入筆數。"""
    elite_idx = _load_elite_blob_index(root)
    needle = _build_needle(rep, top)
    filled = 0
    enriched: List[Dict[str, Any]] = []
    for x in top:
        row = dict(x)
        existing = row.get("local_similarity_pct")
        if existing is not None:
            try:
                float(existing)
                enriched.append(row)
                continue
            except (TypeError, ValueError):
                pass
        blob = _resolve_blob(root, row, elite_idx)
        pct = _semantic_overlap_pct(needle, blob) if blob else 0.0
        row["local_similarity_pct"] = pct
        filled += 1
        enriched.append(row)
    return enriched, filled


def _persist_similarity_into_eval(
    path: str, rep: Dict[str, Any], enriched_top: List[Dict[str, Any]]
) -> int:
    """把 similarity 回寫到 eval report 的對應 rows（依 source_path+name 對齊）。"""
    by_key: Dict[str, float] = {}
    for x in enriched_top:
        pct = x.get("local_similarity_pct")
        if pct is None:
            continue
        key = f"{x.get('source_path')}|{x.get('name')}"
        by_key[key] = float(pct)

    rows = list(rep.get("rows") or [])
    updated = 0
    for r in rows:
        key = f"{r.get('source_path')}|{r.get('name')}"
        if key in by_key and r.get("local_similarity_pct") is None:
            r["local_similarity_pct"] = by_key[key]
            updated += 1
    if updated:
        rep["rows"] = rows
        rep["local_similarity_enriched_at"] = _utc_iso()
        rep["local_similarity_enriched_count"] = updated
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    return updated


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

    enriched_top, filled = _ensure_similarity_on_rows(root, rep, top)
    persisted = _persist_similarity_into_eval(path, rep, enriched_top)

    match_report: Dict[str, Any] = {
        "ok": True,
        "pool_size": int(rep.get("pool_size") or 0),
        "scanned": int(rep.get("sampled") or 0),
        "match_source": "post_wave_asset_value_eval",
        "elite_assets_matched": len(a_rows),
        "coverage_pct": 0.0,
        "is_high_yield": bool(enriched_top),
        "best_match": enriched_top[0] if enriched_top else None,
        "top_matches": [
            {
                "source_path": x.get("source_path"),
                "name": x.get("name"),
                "heuristic_score": x.get("local_score"),
                "final_score": x.get("final_score"),
                "grade": x.get("grade"),
                "local_similarity_pct": x.get("local_similarity_pct"),
            }
            for x in enriched_top[:12]
        ],
        "grades": rep.get("grades"),
        "avg_score": rep.get("avg_score"),
        "groq_calls": rep.get("groq_calls"),
        "groq_success": rep.get("groq_success"),
        "wave_report_path": path.replace("\\", "/"),
        "local_similarity_filled": filled,
        "local_similarity_persisted_to_eval": persisted,
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
    print(
        json.dumps(
            {
                "ok": True,
                "written": out_p,
                "source_report": path,
                "local_similarity_filled": filled,
                "local_similarity_persisted_to_eval": persisted,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
