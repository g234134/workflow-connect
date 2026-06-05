"""
W4-A gate ↔ rollout_trace.jsonl alignment helper (read-only).

Maps trace_contract in rollout_pipeline_config.json to checklist A6/B8.
Does not modify traces, run_records, or rollout exit semantics.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_trace_lines(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8-sig")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"step": "_parse_error", "exit_ok": False, "note": line[:120]})
    return rows


def _phase_cfg(config: dict[str, Any], phase_key: str) -> dict[str, Any]:
    contract = config.get("trace_contract") or {}
    phases = contract.get("phases") or {}
    return dict(phases.get(phase_key) or {})


def _find_steps(rows: list[dict[str, Any]], step_name: str) -> list[dict[str, Any]]:
    return [r for r in rows if str(r.get("step", "")) == step_name]


def _phase_summary_ok(rows: list[dict[str, Any]], *, phase_key: str, summary_step: str) -> bool:
    for row in rows:
        if str(row.get("step", "")) != summary_step:
            continue
        if row.get("kind") == "phase_summary" and row.get("phase") == phase_key:
            return bool(row.get("exit_ok"))
        if row.get("kind") is None and summary_step == phase_key:
            return bool(row.get("exit_ok"))
    return False


def _sub_steps_ok(rows: list[dict[str, Any]], sub_steps: list[str]) -> bool:
    if not sub_steps:
        return False
    for name in sub_steps:
        hits = _find_steps(rows, name)
        if not hits:
            return False
        if not all(bool(h.get("exit_ok")) for h in hits):
            return False
    return True


def _legacy_phase_ok(rows: list[dict[str, Any]], *, phase_key: str, sub_steps: list[str]) -> bool:
    """Historical traces without phase_summary: all configured sub_steps must pass."""
    return _sub_steps_ok(rows, sub_steps)


def check_trace_gate(
    *,
    config: dict[str, Any],
    trace_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    shadow_cfg = _phase_cfg(config, "shadow")
    canary_cfg = _phase_cfg(config, "canary")

    shadow_summary = str(shadow_cfg.get("trace_phase_summary_step", "shadow"))
    canary_summary = str(canary_cfg.get("trace_phase_summary_step", "canary"))
    shadow_sub = list(shadow_cfg.get("trace_sub_steps") or [])
    canary_sub = list(canary_cfg.get("trace_sub_steps") or ["internal_canary"])

    a6_summary = _phase_summary_ok(trace_rows, phase_key="shadow", summary_step=shadow_summary)
    a6_sub = _legacy_phase_ok(trace_rows, phase_key="shadow", sub_steps=shadow_sub)
    a6_ok = a6_summary or a6_sub

    b8_summary = _phase_summary_ok(trace_rows, phase_key="canary", summary_step=canary_summary)
    b8_sub = _sub_steps_ok(trace_rows, canary_sub)
    b8_ok = b8_summary or b8_sub

    return {
        "checks": {
            "A6": {
                "ok": a6_ok,
                "via_phase_summary": a6_summary,
                "via_sub_steps": a6_sub,
                "expected_sub_steps": shadow_sub,
                "verdict_step_alias": shadow_cfg.get("verdict_step", "shadow"),
            },
            "B8": {
                "ok": b8_ok,
                "via_phase_summary": b8_summary,
                "via_sub_steps": b8_sub,
                "expected_sub_steps": canary_sub,
                "verdict_step_alias": canary_cfg.get("verdict_step", "canary"),
                "art_rel_k2_phase_alias": canary_cfg.get("art_rel_k2_phase", "internal_canary"),
            },
        },
        "message": "gate trace alignment check",
    }


def check_trace_file(
    *,
    config_path: Path,
    trace_path: Path,
    require_canary: bool = True,
) -> dict[str, Any]:
    config = _load_json(config_path)
    if config is None:
        return {"ok": False, "message": f"config not found: {config_path}"}

    rows = _load_trace_lines(trace_path)
    if not rows:
        return {"ok": False, "message": f"trace empty or missing: {trace_path}"}

    result = check_trace_gate(config=config, trace_rows=rows)
    a6 = result["checks"]["A6"]["ok"]
    b8 = result["checks"]["B8"]["ok"]

    if require_canary:
        overall = a6 and b8
    else:
        overall = a6
        result["checks"]["B8"]["skipped"] = not require_canary

    result["ok"] = overall
    result["trace_path"] = str(trace_path)
    result["config_path"] = str(config_path)
    if not overall:
        parts = []
        if not a6:
            parts.append("A6 shadow phase")
        if require_canary and not b8:
            parts.append("B8 canary phase")
        result["message"] = "failed: " + ", ".join(parts)
    else:
        result["message"] = "gate trace alignment ok"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="W4-A gate ↔ trace alignment (read-only)")
    parser.add_argument("--config", required=True, help="rollout_pipeline_config.json")
    parser.add_argument("--trace", required=True, help="rollout_trace.jsonl path")
    parser.add_argument(
        "--shadow-only",
        action="store_true",
        help="Only require A6 (skip B8 canary requirement)",
    )
    args = parser.parse_args(argv)

    result = check_trace_file(
        config_path=Path(args.config),
        trace_path=Path(args.trace),
        require_canary=not args.shadow_only,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
