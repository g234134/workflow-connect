# _indexing_and_audit.py — 數據戶籍化工程·一動三審
# 1) 戶籍化：產生 03_RAG_Database/C2_核心知識庫/metadata_index.json
# 2) 戰報備份：複製本役 C3 日誌到 06_Exports_Output/reports/
# 3) 預備銷毀：清點 06_Exports_Output/Archive/format_error/ 0-byte 空檔（不刪除）
# 並更新 04_Workflows/Status.json 之 indexing_last_wave / log_backup_last_wave / cleanup_pending。

from __future__ import annotations

import json
import os
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_workflows = os.path.dirname(os.path.abspath(__file__))
_agents_core = os.path.normpath(os.path.join(_workflows, "..", "02_Agents_Core"))
for _p in (_agents_core, _workflows):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gov_paths import (  # type: ignore
    get_department_under,
    get_tang_gov_root,
    resolve_agent_output_path,
    resolve_artifact_under_root,
)
from Indexing_Agent import Indexing_Agent  # type: ignore

LIQUIDATION_RUN_ID = "6638d1906c5940338c04c952e6268355"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _patch_status(dest_root: str, patch: Dict[str, Any]) -> str:
    path = resolve_artifact_under_root(dest_root, "status_json")
    data: Dict[str, Any] = {}
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data.update(patch)
    data["updated_at"] = _utc_iso()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def step1_indexing(dest_root: str) -> Dict[str, Any]:
    return Indexing_Agent(dest_root=dest_root).build_index()


def step3_log_backup(dest_root: str, run_id: str) -> Dict[str, Any]:
    rag_dir = get_department_under(dest_root, "03_RAG_Database")
    src = os.path.join(rag_dir, "C3_Logs", f"{run_id}.jsonl")
    if not os.path.isfile(src):
        return {"ok": False, "reason": "src_not_found", "src": src}

    reports_dir = resolve_agent_output_path(dest_root, "06_Exports_Output", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dst_log = os.path.join(reports_dir, f"c3_log_backup_{run_id}_{stamp}.jsonl")
    shutil.copy2(src, dst_log)

    src_size = os.path.getsize(src)
    dst_size = os.path.getsize(dst_log)
    line_count = 0
    event_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    with open(dst_log, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            line_count += 1
            try:
                o = json.loads(line)
                event_counter[str(o.get("event"))] += 1
                status_counter[str(o.get("status"))] += 1
            except Exception:  # noqa: BLE001
                continue

    summary = {
        "schema_version": "1.0",
        "src": src,
        "dst": dst_log,
        "run_id": run_id,
        "size_bytes_src": src_size,
        "size_bytes_dst": dst_size,
        "line_count": line_count,
        "top_events": event_counter.most_common(10),
        "status_distribution": status_counter.most_common(),
        "backed_up_at": _utc_iso(),
    }
    summary_path = os.path.join(reports_dir, f"c3_log_backup_{run_id}_{stamp}.summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return {"ok": True, "backup_path": dst_log, "summary_path": summary_path, "summary": summary}


def step2_inventory_format_error(dest_root: str) -> Dict[str, Any]:
    archive_dir = resolve_agent_output_path(dest_root, "06_Exports_Output", "archive")
    fed = os.path.join(archive_dir, "format_error")
    reports_dir = resolve_agent_output_path(dest_root, "06_Exports_Output", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    zero_files: List[Dict[str, Any]] = []
    nonzero_files: List[Dict[str, Any]] = []
    total = 0
    skipped_marker = 0

    if os.path.isdir(fed):
        for dp, _, fns in os.walk(fed):
            for fn in fns:
                if fn == ".department.txt":
                    skipped_marker += 1
                    continue
                fp = os.path.join(dp, fn)
                try:
                    sz = os.path.getsize(fp)
                except OSError:
                    sz = -1
                rec = {"name": fn, "path": fp, "size_bytes": sz}
                total += 1
                if sz == 0:
                    zero_files.append(rec)
                else:
                    nonzero_files.append(rec)

    nonzero_files.sort(key=lambda r: r["size_bytes"], reverse=True)

    inventory = {
        "schema_version": "1.0",
        "generated_at": _utc_iso(),
        "scan_root": fed,
        "marker_files_skipped": skipped_marker,
        "total_files": total,
        "zero_byte_count": len(zero_files),
        "nonzero_byte_count": len(nonzero_files),
        "nonzero_total_size_bytes": sum(r["size_bytes"] for r in nonzero_files if r["size_bytes"] > 0),
        "zero_byte_samples": zero_files[:50],
        "nonzero_top10_largest": nonzero_files[:10],
        "destruction_target_paths_first_20": [r["path"] for r in zero_files[:20]],
        "destruction_held": True,
        "note": "本清單僅清點，未執行任何刪除；待尚書省簽押後另以 destroy_signed=<token> 觸發。",
    }

    inv_path = os.path.join(reports_dir, f"format_error_inventory_{_utc_iso().replace(':','').replace('-','')}.json")
    with open(inv_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)
    return {"inventory_path": inv_path, "inventory": inventory}


def main() -> int:
    dest_root = get_tang_gov_root()

    # ── 步驟 1：戶籍化 ──
    idx = step1_indexing(dest_root)
    # ── 步驟 3：戰報備份 ──
    bak = step3_log_backup(dest_root, LIQUIDATION_RUN_ID)
    # ── 步驟 2：清點（不刪） ──
    inv = step2_inventory_format_error(dest_root)

    _patch_status(
        dest_root,
        {
            "pipeline_status": "Success",
            "indexing_last_wave": {
                "status": "Success",
                "run_id": idx["run_id"],
                "file_count": idx["file_count"],
                "total_size_bytes": idx["total_size_bytes"],
                "by_root_type": idx["stats"]["by_root_type"],
                "canonical_path": idx["canonical_path"],
                "backup_path": idx["backup_path"],
                "completed_at": _utc_iso(),
            },
            "log_backup_last_wave": {
                "status": "Success" if bak.get("ok") else "Manual",
                "src_run_id": LIQUIDATION_RUN_ID,
                "backup_path": bak.get("backup_path"),
                "summary_path": bak.get("summary_path"),
                "completed_at": _utc_iso(),
            },
            "cleanup_pending": {
                "status": "AwaitingSignature",
                "scope": "06_Exports_Output/Archive/format_error 之 0-byte 空檔",
                "zero_byte_count": inv["inventory"]["zero_byte_count"],
                "nonzero_byte_count": inv["inventory"]["nonzero_byte_count"],
                "total_files": inv["inventory"]["total_files"],
                "inventory_path": inv["inventory_path"],
                "destruction_held": True,
                "queued_at": _utc_iso(),
            },
        },
    )

    print(json.dumps(
        {
            "step1_indexing": {
                "run_id": idx["run_id"],
                "file_count": idx["file_count"],
                "total_size_bytes": idx["total_size_bytes"],
                "by_root_type": idx["stats"]["by_root_type"],
                "top_keys_top10": idx["stats"]["top_keys_top20"][:10],
                "canonical_path": idx["canonical_path"],
                "backup_path": idx["backup_path"],
                "error_count": idx["error_count"],
            },
            "step3_log_backup": bak.get("summary"),
            "step2_inventory": {
                "inventory_path": inv["inventory_path"],
                "total_files": inv["inventory"]["total_files"],
                "zero_byte_count": inv["inventory"]["zero_byte_count"],
                "nonzero_byte_count": inv["inventory"]["nonzero_byte_count"],
                "nonzero_total_size_bytes": inv["inventory"]["nonzero_total_size_bytes"],
                "destruction_held": True,
            },
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
