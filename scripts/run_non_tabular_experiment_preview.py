#!/usr/bin/env python3
"""Non-Tabular shadow-flow preview orchestrator CLI v1 (W9-T4 + W12-T3).

Preview-only orchestrator for non_tabular.* task types. Chains v2 decision
(non-tabular branch), non-tabular routing catalog glue, and selector stub —
without executing heavy tools or writing main-chain / Tabular outbox state.

W12-T3 adds optional ``preview+meta`` processing: sandbox metadata extraction
for allowlisted NT-A fixtures when ``--with-metadata-extraction`` is set.

Usage:
    python scripts/run_non_tabular_experiment_preview.py \\
        --task-type non_tabular.document.extract \\
        --case-dir cases/_experiment_samples/nt_docu_stub --format json
    python scripts/run_non_tabular_experiment_preview.py \\
        --task-type non_tabular.document.extract \\
        --case-dir cases/_experiment_samples/nt_docu_stub \\
        --with-metadata-extraction --format json
    python scripts/run_non_tabular_experiment_preview.py \\
        --task-type non_tabular.log.analyze \\
        --case-dir cases/_experiment_samples/nt_log_stub --format text
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from routing.intake_decision_rules_v2 import evaluate_intake_decision_v2
from routing.intake_to_non_tabular_glue import (
    is_non_tabular_task_type,
    plan_non_tabular_route,
)
from tools.document_metadata_extractor_v1 import extract_document_metadata
from tools.non_tabular_lightweight_inspector_v1 import inspect_non_tabular_case_dir
from tools.non_tabular_tool_selector_v1 import select_non_tabular_tools

Format = Literal["text", "json"]

_DEFAULT_OUTBOX_ROOT = _REPO_ROOT / "outbox" / "non_tabular_experiment"

_NT_TASK_TYPE_PATTERN = re.compile(
    r"^non_tabular\.(document|log)\.[a-z0-9_]+$"
)


def _utc_timestamp_stub() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _normalize_case_dir(case_dir: str) -> tuple[Path, str]:
    path = Path(case_dir)
    if not path.is_absolute():
        path = _REPO_ROOT / path
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        rel = resolved.as_posix()
    return resolved, rel


def case_stub_from_dir(case_dir_rel: str) -> str:
    stub = case_dir_rel.replace("\\", "/").replace("/", "_")
    stub = re.sub(r"[^a-zA-Z0-9_-]+", "_", stub)
    return stub[:80] or "case"


def is_supported_non_tabular_task_type(task_type: str) -> bool:
    return bool(_NT_TASK_TYPE_PATTERN.match(task_type))


def _build_risk_notes(
    decision_result: Dict[str, Any],
    glue_plan: Dict[str, Any],
    selector_view: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "decision": decision_result.get("decision"),
        "risk_level": decision_result.get("risk_level"),
        "signals": decision_result.get("signals") or {},
        "inferred_gate_notes": glue_plan.get("inferred_gate_notes") or [],
        "selector_rule_id": selector_view.get("selector_rule_id"),
        "notes": list(
            dict.fromkeys(
                [
                    "preview-only; heavy tools not executed",
                    "sandbox outbox only; no main-chain state writes",
                    *(glue_plan.get("notes") or []),
                    *(selector_view.get("notes") or []),
                ]
            )
        ),
    }


def _write_preview_outbox(
    payload: Dict[str, Any],
    *,
    case_stub: str,
    outbox_root: Path,
    write_outbox: bool,
) -> Optional[str]:
    if not write_outbox:
        return None
    outbox_root.mkdir(parents=True, exist_ok=True)
    filename = f"{_utc_timestamp_stub()}_{case_stub}.json"
    dest = outbox_root / filename
    safe_payload = {
        "schema_version": "non_tabular_experiment_preview_v1",
        "preview_only": True,
        "experiment_id": payload.get("experiment_id"),
        "task_type": payload.get("task_type"),
        "case_ref": payload.get("case_ref"),
        "case_dir": payload.get("case_dir"),
        "decision": payload.get("decision"),
        "planned_route": payload.get("planned_route"),
        "planned_tools": payload.get("planned_tools"),
        "selector_view": payload.get("selector_view"),
        "risk": payload.get("risk"),
        "content_summary": payload.get("content_summary"),
        "processing_summary": payload.get("processing_summary"),
        "final_status": payload.get("final_status"),
        "notes": payload.get("notes"),
    }
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(safe_payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    try:
        return dest.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return dest.as_posix()


def run_non_tabular_experiment_preview(
    task_type: str,
    case_dir: str,
    *,
    write_outbox: bool = True,
    outbox_root: Optional[str] = None,
    with_metadata_extraction: bool = False,
) -> Dict[str, Any]:
    """Run non-tabular preview orchestration and return structured result dict."""
    case_path, case_dir_rel = _normalize_case_dir(case_dir)
    case_ref = case_stub_from_dir(case_dir_rel)
    experiment_id = str(uuid.uuid4())

    base: Dict[str, Any] = {
        "ok": False,
        "experiment_id": experiment_id,
        "case_ref": case_ref,
        "case_dir": case_dir_rel,
        "task_type": task_type,
        "mode": "preview+meta" if with_metadata_extraction else "preview",
        "flow_family": "non_tabular",
        "steps_run": [],
    }

    if not is_non_tabular_task_type(task_type):
        base["message"] = "blocked_non_non_tabular_task_type"
        base["final_status"] = "blocked"
        base["notes"] = [
            "orchestrator accepts non_tabular.* task types only",
            "Tabular and other families are blocked in W9-T4 preview line",
        ]
        return base

    if not is_supported_non_tabular_task_type(task_type):
        base["message"] = "unsupported_non_tabular_task_type"
        base["final_status"] = "blocked"
        base["notes"] = [
            "supported patterns: non_tabular.document.*, non_tabular.log.*",
            "see routing/non_tabular_routing_catalog_v1.yaml",
        ]
        return base

    # S4-lite: metadata-only content summary (W11-T2; no OCR / content reads)
    content_summary = inspect_non_tabular_case_dir(case_dir_rel)
    base["steps_run"].append("S4_lite_content_summary")
    base["content_summary"] = content_summary

    # S3: decision evaluate (v2 non-tabular branch)
    decision = evaluate_intake_decision_v2(task_type, case_dir_rel, use_v1_fallback=False)
    base["steps_run"].append("S3_decision_evaluate")
    base["decision"] = {
        "ok": decision.get("ok"),
        "rules_version": decision.get("rules_version"),
        "decision": decision.get("decision"),
        "risk_level": decision.get("risk_level"),
        "fixture_profile_tier": decision.get("fixture_profile_tier"),
        "rationale": decision.get("rationale"),
        "suggested_route": decision.get("suggested_route"),
        "message": decision.get("message"),
        "shadow_flow_hook": decision.get("shadow_flow_hook"),
    }

    if decision.get("decision") == "reject":
        base["ok"] = True
        base["message"] = decision.get("message", "rejected")
        base["planned_route"] = None
        base["planned_tools"] = []
        base["selector_view"] = None
        base["risk"] = _build_risk_notes(decision, {}, {})
        base["final_status"] = "blocked"
        base["notes"] = ["preview stopped at S3: decision=reject"]
        return base

    # S5: route planning (non-tabular glue)
    glue_plan = plan_non_tabular_route(task_type, case_dir_rel)
    base["steps_run"].append("S5_route_planning")
    base["planned_route"] = {
        "ok": glue_plan.get("ok"),
        "selector_task_type": glue_plan.get("selector_task_type"),
        "planned_tools": glue_plan.get("planned_tools") or [],
        "case_profile": glue_plan.get("case_profile"),
        "skill_card": glue_plan.get("skill_card"),
        "inferred_gate_notes": glue_plan.get("inferred_gate_notes") or [],
        "notes": glue_plan.get("notes") or [],
        "message": glue_plan.get("message"),
        "preview_only": True,
    }

    if not glue_plan.get("ok"):
        base["message"] = glue_plan.get("message", "glue_plan_failed")
        base["planned_tools"] = []
        base["selector_view"] = None
        base["risk"] = _build_risk_notes(decision, glue_plan, {})
        base["final_status"] = "blocked"
        base["notes"] = ["preview stopped at S5: glue plan failed"]
        return base

    planned_tools = list(glue_plan.get("planned_tools") or [])
    case_profile = str(glue_plan.get("case_profile") or case_ref)

    # S6: selector stub (preview only; W9-T3 API)
    selector_view = select_non_tabular_tools(task_type, case_profile, max_tools=3)
    base["steps_run"].append("S6_selector_stub")
    selector_planned = selector_view.get("planned_tools") or []
    base["selector_view"] = {
        "ok": selector_view.get("ok"),
        "selector_rule_id": selector_view.get("selector_rule_id"),
        "profile_tier": selector_view.get("profile_tier"),
        "planned_tools": selector_planned,
        "preview_only": True,
        "message": selector_view.get("message"),
    }

    base["planned_tools"] = [
        str(item.get("tool_id"))
        for item in selector_planned
        if isinstance(item, dict) and item.get("tool_id")
    ] or planned_tools

    base["risk"] = _build_risk_notes(decision, glue_plan, base["selector_view"])

    if not selector_view.get("ok"):
        base["message"] = selector_view.get("message", "selector_failed")
        base["final_status"] = "blocked"
        base["notes"] = ["preview stopped at S6: selector stub failed"]
        return base

    # S7: optional sandbox metadata extraction (W12-T3; allowlist + flag gated)
    if with_metadata_extraction:
        processing_summary = extract_document_metadata(
            case_dir_rel,
            task_type=task_type,
            enabled=True,
        )
        base["processing_summary"] = processing_summary
        base["steps_run"].append("S7_metadata_extraction")
        if processing_summary.get("executed"):
            base["notes"] = [
                "non-tabular shadow preview orchestrator (W9-T4 + W12-T3 preview+meta)",
                "sandbox metadata extraction executed for allowlisted NT-A fixture",
                "does not modify Tabular main chain or production outbox",
                "outbox writes go to outbox/non_tabular_experiment/ only",
            ]
        else:
            base["notes"] = [
                "non-tabular shadow preview orchestrator (W9-T4 + W12-T3)",
                "metadata extraction requested but not executed (gate: allowlist/task_type)",
                "does not modify Tabular main chain or execute heavy tools",
                "outbox writes go to outbox/non_tabular_experiment/ only",
            ]
    else:
        base["notes"] = [
            "non-tabular shadow preview orchestrator (W9-T4)",
            "does not modify Tabular main chain or execute heavy tools",
            "outbox writes go to outbox/non_tabular_experiment/ only",
        ]

    base["ok"] = True
    base["final_status"] = "preview_ready"
    base["message"] = f"non-tabular preview complete; final_status={base['final_status']}"

    outbox_path = _write_preview_outbox(
        base,
        case_stub=case_ref,
        outbox_root=Path(outbox_root) if outbox_root else _DEFAULT_OUTBOX_ROOT,
        write_outbox=write_outbox,
    )
    if outbox_path:
        base["outbox_path"] = outbox_path
        base["steps_run"].append("S9_preview_outbox_write")

    return base


def format_preview_summary_text(result: Dict[str, Any]) -> str:
    lines = [
        "Non-Tabular Experiment Preview (W9-T4)",
        f"experiment_id: {result.get('experiment_id')}",
        f"case_ref: {result.get('case_ref')}",
        f"task_type: {result.get('task_type')}",
        f"final_status: {result.get('final_status')}",
        f"ok: {result.get('ok')}",
    ]
    decision = result.get("decision") or {}
    lines.append(
        f"decision: {decision.get('decision')} (risk={decision.get('risk_level')})"
    )
    route = result.get("planned_route") or {}
    if route:
        lines.append(f"planned_route.selector_task_type: {route.get('selector_task_type')}")
        tools = result.get("planned_tools") or []
        lines.append(f"planned_tools: {', '.join(tools)}")
    selector = result.get("selector_view") or {}
    if selector:
        lines.append(f"selector_view.rule_id: {selector.get('selector_rule_id')}")
    risk = result.get("risk") or {}
    if risk.get("signals"):
        lines.append(f"risk.signals: {risk.get('signals')}")
    if result.get("outbox_path"):
        lines.append(f"outbox_path: {result.get('outbox_path')}")
    summary = result.get("content_summary") or {}
    if summary.get("ok"):
        lines.append(
            f"content_summary: {summary.get('file_count')} files, "
            f"{summary.get('total_size_bytes')} bytes"
        )
        ext = summary.get("extension_distribution") or {}
        if ext:
            lines.append(f"content_summary.ext: {ext}")
    proc = result.get("processing_summary") or {}
    if proc.get("enabled"):
        lines.append(
            f"processing_summary.executed: {proc.get('executed')} "
            f"({proc.get('message')})"
        )
        if proc.get("files_processed"):
            lines.append(f"processing_summary.files_processed: {proc.get('files_processed')}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Non-Tabular shadow-flow preview orchestrator (W9-T4).",
    )
    parser.add_argument(
        "--task-type",
        required=True,
        help="non_tabular.document.* or non_tabular.log.* task_type",
    )
    parser.add_argument(
        "--case-dir",
        required=True,
        help="Case directory (repo-relative or absolute)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text summary)",
    )
    parser.add_argument(
        "--no-outbox",
        action="store_true",
        help="Skip writing preview JSON to outbox/non_tabular_experiment/",
    )
    parser.add_argument(
        "--outbox-root",
        default=None,
        help="Optional outbox root override (default: outbox/non_tabular_experiment/)",
    )
    parser.add_argument(
        "--with-metadata-extraction",
        action="store_true",
        help=(
            "Enable W12-T3 sandbox metadata extraction (preview+meta). "
            "Requires NT-A task_type, allowlisted case_dir, and docu-corp intake."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("preview", "preview+meta"),
        default=None,
        help="Processing mode alias: preview+meta enables --with-metadata-extraction",
    )
    args = parser.parse_args(argv)

    with_meta = args.with_metadata_extraction or args.mode == "preview+meta"

    result = run_non_tabular_experiment_preview(
        args.task_type,
        args.case_dir,
        write_outbox=not args.no_outbox,
        outbox_root=args.outbox_root,
        with_metadata_extraction=with_meta,
    )

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_preview_summary_text(result))

    if result.get("final_status") == "blocked" and not result.get("ok"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
