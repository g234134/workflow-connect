#!/usr/bin/env python3
"""Project command_center live JSON fixtures (read-only · local).

Builds P1–P5 live projections from mock shells + P8.9 operator_fields overlay.
P1/P5: W4-UI-F · P2–P4: W4-UI-G thin extension.
Does not call prod APIs, Grafana, or PG soak endpoints.

Usage:
  python scripts/project_command_center_live_v1.py --write
  python scripts/project_command_center_live_v1.py --page p1 --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MOCK_DIR = REPO_ROOT / "ui" / "command_center" / "mock"
LIVE_DIR = REPO_ROOT / "ui" / "command_center" / "live"

PAGE_MAP = {
    "p1": {
        "mock": "p1_overview_v1.json",
        "live": "p1_overview_v1.json",
        "schema_version": "w4_ui_f_p1_live_projection_v1",
    },
    "p2": {
        "mock": "p2_skills_resources_v1.json",
        "live": "p2_skills_resources_v1.json",
        "schema_version": "w4_ui_g_p2_live_projection_v1",
    },
    "p3": {
        "mock": "p3_dark_loop_v1.json",
        "live": "p3_dark_loop_v1.json",
        "schema_version": "w4_ui_g_p3_live_projection_v1",
    },
    "p4": {
        "mock": "p4_command_desk_v1.json",
        "live": "p4_command_desk_v1.json",
        "schema_version": "w4_ui_g_p4_live_projection_v1",
    },
    "p5": {
        "mock": "p5_swimlane_v1.json",
        "live": "p5_swimlane_v1.json",
        "schema_version": "w4_ui_f_p5_live_projection_v1",
    },
}

TZ = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def _project_operator_fields(case_ref: str) -> dict[str, Any]:
    sys.path.insert(0, str(REPO_ROOT))
    from delivery.p89_operator_fields_v1 import project_operator_fields

    result = project_operator_fields(case_ref=case_ref)
    if not isinstance(result, dict):
        return {
            "ok": False,
            "schema_version": "p89_operator_fields_v1",
            "read_only": True,
            "demo": False,
            "message": "operator_fields projection returned non-dict",
            "fields": [],
            "rows": [],
            "count": 0,
        }
    # Cap rows for UI shell; keep five-key contract.
    rows = list(result.get("rows") or [])[:8]
    out = {
        "ok": bool(result.get("ok")),
        "schema_version": result.get("schema_version") or "p89_operator_fields_v1",
        "read_only": True,
        "demo": False,
        "case_ref": result.get("case_ref") or case_ref,
        "message": "P8.9 five-key live projection overlay (read_only · ≠ prod Operator)",
        "count": len(rows),
        "fields": list(
            result.get("fields")
            or [
                "event_id",
                "ack_status",
                "handler_id",
                "dispatch_registry_hit",
                "dlq_flag",
            ]
        ),
        "rows": rows,
        "source": "delivery.p89_operator_fields_v1",
    }
    return out


def _queue_priority_hint() -> dict[str, Any]:
    queue_path = REPO_ROOT / "04_Workflows" / "command_queue" / "QUEUE.yaml"
    hint: dict[str, Any] = {
        "ok": queue_path.is_file(),
        "ready_count": None,
        "blocked_count": None,
        "priority_next_ids": [],
        "note": "read-only QUEUE narrative · ≠ Round-2 execute",
    }
    if not queue_path.is_file():
        return hint
    text = queue_path.read_text(encoding="utf-8")
    # Lightweight parse without requiring pyyaml for core path.
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("ready:"):
            try:
                hint["ready_count"] = int(s.split(":", 1)[1].strip())
            except ValueError:
                pass
        if s.startswith("blocked:") and "blocked_by" not in s:
            try:
                hint["blocked_count"] = int(s.split(":", 1)[1].strip())
            except ValueError:
                pass
    # priority_next ids
    in_pn = False
    for line in text.splitlines():
        if line.startswith("priority_next:"):
            in_pn = True
            continue
        if in_pn:
            if line and not line.startswith(" ") and not line.startswith("-"):
                break
            if line.strip().startswith("- id:"):
                hint["priority_next_ids"].append(line.split(":", 1)[1].strip())
            if line.startswith("human_ops_sequence:"):
                break
    return hint


def project_page(page: str, *, case_ref: str = "demo_phase") -> dict[str, Any]:
    meta = PAGE_MAP[page]
    mock_path = MOCK_DIR / meta["mock"]
    base = json.loads(mock_path.read_text(encoding="utf-8"))
    if not isinstance(base, dict):
        raise ValueError(f"mock root must be object: {mock_path}")

    op = _project_operator_fields(case_ref)
    queue_hint = _queue_priority_hint()

    out = dict(base)
    out["ok"] = True
    out["schema_version"] = meta["schema_version"]
    out["demo"] = False
    out["read_only"] = True
    out["data_source"] = "live_projection"
    out["host"] = "ui/command_center"
    out["generated_at"] = _now_iso()
    ticket_tag = "W4-UI-F" if page in {"p1", "p5"} else "W4-UI-G"
    out["message"] = (
        f"{ticket_tag} {page.upper()} live projection "
        "(CLI overlay · read_only · fallback-mock available · ≠ Grafana/PG soak/Operator prod)"
    )
    out["secrets_policy"] = "mask_only"
    out["secrets"] = {
        "api_key_display": "••••••••",
        "note": "金鑰僅遮罩占位；禁止渲染明文；驗收語意見 _smoke_test_keys.py",
    }
    out["operator_fields"] = op
    out["live_overlays"] = {
        "p89_operator_fields": {
            "ok": op.get("ok"),
            "count": op.get("count"),
            "case_ref": op.get("case_ref"),
        },
        "command_queue": queue_hint,
        "metrics_note": "toolchain /metrics stub narrative only · ≠ Prometheus soak claim",
        "gate_note": "P7.5 gate/alerts/sink contract alignment · file_stub · ≠ prod alert sink",
    }

    # Light KPI overlays from queue when available (P1/P5).
    if isinstance(out.get("kpis"), list) and queue_hint.get("ready_count") is not None:
        for kpi in out["kpis"]:
            if not isinstance(kpi, dict):
                continue
            kid = kpi.get("id")
            if page == "p1" and kid == "pending_delivery":
                blocked = queue_hint.get("blocked_count")
                if blocked is not None:
                    kpi["value"] = str(blocked)
                    kpi["delta"] = "QUEUE blocked（只讀投影）"
            if page == "p5" and kid == "running":
                ready = queue_hint.get("ready_count")
                if ready is not None:
                    kpi["value"] = str(ready)
                    kpi["delta"] = "QUEUE ready（只讀投影）"

    brand = dict(out.get("brand") or {})
    brand["clock_demo"] = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S UTC+8")
    if page == "p5":
        brand["subtitle"] = "泳道 · 交接 · 審核 · 交付（live projection）"
    elif page == "p2":
        brand["subtitle"] = "統一指揮 · 協同作戰 · 高效治理（live · 只讀）"
    elif page == "p3":
        brand["subtitle"] = "統一指揮 · 協同作戰 · 高效治理（live · 只讀）"
    elif page == "p4":
        brand["subtitle"] = "治理中樞 · 協同作戰 · 高效治理（live）"
    out["brand"] = brand

    out["non_claims"] = [
        "≠ Grafana",
        "≠ PG soak",
        "≠ DarkOps 解禁",
        "≠ 金鑰明文",
        "≠ Operator prod",
        "≠ Phase% authorize",
        "≠ Round-2 GO",
        "≠ live SLO 承諾",
    ]
    return out


def write_all(case_ref: str) -> dict[str, Any]:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    written: dict[str, Any] = {"ok": True, "pages": {}, "dir": "ui/command_center/live"}
    for page in PAGE_MAP:
        data = project_page(page, case_ref=case_ref)
        path = LIVE_DIR / PAGE_MAP[page]["live"]
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written["pages"][page] = {
            "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "ok": data.get("ok"),
            "operator_fields_count": (data.get("operator_fields") or {}).get("count"),
        }
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", choices=sorted(PAGE_MAP.keys()), default=None)
    parser.add_argument("--case-ref", default="demo_phase")
    parser.add_argument("--write", action="store_true", help="Write live/*.json")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    args = parser.parse_args(argv)

    if args.write:
        result = write_all(args.case_ref)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1

    page = args.page or "p1"
    data = project_page(page, case_ref=args.case_ref)
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(
            json.dumps(
                {
                    "ok": data.get("ok"),
                    "page": page,
                    "schema_version": data.get("schema_version"),
                    "data_source": data.get("data_source"),
                    "operator_fields_count": (data.get("operator_fields") or {}).get(
                        "count"
                    ),
                    "non_claims": data.get("non_claims"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0 if data.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
