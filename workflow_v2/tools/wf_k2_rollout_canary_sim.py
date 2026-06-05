"""
W4-A internal canary simulation — cohort pick + ART-REL sidecar (runtime-only).

Does not change merge adapter or production routes. Writes DEC/EXEC JSON under case dir.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _cohort_bucket(task_id: str, *, salt: str, percent: int) -> bool:
    digest = hashlib.sha256(f"{salt}:{task_id}".encode()).hexdigest()
    slot = int(digest[:8], 16) % 100
    return slot < max(0, min(percent, 100))


def simulate_canary(
    *,
    config: dict[str, Any],
    run_id: str,
    case_dir: Path,
    traffic_percent: int | None = None,
) -> dict[str, Any]:
    canary_cfg = config.get("canary_step") or {}
    phase_cfg = (config.get("k2_phases") or {}).get("internal_canary") or {}
    pct = traffic_percent if traffic_percent is not None else int(phase_cfg.get("traffic_percent", 5))
    salt = str(canary_cfg.get("cohort_salt", "w4a-default"))
    task_ids = list(canary_cfg.get("sample_task_ids") or [])
    env_logical = str(config.get("env_logical", "staging-internal"))
    pilot_id = str(config.get("pilot_artifact_id", "W3-A-K2-ASK-ROLLOUT-PILOT"))
    stream_id = str(config.get("pilot_stream_id", "W4-A-PILOT-RELEASE-STREAM-v0.1"))

    assignments: list[dict[str, Any]] = []
    in_cohort = 0
    for tid in task_ids:
        selected = _cohort_bucket(tid, salt=salt, percent=pct)
        if selected:
            in_cohort += 1
        assignments.append(
            {
                "task_id": tid,
                "in_canary_cohort": selected,
                "would_primary_source": "k2" if selected else "ask",
            }
        )

    date_suffix = run_id.split("_")[0] if "_" in run_id else run_id[:8]
    release_id = f"w4a-p2-canary-{date_suffix}"
    dec_name = "07_art_rel_dec.json"
    exec_name = "08_art_rel_exec.json"

    dec = {
        "artifact_id": "ART-REL-DEC",
        "ticket_id": "W4-A-K2-ROLLOUT-INTEGRATION",
        "pilot_artifact_id": pilot_id,
        "release_id": release_id,
        "decision": "approve",
        "k2_phase": "internal_canary",
        "traffic_percent": pct,
        "shadow_window_days": None,
        "release_scope": {
            "summary": f"Internal canary {pct}% on K-2×ask — {env_logical} (W4-A pilot stream)",
            "change_class": "CHG-OBS-ONLY",
            "entrypoint": "ask_api",
            "merge_interface": "merge_ask_and_k2",
        },
        "target_audience_or_env": env_logical,
        "rollback_strategy_draft": (
            "Set cohort to 0% / ask-only; disable primary_source=k2 for cohort; "
            "re-run wf_k2_rollout_run.ps1 -Phase rollback."
        ),
        "qa_verdict_ref": {
            "artifact": "shadow_run_latest.md",
            "note": "Shadow step passed in same run_id before canary",
        },
        "neighbor_authority_ref": ["root_plan_4.8", "k2_deployment_governance"],
        "p0_blockers": [],
        "decided_at": date_suffix,
        "decided_by_role": "release",
        "message": "W4-A internal canary pilot — not remote prod rollout.",
    }

    exec_doc = {
        "artifact_id": "ART-REL-EXEC",
        "ticket_id": "W4-A-K2-ROLLOUT-INTEGRATION",
        "pilot_artifact_id": pilot_id,
        "release_id": release_id,
        "decision_ref": dec_name,
        "target_audience_or_env": env_logical,
        "published_at": _utc_now_iso(),
        "execution_evidence": {
            "env_logical": env_logical,
            "entrypoint": "ask_api",
            "merge_interface": "ASK_MERGE_INTERFACE",
            "canary_cohort_ref": "canary_env.md",
            "shadow_run_ref": "shadow_run_latest.md",
            "pilot_stream_id": stream_id,
            "run_id": run_id,
            "canary_assignments": assignments,
            "metrics_ref": [
                f"cohort_in={in_cohort}/{len(task_ids)} at {pct}%",
            ],
            "commands_run": [
                {
                    "cmd": "wf_k2_rollout_canary_sim.py",
                    "exit_ok": True,
                    "note": "Simulated cohort only — no live traffic switch",
                }
            ],
        },
        "rollback_path_valid": False,
        "not_in_scope": "No remote prod auto rollout; no Phase 3+; no merge adapter change",
        "executed_by_role": "release",
        "message": "Internal canary simulation per W4-A boundary.",
    }

    case_dir.mkdir(parents=True, exist_ok=True)
    dec_path = case_dir / dec_name
    exec_path = case_dir / exec_name
    dec_path.write_text(json.dumps(dec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    exec_path.write_text(json.dumps(exec_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    canary_env = case_dir / "canary_env.md"
    if not canary_env.exists():
        canary_env.write_text(
            "\n".join(
                [
                    "# W3-A / W4-A — internal canary environment",
                    "",
                    f"- **env_logical**: `{env_logical}`",
                    f"- **cohort_kind**: `internal_staff_hash`",
                    f"- **traffic_percent**: `{pct}`",
                    f"- **cohort_salt**: `{salt}` (config only — not a secret)",
                    "",
                    "> Generated by W4-A rollout helper when missing.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    return {
        "ok": True,
        "phase": "internal_canary",
        "run_id": run_id,
        "traffic_percent": pct,
        "sample_count": len(task_ids),
        "cohort_in_count": in_cohort,
        "assignments": assignments,
        "artifacts": {
            "art_rel_dec": str(dec_path),
            "art_rel_exec": str(exec_path),
            "canary_env": str(canary_env),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="W4-A internal canary simulation")
    parser.add_argument("--config", required=True, help="rollout_pipeline_config.json path")
    parser.add_argument("--case-dir", required=True, help="W3-A_case directory")
    parser.add_argument("--run-id", required=True, help="run record id")
    parser.add_argument("--traffic-percent", type=int, default=None)
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.is_file():
        out = {"ok": False, "message": f"config not found: {config_path}"}
        print(json.dumps(out, ensure_ascii=False))
        return 3

    config = json.loads(config_path.read_text(encoding="utf-8"))
    result = simulate_canary(
        config=config,
        run_id=args.run_id,
        case_dir=Path(args.case_dir),
        traffic_percent=args.traffic_percent,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
