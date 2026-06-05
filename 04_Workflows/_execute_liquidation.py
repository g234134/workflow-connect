# _execute_liquidation.py — 數據清算戰役·正式點火
# 簽押 → Liquidation_Agent.execute_signed → 門下省終審 → 寫回 Status.json。

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

from gov_paths import resolve_artifact_under_root, get_tang_gov_root  # type: ignore
from Liquidation_Agent import Liquidation_Agent  # type: ignore
from MenXia_Audit import MenXia_Audit  # type: ignore


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

    # 簽押 token：尚書省於本對話中下達「准奏／全量出擊／點火」之朱批
    signed_token = (
        "shangshu_signed:"
        + _utc_iso()
        + ":option_A:liquidate_quarantine_json"
    )

    _patch_status(
        dest_root,
        {"pipeline_status": "Running", "shangshu_signed_token": signed_token},
    )

    # ── 點火 ──
    liq = Liquidation_Agent(dest_root=dest_root, dry_run=False)
    liq_result = liq.execute_signed(signed_token=signed_token)
    liq_run_id = liq.agent.run_id

    # ── 門下省終審 ──
    auditor = MenXia_Audit(dest_root=dest_root)
    audit = auditor.audit_after_execution(
        manager_run_id=liq_run_id,
        task_errors=liq_result.get("errors", 0),
    )

    pipeline_status = "Manual" if (audit.veto or not liq_result.get("ok", False)) else "Success"

    # ── 戰報入 Status.json ──
    _patch_status(
        dest_root,
        {
            "pipeline_status": pipeline_status,
            "shangshu_signed_token": signed_token,
            "liquidation_last_wave": {
                "status": pipeline_status,
                "liquidation_run_id": liq_run_id,
                "moved": liq_result.get("moved", {}),
                "errors": liq_result.get("errors", 0),
                "menxia_run_id": auditor.agent.run_id,
                "menxia_veto": audit.veto,
                "menxia_failure_count": audit.failure_count,
                "completed_at": _utc_iso(),
            },
        },
    )

    summary = {
        "pipeline_status": pipeline_status,
        "liquidation_run_id": liq_run_id,
        "moved": liq_result.get("moved", {}),
        "errors": liq_result.get("errors", 0),
        "audit": {
            "latest_run_id": audit.latest_run_id,
            "failure_count": audit.failure_count,
            "veto": audit.veto,
            "terminate_pipeline": audit.terminate_pipeline,
        },
        "signed_token": signed_token,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
