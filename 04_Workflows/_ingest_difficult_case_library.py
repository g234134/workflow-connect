"""_ingest_difficult_case_library.py — 將精煉戰報中的「高難度」樣本合併進案例庫（供下波跳過 Groq）。

判定（任一即入庫）：
  · 曾送 Groq（groq_used）
  · 白名單副檔 + 本地灰區（信心 <0.65 或 4≤local_score≤6）

索引：schema 1.1
  · cases：仍以 content_sha256（64 hex）為主鍵（若有）
  · path_aliases：正規化路徑 → sha
  · path_only：無 sha 時以 stored_path / source_path 正規化鍵保存一筆

下波精煉：優先 SHA 命中；否則以 stored_path / source_path / cleaned JSON 路徑回退比對。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from _tang_paths import bootstrap_sys_path  # type: ignore

_here = os.path.dirname(os.path.abspath(__file__))
_root = bootstrap_sys_path(_here)

from gov_paths import get_tang_gov_root, resolve_agent_output_path  # type: ignore

GROQ_WHITELIST_EXT = frozenset(
    {".py", ".php", ".json", ".jsonc", ".json5", ".yml", ".yaml", ".toml"}
)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _norm_path(p: Any) -> str:
    if not p:
        return ""
    return os.path.normpath(str(p)).replace("\\", "/").lower()


def _is_hex_sha64(s: str) -> bool:
    t = str(s or "").strip().lower()
    return len(t) == 64 and re.fullmatch(r"[0-9a-f]{64}", t) is not None


def _latest_eval_report(rep_dir: str) -> str:
    cands = glob.glob(os.path.join(rep_dir, "asset_value_eval_*.json"))
    if not cands:
        return ""
    cands.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return cands[0]


def _row_difficult(row: Dict[str, Any]) -> bool:
    ext = str(row.get("extension") or "").lower()
    if row.get("groq_used") is True:
        return True
    if ext not in GROQ_WHITELIST_EXT:
        return False
    try:
        conf = float(row.get("confidence") or 0)
        loc = float(row.get("local_score") or 0)
    except (TypeError, ValueError):
        return False
    ambiguous = (conf < 0.65) or (4.0 <= loc <= 6.0)
    return ambiguous


def _merge_case(
    prev: Dict[str, Any],
    row: Dict[str, Any],
    run_id: str,
) -> Dict[str, Any]:
    """新資料優先覆寫成功 Groq；失敗時保留舊的成功快取。"""
    sha = str(row.get("content_sha256") or "").strip()
    groq_reason = row.get("groq_reason")
    groq_val = row.get("groq_value")
    out = {
        "content_sha256": sha if _is_hex_sha64(sha) else "",
        "extension": str(row.get("extension") or "").lower(),
        "local_score": row.get("local_score"),
        "confidence": row.get("confidence"),
        "learned_run_id": run_id,
        "learned_at": _utc_iso(),
        "name": row.get("name"),
        "source_path": row.get("source_path"),
        "stored_path": row.get("stored_path"),
    }
    if groq_reason == "groq_ok" and isinstance(groq_val, (int, float)):
        out["groq_value"] = float(groq_val)
        out["groq_rationale"] = row.get("groq_rationale")
        out["groq_reason"] = "groq_ok"
    elif prev and prev.get("groq_reason") == "groq_ok" and isinstance(prev.get("groq_value"), (int, float)):
        out["groq_value"] = float(prev["groq_value"])
        out["groq_rationale"] = prev.get("groq_rationale")
        out["groq_reason"] = "groq_ok"
        out["learned_run_id"] = prev.get("learned_run_id") or run_id
    else:
        out["groq_value"] = groq_val if isinstance(groq_val, (int, float)) else None
        out["groq_rationale"] = row.get("groq_rationale")
        out["groq_reason"] = str(groq_reason) if groq_reason is not None else None
    return out


def _rebuild_path_aliases(cases: Dict[str, Any]) -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    for sha, ent in cases.items():
        if not _is_hex_sha64(str(sha)):
            continue
        if not isinstance(ent, dict):
            continue
        for pk in ("stored_path", "source_path"):
            n = _norm_path(ent.get(pk))
            if n:
                aliases[n] = str(sha).strip().lower()
    return aliases


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="", help="指定 asset_value_eval_*.json；預設取最新")
    args = ap.parse_args()

    root = get_tang_gov_root()
    rep_dir = resolve_agent_output_path(root, "06_Exports_Output", "reports")
    os.makedirs(rep_dir, exist_ok=True)
    path = args.report.strip() or _latest_eval_report(rep_dir)
    if not path or not os.path.isfile(path):
        print(json.dumps({"ok": False, "error": "no_report"}, ensure_ascii=False))
        return 2

    with open(path, "r", encoding="utf-8") as f:
        rep: Dict[str, Any] = json.load(f)
    run_id = str(rep.get("run_id") or "")
    rows: List[Dict[str, Any]] = list(rep.get("rows") or [])

    lib_path = os.path.join(rep_dir, "difficult_case_library.json")
    data: Dict[str, Any] = {
        "schema_version": "1.1",
        "updated_at": _utc_iso(),
        "cases": {},
        "path_aliases": {},
        "path_only": {},
    }
    if os.path.isfile(lib_path):
        try:
            with open(lib_path, "r", encoding="utf-8") as f:
                old = json.load(f) or {}
            if isinstance(old, dict):
                data["cases"] = dict(old.get("cases") or {})
                data["path_only"] = dict(old.get("path_only") or {})
        except Exception:  # noqa: BLE001
            pass

    cases: Dict[str, Any] = {}
    for k, v in (data.get("cases") or {}).items():
        if isinstance(v, dict) and _is_hex_sha64(str(k)):
            cases[str(k).strip().lower()] = v
    path_only: Dict[str, Any] = {str(k): v for k, v in (data.get("path_only") or {}).items() if isinstance(v, dict)}

    added = 0
    updated = 0
    path_added = 0
    prev_case_keys = set(cases.keys())
    prev_path_keys = set(path_only.keys())

    for row in rows:
        if row.get("error"):
            continue
        if not _row_difficult(row):
            continue
        sha = str(row.get("content_sha256") or "").strip()
        prev_rec: Dict[str, Any] = {}
        if _is_hex_sha64(sha):
            prev_rec = cases.get(sha.lower()) or {}
        else:
            pk2 = _norm_path(row.get("stored_path")) or _norm_path(row.get("source_path"))
            if pk2:
                prev_rec = path_only.get(pk2) or {}
        merged = _merge_case(prev_rec, row, run_id)

        if _is_hex_sha64(sha):
            skl = sha.lower()
            prev = cases.get(skl)
            cases[skl] = merged
            if prev is None:
                added += 1
            else:
                updated += 1
        else:
            pk = _norm_path(row.get("stored_path")) or _norm_path(row.get("source_path"))
            if not pk:
                continue
            prev_p = path_only.get(pk)
            path_only[pk] = merged
            if prev_p is None:
                path_added += 1
            else:
                updated += 1

    data["cases"] = cases
    data["path_only"] = path_only
    data["path_aliases"] = _rebuild_path_aliases(cases)
    data["updated_at"] = _utc_iso()
    data["last_ingest_run_id"] = run_id
    data["last_ingest_report"] = path.replace("\\", "/")

    tmp = lib_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, lib_path)

    summary = {
        "ok": True,
        "written": lib_path,
        "ingested_from": path,
        "run_id": run_id,
        "rows_scanned": len(rows),
        "cases_by_sha": len(cases),
        "path_only_keys": len(path_only),
        "path_aliases": len(data["path_aliases"]),
        "new_sha_keys": len(set(cases.keys()) - prev_case_keys),
        "new_path_only_keys": len(set(path_only.keys()) - prev_path_keys),
        "merge_updates": updated,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
