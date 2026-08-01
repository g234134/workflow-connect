"""Wave 3 minimal smoke chain: G7 → gate parity → notify → alert sink → MP-SMOKE.

Contract: docs/wave3-smoke-g7-gate-notify-mp-chain-v1.md

Honest boundaries:
  - L-local only; ≠ prod / required CI / Web UI / Dashboard authorize
  - Does not change gate decision logic; wires existing stubs
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from delivery.p75_alert_sink_v1 import emit_alerts
from routing.intake_gate_http_stub_v1 import handle_gate_request
from routing.intake_gate_layer_v1 import evaluate_intake_gate

SCHEMA_VERSION = "wave3_smoke_chain_v1"
DOC_REL = "docs/wave3-smoke-g7-gate-notify-mp-chain-v1.md"
DEFAULT_CASE_REF = "demo_phase"
DEFAULT_TASK_TYPE = "tabular.cleaning.mvp"
DEFAULT_CASE_DIR = "cases/demo_phase"

STEP_IDS: tuple[str, ...] = (
    "g7_http_preview",
    "gate_layer_preview_parity",
    "g7_http_run_notify",
    "alert_sink_file",
    "mp_smoke",
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MP_SMOKE_SCRIPT = _REPO_ROOT / "scripts" / "run_multi_phase_smoke_v1.py"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_mp_smoke_module():
    spec = importlib.util.spec_from_file_location(
        "run_multi_phase_smoke_v1",
        _MP_SMOKE_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load MP-SMOKE script: {_MP_SMOKE_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _step(
    step_id: str,
    *,
    ok: bool,
    message: str,
    detail: Optional[Dict[str, Any]] = None,
    artifact_paths: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "step_id": step_id,
        "ok": bool(ok),
        "message": message,
        "artifact_paths": artifact_paths or {},
    }
    if detail is not None:
        row["detail"] = detail
    return row


def _case_dir_for_ref(case_ref: str) -> str:
    mapping = {
        "demo_phase": "cases/demo_phase",
        "sampleco/2026-0001": "cases/sampleco/2026-0001",
    }
    return mapping.get(case_ref, f"cases/{case_ref}")


def run_wave3_smoke_chain_v1(
    case_ref: str = DEFAULT_CASE_REF,
    *,
    task_type: str = DEFAULT_TASK_TYPE,
    case_dir: Optional[str] = None,
    repo_root: Optional[Path] = None,
    outbox_root_override: Optional[str] = None,
    include_mp_smoke: bool = True,
    enable_dispatch: bool = False,
) -> Dict[str, Any]:
    """Run Wave 3 smoke chain; returns stable summary dict with ``ok`` / ``steps``."""
    root = Path(repo_root).resolve() if repo_root else _REPO_ROOT
    case_path = case_dir or _case_dir_for_ref(case_ref)
    outbox_str = (
        str(Path(outbox_root_override).resolve())
        if outbox_root_override
        else str((root / "outbox").resolve())
    )
    Path(outbox_str).mkdir(parents=True, exist_ok=True)

    steps: List[Dict[str, Any]] = []

    # 1 — G7 HTTP stub preview (no outbox write)
    status_preview, g7_preview = handle_gate_request(
        {
            "task_type": task_type,
            "case_dir": case_path,
            "mode": "preview",
            "outbox_root": outbox_str,
        },
        repo_root=root,
        outbox_root_override=outbox_str,
    )
    gate_preview = g7_preview.get("gate") if isinstance(g7_preview.get("gate"), dict) else {}
    steps.append(
        _step(
            "g7_http_preview",
            ok=bool(g7_preview.get("ok")) and status_preview == 200 and bool(gate_preview.get("ok")),
            message=str(g7_preview.get("message") or "g7 preview"),
            detail={
                "http_status": status_preview,
                "decision": gate_preview.get("decision"),
                "intake_decision_id": gate_preview.get("intake_decision_id"),
                "case_ref": gate_preview.get("case_ref") or case_ref,
            },
        )
    )

    # 2 — Gate layer preview parity vs G7
    layer_preview = evaluate_intake_gate(
        task_type,
        case_path,
        mode="preview",
        repo_root=root,
        outbox_root_override=outbox_str,
    )
    g7_decision = gate_preview.get("decision")
    layer_decision = layer_preview.get("decision")
    parity_ok = (
        bool(layer_preview.get("ok"))
        and g7_decision is not None
        and g7_decision == layer_decision
    )
    steps.append(
        _step(
            "gate_layer_preview_parity",
            ok=parity_ok,
            message=(
                f"parity ok decision={layer_decision}"
                if parity_ok
                else f"parity mismatch g7={g7_decision} layer={layer_decision}"
            ),
            detail={
                "g7_decision": g7_decision,
                "layer_decision": layer_decision,
                "layer_ok": layer_preview.get("ok"),
            },
        )
    )

    # 3 — G7 HTTP stub run + notify
    status_run, g7_run = handle_gate_request(
        {
            "task_type": task_type,
            "case_dir": case_path,
            "mode": "run",
            "outbox_root": outbox_str,
            "enable_notifications": True,
        },
        repo_root=root,
        outbox_root_override=outbox_str,
    )
    gate_run = g7_run.get("gate") if isinstance(g7_run.get("gate"), dict) else {}
    notification = g7_run.get("notification") if isinstance(g7_run.get("notification"), dict) else {}
    run_artifacts: Dict[str, str] = {}
    if gate_run.get("outbox_record_path"):
        run_artifacts["outbox_record_path"] = str(gate_run["outbox_record_path"])
    notify_path = (notification.get("sink_result") or {}).get("path")
    if notify_path:
        run_artifacts["notification_path"] = str(notify_path)
    steps.append(
        _step(
            "g7_http_run_notify",
            ok=(
                bool(g7_run.get("ok"))
                and status_run == 200
                and bool(gate_run.get("ok"))
                and bool(notification.get("ok", True))
            ),
            message=str(g7_run.get("message") or "g7 run+notify"),
            artifact_paths=run_artifacts,
            detail={
                "http_status": status_run,
                "decision": gate_run.get("decision"),
                "notification_ok": notification.get("ok"),
                "event_type": notification.get("event_type") or "intake.gate_decision",
            },
        )
    )

    # 4 — Optional local alert sink (G6 file) from gate decision signal
    decision_for_alert = str(gate_run.get("decision") or g7_decision or "unknown")
    sink_path = str(Path(outbox_str) / "p75_alert_sink" / "wave3_smoke_events.jsonl")
    sink_result = emit_alerts(
        [
            {
                "code": f"wave3_smoke_gate_{decision_for_alert}",
                "level": "warn",
                "message": f"wave3 smoke chain gate decision={decision_for_alert}",
                "detail": f"case_ref={case_ref}",
            }
        ],
        mode="file",
        source="wave3_smoke_chain_v1",
        sink_path_override=sink_path,
        repo_root=root,
        probe_snapshot={
            "case_ref": case_ref,
            "decision": decision_for_alert,
            "chain": SCHEMA_VERSION,
        },
    )
    steps.append(
        _step(
            "alert_sink_file",
            ok=bool(sink_result.get("ok")) and int(sink_result.get("emitted") or 0) >= 1,
            message=str(sink_result.get("message") or "alert sink emit"),
            artifact_paths={"sink_path": sink_path},
            detail={
                "emitted": sink_result.get("emitted"),
                "sink_mode": sink_result.get("sink_mode"),
            },
        )
    )

    # 5 — MP-SMOKE related steps (full seven-step runner by default)
    if include_mp_smoke:
        try:
            mp_mod = _load_mp_smoke_module()
            mp_result = mp_mod.run_multi_phase_smoke_v1(
                case_ref,
                task_type=task_type,
                repo_root=root,
                outbox_root_override=outbox_str,
                enable_dispatch=enable_dispatch,
                write_summary=True,
            )
            mp_ok = bool(mp_result.get("ok"))
            failed = mp_result.get("failed_steps") or []
            summary_path = ""
            ver_dir = getattr(mp_mod, "default_verification_dir", None)
            if callable(ver_dir):
                summary_path = str(
                    ver_dir(case_ref, repo_root=root) / "multi_phase_smoke_run.json"
                )
            steps.append(
                _step(
                    "mp_smoke",
                    ok=mp_ok,
                    message=(
                        "mp-smoke ok"
                        if mp_ok
                        else f"mp-smoke failed_steps={failed}"
                    ),
                    artifact_paths=(
                        {"multi_phase_smoke_run": summary_path} if summary_path else {}
                    ),
                    detail={
                        "mp_ok": mp_ok,
                        "failed_steps": failed,
                        "step_count": len(mp_result.get("steps") or []),
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001 — surface as step failure
            steps.append(
                _step(
                    "mp_smoke",
                    ok=False,
                    message=f"mp-smoke exception: {exc}",
                    detail={"error": str(exc)},
                )
            )
    else:
        steps.append(
            _step(
                "mp_smoke",
                ok=True,
                message="mp-smoke skipped (include_mp_smoke=false)",
                detail={"skipped": True},
            )
        )

    failed_steps = [s["step_id"] for s in steps if not s.get("ok")]
    overall_ok = len(failed_steps) == 0
    return {
        "ok": overall_ok,
        "schema_version": SCHEMA_VERSION,
        "message": (
            "wave3 smoke chain passed"
            if overall_ok
            else f"wave3 smoke chain failed: {failed_steps}"
        ),
        "case_ref": case_ref,
        "task_type": task_type,
        "case_dir": case_path,
        "run_at": _utc_now_iso(),
        "outbox_root": outbox_str,
        "include_mp_smoke": include_mp_smoke,
        "steps": steps,
        "failed_steps": failed_steps,
        "contract_ref": DOC_REL,
        "non_claims": [
            "≠ prod / required CI",
            "≠ Web UI",
            "≠ Dashboard Phase% authorize",
            "≠ DarkOps / app_api",
            "≠ Phase closure",
        ],
    }
