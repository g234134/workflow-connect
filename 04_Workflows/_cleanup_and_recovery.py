# _cleanup_and_recovery.py — 清算餘波·混合模式（甲+修復）
# 1) Cleanup_Agent：物理銷毀 14 件 0-byte 佔位空殼（cleanup_executed）
# 2) Recovery_Agent：對 797 件非 0-byte 進行一次性編碼／BOM 修復與重分類
# 3) 更新 Status.json：cleanup_last_wave + recovery_last_wave + pipeline_status=Success

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict

_workflows = os.path.dirname(os.path.abspath(__file__))
_agents_core = os.path.normpath(os.path.join(_workflows, "..", "02_Agents_Core"))
for _p in (_agents_core, _workflows):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gov_paths import (  # type: ignore
    get_tang_gov_root,
    resolve_artifact_under_root,
)
from Cleanup_Agent import Cleanup_Agent  # type: ignore
from Recovery_Agent import Recovery_Agent  # type: ignore


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


def main() -> int:
    dest_root = get_tang_gov_root()
    signed_token = (
        "shangshu_signed:"
        + _utc_iso()
        + ":hybrid_mode:cleanup_zero_byte+recovery_nonzero"
    )

    _patch_status(
        dest_root,
        {"pipeline_status": "Running", "shangshu_signed_token": signed_token},
    )

    # ── 步驟 1：物理銷毀 14 件 0-byte ──
    cleaner = Cleanup_Agent(dest_root=dest_root, signed_token=signed_token)
    targets = cleaner.list_zero_byte_in_format_error()
    cleanup_result = cleaner.destroy_files(targets, scope="format_error_zero_byte")
    cleanup_run_id = cleaner.agent.run_id

    # ── 步驟 2：一次性修復 797 件 ──
    recovery = Recovery_Agent(dest_root=dest_root, signed_token=signed_token)
    recovery_result = recovery.repair_all()
    recovery_run_id = recovery.agent.run_id

    final_pipeline = "Success"
    if (not cleanup_result.get("ok", False)) or (not recovery_result.get("ok", False)):
        final_pipeline = "Manual"

    _patch_status(
        dest_root,
        {
            "pipeline_status": final_pipeline,
            "shangshu_signed_token": signed_token,
            "cleanup_last_wave": {
                "status": "Success" if cleanup_result.get("ok") else "Manual",
                "cleanup_run_id": cleanup_run_id,
                "deleted_count": cleanup_result.get("deleted_count", 0),
                "errors": len(cleanup_result.get("errors", [])),
                "scope": cleanup_result.get("scope"),
                "completed_at": cleanup_result.get("completed_at"),
            },
            "recovery_last_wave": {
                "status": "Success" if recovery_result.get("ok") else "Manual",
                "recovery_run_id": recovery_run_id,
                "target_count": recovery_result.get("target_count", 0),
                "repaired": recovery_result.get("repaired", 0),
                "unrecoverable": recovery_result.get("unrecoverable", 0),
                "decode_failed": recovery_result.get("decode_failed", 0),
                "parse_failed": recovery_result.get("parse_failed", 0),
                "write_errors": recovery_result.get("write_errors", 0),
                "success_rate": recovery_result.get("success_rate", 0.0),
                "by_encoding": recovery_result.get("by_encoding", {}),
                "by_category": recovery_result.get("by_category", {}),
                "by_destination": recovery_result.get("by_destination", {}),
                "completed_at": recovery_result.get("completed_at"),
            },
        },
    )

    print(json.dumps(
        {
            "pipeline_status": final_pipeline,
            "signed_token": signed_token,
            "cleanup": {
                "run_id": cleanup_run_id,
                "deleted_count": cleanup_result.get("deleted_count"),
                "errors": cleanup_result.get("errors"),
            },
            "recovery": {
                "run_id": recovery_run_id,
                "target_count": recovery_result.get("target_count"),
                "repaired": recovery_result.get("repaired"),
                "unrecoverable": recovery_result.get("unrecoverable"),
                "decode_failed": recovery_result.get("decode_failed"),
                "parse_failed": recovery_result.get("parse_failed"),
                "write_errors": recovery_result.get("write_errors"),
                "success_rate": recovery_result.get("success_rate"),
                "by_encoding": recovery_result.get("by_encoding"),
                "by_category": recovery_result.get("by_category"),
                "by_destination": recovery_result.get("by_destination"),
                "by_parse_strategy": recovery_result.get("by_parse_strategy"),
                "unrecoverable_samples": recovery_result.get("unrecoverable_samples"),
            },
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
